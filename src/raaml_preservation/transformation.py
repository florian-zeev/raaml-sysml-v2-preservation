from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag
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


def analyze_property_transformation_surface(
    repository_root: Path,
) -> dict[str, Any]:
    """Classify every corpus UML Property by the official rule filters."""
    lock_path = repository_root / "standards.lock.json"
    source_dir = repository_root / "sources" / "cache"
    for collection in (RAAML_CORPUS, "v1-reference-models"):
        verification = verify_sources(
            lock_path=lock_path,
            source_dir=source_dir,
            collection=collection,
        )
        if not verification["ok"]:
            first = verification["diagnostics"][0]
            raise LockError(first["message"])

    lock = load_lock(lock_path)
    artifacts = [
        artifact
        for artifact in lock["artifacts"]
        if artifact["collection"] == RAAML_CORPUS
    ]
    if len(artifacts) != 17:
        raise ValueError(
            f"expected 17 locked RAAML artifacts, got {len(artifacts)}"
        )
    allowed_remote_documents = _allowed_remote_documents(lock)
    paths_by_url: dict[str, Path] = {}
    for artifact in lock["artifacts"]:
        path = source_dir / artifact["filename"]
        if path.suffix.lower() != ".xmi" or not path.is_file():
            continue
        url = artifact["authoritativeUrl"]
        paths_by_url[url] = path
        if url.startswith("https://www.omg.org/"):
            paths_by_url[
                url.replace("https://www.omg.org/", "http://www.omg.org/", 1)
            ] = path

    parsed: dict[Path, tuple[ET.Element, dict[str, ET.Element], dict[ET.Element, ET.Element]]] = {}

    def parse(path: Path) -> tuple[
        ET.Element,
        dict[str, ET.Element],
        dict[ET.Element, ET.Element],
    ]:
        if path not in parsed:
            preflight_xml(
                path,
                allowed_remote_documents=allowed_remote_documents,
            )
            root = ET.parse(path).getroot()
            parsed[path] = (
                root,
                {
                    element.get(XMI_2013_ID): element
                    for element in root.iter()
                    if element.get(XMI_2013_ID)
                },
                {
                    child: owner
                    for owner in root.iter()
                    for child in owner
                },
            )
        return parsed[path]

    def resolve(
        element: ET.Element,
        role: str,
        current_path: Path,
    ) -> tuple[Path, str, ET.Element | str] | None:
        local_value = element.get(role)
        if local_value:
            target_id = local_value.split()[0]
            target = parse(current_path)[1].get(target_id)
            if target is None:
                raise ValueError(
                    f"{current_path.name}:{role} has unresolved local "
                    f"target {target_id!r}"
                )
            return current_path, target_id, target
        for child in element:
            if _local_name(child.tag) != role:
                continue
            target_id = child.get(
                f"{{{XMI_2013_NAMESPACE}}}idref"
            )
            target_path = current_path
            if target_id is None:
                href = child.get("href")
                if href is None:
                    raise ValueError(
                        f"{current_path.name}:{role} has no reference"
                    )
                document, target_id = urldefrag(href)
                if document:
                    target_path = paths_by_url.get(document)
                    if target_path is None:
                        raise ValueError(
                            f"{current_path.name}:{role} references "
                            f"unlocked document {document!r}"
                        )
                    if role == "type" and target_path.name in {
                        "ISO80000.xmi",
                        "PrimitiveTypes.xmi",
                        "SysML.xmi",
                        "UML-20131001.xmi",
                        "UML.xmi",
                    }:
                        return (
                            target_path,
                            target_id,
                            _external_property_type_kind(target_path.name),
                        )
            target = parse(target_path)[1].get(target_id)
            if target is None:
                raise ValueError(
                    f"{current_path.name}:{role} has unresolved target "
                    f"{target_id!r}"
                )
            return target_path, target_id, target
        return None

    block_targets: set[tuple[Path, str]] = set()
    constraint_block_targets: set[tuple[Path, str]] = set()
    corpus_paths = sorted(
        (source_dir / artifact["filename"] for artifact in artifacts),
        key=lambda path: path.name,
    )
    for path in corpus_paths:
        root = parse(path)[0]
        for element in root:
            namespace, name = _expanded_name(element.tag)
            if not namespace.startswith(SYSML_V1_NAMESPACE_PREFIX):
                continue
            if name not in {"Block", "ConstraintBlock"}:
                continue
            role = "base_Class"
            target_id = element.get(role)
            if target_id is None:
                raise ValueError(f"{path.name}:{name} has no {role}")
            targets = (
                block_targets
                if name == "Block"
                else constraint_block_targets
            )
            targets.add((path, target_id))

    counts: Counter[str] = Counter()
    for path in corpus_paths:
        root, _, parents = parse(path)
        for element in root.iter():
            if element.get(XMI_2013_TYPE) != "uml:Property":
                continue
            name = element.get("name") or ""
            owner = parents[element]
            owner_id = owner.get(XMI_2013_ID)
            owner_key = (path, owner_id) if owner_id else None
            association = resolve(element, "association", path)
            property_type = resolve(element, "type", path)
            tag = _local_name(element.tag)

            if name.startswith("base_"):
                category = "stereotype-base-property"
            elif association is not None and tag == "ownedEnd":
                category = "association-owned-end"
            elif association is not None:
                if property_type is None:
                    raise ValueError(
                        f"{path.name}:{name} is an untyped non-owned end"
                    )
                type_kind = _resolved_type_kind(property_type)
                if type_kind not in {
                    "uml:AssociationClass",
                    "uml:Class",
                    "uml:Interface",
                }:
                    raise ValueError(
                        f"{path.name}:{name} non-owned end has type "
                        f"{type_kind!r}, not Class or Interface"
                    )
                category = "association-non-owned-end"
            elif owner_key in constraint_block_targets:
                if property_type is None:
                    raise ValueError(
                        f"{path.name}:{name} is an untyped "
                        "ConstraintBlock parameter"
                    )
                category = "constraint-parameter"
            elif property_type is None:
                category = "untyped-property"
            else:
                type_path, type_id, _ = property_type
                type_kind = _resolved_type_kind(property_type)
                if (type_path, type_id) in block_targets:
                    category = "part-property"
                elif type_kind in {
                    "uml:DataType",
                    "uml:Enumeration",
                    "uml:PrimitiveType",
                }:
                    category = "attribute-property"
                elif type_kind in {
                    "uml:AssociationClass",
                    "uml:Class",
                    "uml:Interface",
                }:
                    category = "occurrence-property"
                else:
                    raise ValueError(
                        f"{path.name}:{name} has unsupported type "
                        f"{type_kind!r}"
                    )
            counts[category] += 1

    categories = [
        (
            "stereotype-base-property",
            "Handled by Stereotype metadata and extension mappings",
            ["Mappings-UML4SysML-Packages-StereotypeMetadataDefinition_Mapping"],
        ),
        (
            "association-owned-end",
            "Feature",
            ["Mappings-UML4SysML-StructuredClassifiers-OwnedEnd_Mapping"],
        ),
        (
            "association-non-owned-end",
            "OccurrenceUsage plus association-end Feature",
            [
                "Mappings-UML4SysML-Classification-PropertyTypedByClassInterface_Mapping",
                "Mappings-UML4SysML-StructuredClassifiers-NonOwnedEnd_Mapping",
            ],
        ),
        (
            "constraint-parameter",
            "AttributeUsage",
            ["Mappings-SysMLv1-ConstraintBlocks-ConstraintParameter_Mapping"],
        ),
        (
            "attribute-property",
            "AttributeUsage",
            ["Mappings-UML4SysML-SimpleClassifiers-Attribute_Mapping"],
        ),
        (
            "occurrence-property",
            "OccurrenceUsage",
            [
                "Mappings-UML4SysML-Classification-PropertyTypedByClassInterface_Mapping"
            ],
        ),
        (
            "untyped-property",
            "Feature",
            ["Mappings-UML4SysML-Classification-PropertyUntyped_Mapping"],
        ),
        (
            "part-property",
            "PartUsage",
            ["Mappings-SysMLv1-Blocks-PartProperty_Mapping"],
        ),
    ]
    property_count = sum(counts.values())
    if property_count != 267:
        raise ValueError(
            f"expected 267 UML Properties, classified {property_count}"
        )
    return {
        "schemaVersion": "0.1.0",
        "documentKind": "property-transformation-surface",
        "corpus": RAAML_CORPUS,
        "propertyCount": property_count,
        "categories": [
            {
                "id": category_id,
                "count": counts[category_id],
                "officialTarget": target,
                "machineRuleIds": rule_ids,
            }
            for category_id, target, rule_ids in categories
        ],
    }


def _allowed_remote_documents(lock: dict[str, Any]) -> set[str]:
    authoritative_urls = {
        artifact["authoritativeUrl"] for artifact in lock["artifacts"]
    }
    return authoritative_urls | {
        url.replace("https://www.omg.org/", "http://www.omg.org/", 1)
        for url in authoritative_urls
        if url.startswith("https://www.omg.org/")
    }


def _external_property_type_kind(filename: str) -> str:
    if filename in {"UML-20131001.xmi", "UML.xmi"}:
        # UML metaclasses are themselves represented as UML Classes.
        return "uml:Class"
    if filename == "ISO80000.xmi":
        return "uml:DataType"
    if filename in {"PrimitiveTypes.xmi", "SysML.xmi"}:
        return "uml:PrimitiveType"
    raise ValueError(f"unsupported external property type document {filename}")


def _resolved_type_kind(
    reference: tuple[Path, str, ET.Element | str],
) -> str | None:
    target = reference[2]
    if isinstance(target, str):
        return target
    return target.get(XMI_2013_TYPE)


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
            _check_property_surface(
                matrix,
                analyze_property_transformation_surface(repository_root),
                diagnostics,
            )
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        ValueError,
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


def _check_property_surface(
    matrix: dict[str, Any],
    surface: dict[str, Any],
    diagnostics: list[dict[str, str]],
) -> None:
    rows = {row["id"]: row for row in matrix["rows"]}
    for category in surface["categories"]:
        row = rows.get(category["id"])
        if row is None:
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "TRANSFORMATION_PROPERTY_ROW_MISSING",
                    "message": (
                        "matrix is missing Property category "
                        f"{category['id']}"
                    ),
                }
            )
            continue
        if row["corpusCount"] != category["count"]:
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "TRANSFORMATION_PROPERTY_COUNT_MISMATCH",
                    "message": (
                        f"{category['id']}: matrix count "
                        f"{row['corpusCount']} does not match source count "
                        f"{category['count']}"
                    ),
                }
            )
        if row["officialTarget"] != category["officialTarget"]:
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "TRANSFORMATION_PROPERTY_TARGET_MISMATCH",
                    "message": (
                        f"{category['id']}: matrix target "
                        f"{row['officialTarget']!r} does not match "
                        f"{category['officialTarget']!r}"
                    ),
                }
            )
        if row["machineRuleIds"] != category["machineRuleIds"]:
            diagnostics.append(
                {
                    "severity": "error",
                    "code": "TRANSFORMATION_PROPERTY_RULE_MISMATCH",
                    "message": (
                        f"{category['id']}: matrix rule IDs do not match "
                        "the classified source surface"
                    ),
                }
            )
