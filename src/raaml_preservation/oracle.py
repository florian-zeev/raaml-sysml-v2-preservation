from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any
from xml.parsers import expat

from .secure_xml import UnsafeXmlError, preflight_xml
from .sources import load_lock, verify_sources


CORPUS = "raaml-1.1-definitions"
XMI_NAMESPACE = "http://www.omg.org/spec/XMI/20131001"
RAAML_NAMESPACE_PREFIX = "https://www.omg.org/spec/RAAML/"

CATEGORY_BY_XMI_TYPE = {
    "uml:Profile": "profiles",
    "uml:Package": "packages",
    "uml:Stereotype": "stereotypes",
    "uml:Class": "classes",
    "uml:Enumeration": "enumerations",
    "uml:EnumerationLiteral": "enumerationLiterals",
    "uml:Association": "associations",
    "uml:AssociationClass": "associationClasses",
    "uml:Property": "properties",
    "uml:Port": "ports",
    "uml:Connector": "connectors",
    "uml:Constraint": "constraints",
    "uml:Extension": "extensions",
    "uml:ExtensionEnd": "extensionEnds",
    "uml:Comment": "comments",
    "uml:Image": "images",
}

BASELINE_PATH = (
    Path(__file__).resolve().parents[2]
    / "oracle"
    / "corpus-baseline-v0.1.json"
)


def load_baseline(path: Path = BASELINE_PATH) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot load oracle baseline: {error}") from error
    if (
        not isinstance(value, dict)
        or value.get("schemaVersion") != "0.1.0"
        or value.get("corpus") != CORPUS
        or not isinstance(value.get("expectedTotals"), dict)
        or not isinstance(value.get("expectedAssociationsByLibrary"), dict)
        or not isinstance(value.get("goldenFacts"), dict)
    ):
        raise ValueError("oracle baseline has an invalid structure")
    return value


_BASELINE = load_baseline()
EXPECTED_TOTALS = _BASELINE["expectedTotals"]
EXPECTED_ASSOCIATIONS = _BASELINE["expectedAssociationsByLibrary"]


def audit_corpus(
    repository_root: Path,
    *,
    lock_path: Path | None = None,
    source_dir: Path | None = None,
) -> dict[str, Any]:
    lock_path = lock_path or repository_root / "standards.lock.json"
    source_dir = source_dir or repository_root / "sources" / "cache"
    lock = load_lock(lock_path)
    artifacts = [
        artifact
        for artifact in lock["artifacts"]
        if artifact["collection"] == CORPUS
    ]
    verification = verify_sources(
        lock_path=lock_path,
        source_dir=source_dir,
        collection=CORPUS,
    )
    diagnostics: list[dict[str, str]] = []
    if not verification["ok"]:
        diagnostics.extend(
            {
                "severity": item["severity"],
                "code": item["code"],
                "message": item["message"],
            }
            for item in verification["diagnostics"]
        )
        return _report({}, {}, {}, diagnostics)

    allowed = _allowed_remote_documents(lock)
    totals: Counter[str] = Counter()
    by_artifact: dict[str, dict[str, int]] = {}
    constraint_owners: defaultdict[str, list[str]] = defaultdict(list)
    association_classes: list[str] = []

    for artifact in artifacts:
        path = source_dir / artifact["filename"]
        try:
            preflight_xml(path, allowed_remote_documents=allowed)
            result = _audit_file(path)
        except (UnsafeXmlError, OSError, expat.ExpatError) as error:
            diagnostics.append(
                {
                    "severity": "error",
                    "code": getattr(error, "code", "ORACLE_XML"),
                    "message": f"{artifact['filename']}: {error}",
                }
            )
            continue
        by_artifact[artifact["filename"]] = dict(sorted(result["counts"].items()))
        totals.update(result["counts"])
        for name, owners in result["constraintOwners"].items():
            constraint_owners[name].extend(owners)
        association_classes.extend(
            f"{artifact['filename']}::{name}"
            for name in result["associationClasses"]
        )

    for category, expected in EXPECTED_TOTALS.items():
        actual = totals[category]
        if actual != expected:
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "ORACLE_COUNT_MISMATCH",
                    "message": (
                        f"{category}: expected {expected}, observed {actual}"
                    ),
                }
            )
    for filename, expected in EXPECTED_ASSOCIATIONS.items():
        actual = by_artifact.get(filename, {}).get("associations", 0)
        if actual != expected:
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "ORACLE_ASSOCIATION_COUNT",
                    "message": (
                        f"{filename}: expected {expected} Associations, "
                        f"observed {actual}"
                    ),
                }
            )

    expected_golden = _BASELINE["goldenFacts"]
    client_owners = sorted(constraint_owners["ClientIsSituation"])
    if client_owners != expected_golden["clientIsSituationOwners"]:
        diagnostics.append(
            {
                "severity": "error",
                "code": "ORACLE_DUPLICATE_CONSTRAINT_OWNER",
                "message": (
                    "ClientIsSituation owners are "
                    f"{client_owners!r}, expected "
                    f"{expected_golden['clientIsSituationOwners']!r}"
                ),
            }
        )
    if association_classes != expected_golden["associationClasses"]:
        diagnostics.append(
            {
                "severity": "error",
                "code": "ORACLE_ASSOCIATION_CLASS",
                "message": (
                    "AssociationClass declarations are "
                    f"{association_classes!r}"
                ),
            }
        )

    golden = {
        "clientIsSituationOwners": client_owners,
        "associationClasses": association_classes,
        "associationsByLibrary": {
            filename: by_artifact.get(filename, {}).get("associations", 0)
            for filename in EXPECTED_ASSOCIATIONS
        },
        "portsByLibrary": {
            filename: by_artifact.get(filename, {}).get("ports", 0)
            for filename in ("FMEALib.xmi", "FTALib.xmi", "RBDLib.xmi")
        },
        "connectorsByLibrary": {
            filename: by_artifact.get(filename, {}).get("connectors", 0)
            for filename in ("FMEALib.xmi", "FTALib.xmi", "RBDLib.xmi")
        },
    }
    for field in ("portsByLibrary", "connectorsByLibrary"):
        if golden[field] != expected_golden[field]:
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "ORACLE_GOLDEN_MISMATCH",
                    "message": (
                        f"{field}: expected {expected_golden[field]!r}, "
                        f"observed {golden[field]!r}"
                    ),
                }
            )
    return _report(dict(totals), by_artifact, golden, diagnostics)


def _audit_file(path: Path) -> dict[str, Any]:
    parser = expat.ParserCreate(namespace_separator="}")
    counts: Counter[str] = Counter()
    stack: list[dict[str, str | None]] = []
    constraint_owners: defaultdict[str, list[str]] = defaultdict(list)
    association_classes: list[str] = []

    def start(name: str, attributes: dict[str, str]) -> None:
        namespace, local_name = _split_expanded_name(name)
        xmi_type = attributes.get(f"{XMI_NAMESPACE}}}type")
        element_name = attributes.get("name")
        category = CATEGORY_BY_XMI_TYPE.get(xmi_type)
        if category is not None:
            counts[category] += 1

        if xmi_type == "uml:Constraint" and element_name:
            owner_name = next(
                (
                    item["name"]
                    for item in reversed(stack)
                    if item["type"] in {
                        "uml:Stereotype",
                        "uml:Class",
                        "uml:Association",
                        "uml:AssociationClass",
                    }
                    and item["name"] is not None
                ),
                None,
            )
            if owner_name is not None:
                constraint_owners[element_name].append(owner_name)
        if xmi_type == "uml:AssociationClass" and element_name:
            association_classes.append(element_name)

        if (
            len(stack) == 1
            and namespace.startswith(RAAML_NAMESPACE_PREFIX)
        ):
            counts["raamlApplications"] += 1
        stack.append(
            {
                "local": local_name,
                "type": xmi_type,
                "name": element_name,
            }
        )

    def end(_name: str) -> None:
        stack.pop()

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            parser.Parse(block, False)
        parser.Parse(b"", True)
    return {
        "counts": counts,
        "constraintOwners": constraint_owners,
        "associationClasses": association_classes,
    }


def _report(
    totals: dict[str, int],
    by_artifact: dict[str, dict[str, int]],
    golden: dict[str, Any],
    diagnostics: list[dict[str, str]],
) -> dict[str, Any]:
    failed = sum(item["severity"] == "error" for item in diagnostics)
    return {
        "schemaVersion": "0.1.0",
        "command": "oracle audit",
        "ok": failed == 0,
        "summary": {
            "checked": 17 if by_artifact else 0,
            "failed": failed,
        },
        "counts": dict(sorted(totals.items())),
        "byArtifact": dict(sorted(by_artifact.items())),
        "goldenFacts": golden,
        "diagnostics": diagnostics,
    }


def _allowed_remote_documents(lock: dict[str, Any]) -> frozenset[str]:
    authoritative = {
        artifact["authoritativeUrl"] for artifact in lock["artifacts"]
    }
    historical = {
        url.replace("https://www.omg.org/", "http://www.omg.org/", 1)
        for url in authoritative
        if url.startswith("https://www.omg.org/")
    }
    return frozenset(authoritative | historical)


def _split_expanded_name(name: str) -> tuple[str, str]:
    if "}" not in name:
        return "", name
    return tuple(name.rsplit("}", 1))  # type: ignore[return-value]
