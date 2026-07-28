from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from .schemas import (
    SchemaValidationError,
    validate_instance_against_schema,
)
from .secure_xml import preflight_xml
from .sources import LockError, load_lock, verify_sources


RAAML_CORPUS = "raaml-1.1-definitions"
SYSML_V1_NAMESPACE_PREFIX = "http://www.omg.org/spec/SysML/"
XMI_2013_NAMESPACE = "http://www.omg.org/spec/XMI/20131001"
XMI_2013_ID = f"{{{XMI_2013_NAMESPACE}}}id"
XMI_2013_TYPE = f"{{{XMI_2013_NAMESPACE}}}type"
XMI_ID = "{http://www.omg.org/spec/XMI/20161101}id"
XMI_TYPE = "{http://www.omg.org/spec/XMI/20161101}type"


def analyze_corpus_transformation_surface(
    repository_root: Path,
) -> dict[str, Any]:
    """Inventory SysML v1 applications that select specialized mappings."""
    lock_path = repository_root / "standards.lock.json"
    source_dir = repository_root / "sources" / "cache"
    verification = verify_sources(
        lock_path=lock_path,
        source_dir=source_dir,
        collection=RAAML_CORPUS,
    )
    if not verification["ok"]:
        first = verification["diagnostics"][0]
        raise LockError(first["message"])

    lock = load_lock(lock_path)
    artifacts = sorted(
        (
            artifact
            for artifact in lock["artifacts"]
            if artifact["collection"] == RAAML_CORPUS
        ),
        key=lambda artifact: artifact["filename"],
    )
    if len(artifacts) != 17:
        raise ValueError(
            f"expected 17 locked RAAML artifacts, got {len(artifacts)}"
        )
    authoritative_urls = {
        artifact["authoritativeUrl"] for artifact in lock["artifacts"]
    }
    allowed_remote_documents = authoritative_urls | {
        url.replace("https://www.omg.org/", "http://www.omg.org/", 1)
        for url in authoritative_urls
        if url.startswith("https://www.omg.org/")
    }

    namespace_counts: Counter[str] = Counter()
    stereotype_counts: Counter[str] = Counter()
    target_roles: dict[str, set[str]] = defaultdict(set)
    target_kinds: dict[str, Counter[str]] = defaultdict(Counter)

    for artifact in artifacts:
        path = source_dir / artifact["filename"]
        preflight_xml(
            path,
            allowed_remote_documents=allowed_remote_documents,
        )
        root = ET.parse(path).getroot()
        elements_by_id = {
            element.get(XMI_2013_ID): element
            for element in root.iter()
            if element.get(XMI_2013_ID)
        }
        for element in root:
            namespace, name = _expanded_name(element.tag)
            if not namespace.startswith(SYSML_V1_NAMESPACE_PREFIX):
                continue
            targets = [
                (_local_name(attribute), value)
                for attribute, value in element.attrib.items()
                if _local_name(attribute).startswith("base_")
            ]
            if len(targets) != 1:
                raise ValueError(
                    f"{artifact['filename']}:{name} must have exactly "
                    "one base_* target"
                )
            role, target_id = targets[0]
            target = elements_by_id.get(target_id)
            if target is None:
                raise ValueError(
                    f"{artifact['filename']}:{name} has unresolved "
                    f"target {target_id!r}"
                )
            namespace_counts[namespace] += 1
            stereotype_counts[name] += 1
            target_roles[name].add(role)
            target_kinds[name][target.get(XMI_2013_TYPE, "<missing>")] += 1

    stereotypes = []
    for name in sorted(stereotype_counts):
        stereotypes.append(
            {
                "name": name,
                "count": stereotype_counts[name],
                "targetRoles": sorted(target_roles[name]),
                "targetKinds": [
                    {"kind": kind, "count": count}
                    for kind, count in sorted(target_kinds[name].items())
                ],
            }
        )
    return {
        "schemaVersion": "0.1.0",
        "documentKind": "corpus-transformation-surface",
        "corpus": RAAML_CORPUS,
        "artifactCount": len(artifacts),
        "rootSysmlApplicationCount": sum(stereotype_counts.values()),
        "namespaces": [
            {"namespace": namespace, "count": count}
            for namespace, count in sorted(namespace_counts.items())
        ],
        "stereotypes": stereotypes,
    }


def _expanded_name(name: str) -> tuple[str, str]:
    if name.startswith("{"):
        namespace, local_name = name[1:].split("}", 1)
        return namespace, local_name
    return "", name


def _local_name(name: str) -> str:
    return name.rsplit("}", 1)[-1]


def audit_transformation_matrix(
    repository_root: Path,
    *,
    matrix_path: Path | None = None,
    require_resolved: bool = False,
) -> dict[str, Any]:
    matrix_path = matrix_path or (
        repository_root
        / "analysis"
        / "transformation-matrix-v0.1.json"
    )
    diagnostics: list[dict[str, str]] = []
    matrix: dict[str, Any] = {}
    try:
        matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
        validate_instance_against_schema(
            matrix,
            repository_root
            / "schemas"
            / "transformation-matrix.schema.json",
        )
        source_report = verify_sources(
            lock_path=repository_root / "standards.lock.json",
            source_dir=repository_root / "sources" / "cache",
            collection="standards-baseline",
        )
        if not source_report["ok"]:
            diagnostics.extend(source_report["diagnostics"])
        else:
            _check_machine_rules(
                matrix,
                repository_root
                / "sources"
                / "cache"
                / "SysMLv1Tov2.xmi",
                diagnostics,
            )
            _check_corpus_surface_counts(
                matrix,
                analyze_corpus_transformation_surface(repository_root),
                diagnostics,
            )
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        SchemaValidationError,
        LockError,
        ET.ParseError,
    ) as error:
        diagnostics.append(
            {
                "severity": "error",
                "code": "TRANSFORMATION_MATRIX_INVALID",
                "message": str(error),
            }
        )

    rows = matrix.get("rows", [])
    open_rows = [
        row["id"]
        for row in rows
        if row.get("classification") == "open"
    ]
    if require_resolved and open_rows:
        diagnostics.append(
            {
                "severity": "error",
                "code": "TRANSFORMATION_RULE_OPEN",
                "message": (
                    "unresolved transformation rows: "
                    + ", ".join(open_rows)
                ),
            }
        )
    elif open_rows:
        diagnostics.append(
            {
                "severity": "warning",
                "code": "TRANSFORMATION_RULE_OPEN",
                "message": (
                    "unresolved transformation rows: "
                    + ", ".join(open_rows)
                ),
            }
        )

    failures = sum(
        item["severity"] == "error"
        for item in diagnostics
    )
    return {
        "schemaVersion": "0.1.0",
        "command": "transformation audit",
        "ok": failures == 0,
        "summary": {
            "checked": len(rows),
            "failed": failures,
            "open": len(open_rows),
        },
        "matrixVersion": matrix.get("matrixVersion"),
        "openRows": open_rows,
        "diagnostics": diagnostics,
    }


def _check_machine_rules(
    matrix: dict[str, Any],
    model_path: Path,
    diagnostics: list[dict[str, str]],
) -> None:
    root = ET.parse(model_path).getroot()
    elements = {
        element.get(XMI_ID): element
        for element in root.iter()
        if element.get(XMI_ID)
    }
    for row in matrix["rows"]:
        for rule_id in row["machineRuleIds"]:
            element = elements.get(rule_id)
            if element is None:
                diagnostics.append(
                    {
                        "severity": "error",
                        "code": "TRANSFORMATION_RULE_MISSING",
                        "message": f"{row['id']}: missing XMI rule {rule_id}",
                    }
                )
            elif element.get(XMI_TYPE) != "uml:Class":
                diagnostics.append(
                    {
                        "severity": "error",
                        "code": "TRANSFORMATION_RULE_WRONG_KIND",
                        "message": (
                            f"{row['id']}: {rule_id} has type "
                            f"{element.get(XMI_TYPE)!r}, expected 'uml:Class'"
                        ),
                    }
                )


def _check_corpus_surface_counts(
    matrix: dict[str, Any],
    surface: dict[str, Any],
    diagnostics: list[dict[str, str]],
) -> None:
    rows = {row["id"]: row for row in matrix["rows"]}
    stereotypes = {
        row["name"]: row for row in surface["stereotypes"]
    }
    block_kinds = {
        row["kind"]: row["count"]
        for row in stereotypes["Block"]["targetKinds"]
    }
    expected = {
        "association-block": block_kinds.get("uml:AssociationClass", 0),
        "binding-connector": stereotypes["BindingConnector"]["count"],
        "block": block_kinds.get("uml:Class", 0),
        "constraint-block": stereotypes["ConstraintBlock"]["count"],
        "nested-connector-end": stereotypes["NestedConnectorEnd"]["count"],
        "value-type-enumeration": stereotypes["ValueType"]["count"],
    }
    for row_id, expected_count in expected.items():
        row = rows.get(row_id)
        if row is None:
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "TRANSFORMATION_SURFACE_ROW_MISSING",
                    "message": (
                        f"matrix is missing specialized corpus row {row_id}"
                    ),
                }
            )
        elif row["corpusCount"] != expected_count:
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "TRANSFORMATION_SURFACE_COUNT_MISMATCH",
                    "message": (
                        f"{row_id}: matrix count {row['corpusCount']} "
                        f"does not match source count {expected_count}"
                    ),
                }
            )
