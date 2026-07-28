from __future__ import annotations

import base64
from collections import defaultdict
from pathlib import Path
import re
import tempfile
from typing import Any

from .adapters import AdapterError, build_adapter, run_adapter
from .facts import FactExtractionError, extract_facts


OCL_LANGUAGE_NAMES = {"ocl", "ocl2.0", "ocl 2.0", "ocl2"}
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
STANDARD_NAVIGATION_PROPERTIES = {
    "client",
    "general",
    "name",
    "supplier",
    "type",
}
STANDARD_OCL_OPERATIONS = {
    "allInstances",
    "and",
    "asSet",
    "implies",
    "includes",
    "includesAll",
    "isEmpty",
    "not",
    "or",
}
STANDARD_OCL_ITERATORS = {
    "closure",
    "collect",
}


def validate_ocl_corpus(repository_root: Path) -> dict[str, Any]:
    diagnostics: list[dict[str, str]] = []
    try:
        _raw, canonical = extract_facts(repository_root)
        constraints = _ocl_constraints(canonical)
        if len(constraints) != 33:
            raise FactExtractionError(
                "OCL_CORPUS_COUNT",
                f"expected 33 OCL expressions, got {len(constraints)}",
            )
        type_candidates = _type_candidates(canonical)
        property_names = _property_names(canonical)
        visible_types, visible_properties = _visible_catalogs(
            canonical,
            constraints,
        )
        with tempfile.TemporaryDirectory() as temporary:
            catalog_path = Path(temporary) / "ocl-corpus.tsv"
            catalog_path.write_text(
                _catalog_text(
                    type_names=set(type_candidates),
                    property_names=property_names,
                    constraints=constraints,
                ),
                encoding="utf-8",
                newline="\n",
            )
            build_adapter(repository_root)
            adapter_report = run_adapter(
                repository_root,
                "ocl-corpus",
                catalog_path,
            )
    except (AdapterError, FactExtractionError, OSError) as error:
        diagnostics.append(
            {
                "severity": "error",
                "code": getattr(error, "code", "OCL_CORPUS_FAILURE"),
                "message": str(error),
            }
        )
        return _report([], diagnostics)

    results = adapter_report.get("results")
    if not isinstance(results, list):
        diagnostics.append(
            {
                "severity": "error",
                "code": "OCL_ADAPTER_RESULT",
                "message": "OCL corpus adapter returned no results array",
            }
        )
        return _report([], diagnostics)

    diagnostics.extend(
        _validate_ast_references(
            results,
            visible_type_candidates=visible_types,
            visible_property_names=visible_properties,
        )
    )

    return _report(results, diagnostics)


def _ocl_constraints(canonical: dict[str, Any]) -> list[dict[str, str]]:
    result = []
    for artifact in canonical["artifacts"]:
        for declaration in artifact["declarations"]:
            owner = declaration["name"]
            for constraint in declaration["constraints"]:
                normalized_languages = [
                    language.strip().lower()
                    for language in constraint["languages"]
                ]
                if not any(
                    language in OCL_LANGUAGE_NAMES
                    for language in normalized_languages
                ):
                    continue
                if len(constraint["languages"]) != len(constraint["bodyLines"]):
                    raise FactExtractionError(
                        "OCL_LANGUAGE_BODY_CARDINALITY",
                        f"{constraint['id']}: language/body counts differ",
                    )
                for language, body in zip(
                    constraint["languages"],
                    constraint["bodyLines"],
                    strict=True,
                ):
                    if language.strip().lower() not in OCL_LANGUAGE_NAMES:
                        continue
                    if owner is None:
                        raise FactExtractionError(
                            "OCL_CONTEXT_UNNAMED",
                            f"{constraint['id']}: owning declaration has no name",
                        )
                    result.append(
                        {
                            "key": constraint["id"],
                            "artifactId": artifact["artifactId"],
                            "owner": owner,
                            "body": body,
                        }
                    )
    return sorted(result, key=lambda item: item["key"])


def _type_candidates(canonical: dict[str, Any]) -> dict[str, list[str]]:
    candidates: defaultdict[str, list[str]] = defaultdict(list)
    for artifact in canonical["artifacts"]:
        for declaration in artifact["declarations"]:
            name = declaration["name"]
            if name is not None and IDENTIFIER.fullmatch(name):
                candidates[name].append(declaration["id"])
    return {
        name: sorted(identities)
        for name, identities in sorted(candidates.items())
    }


def _property_names(canonical: dict[str, Any]) -> set[str]:
    names = set(STANDARD_NAVIGATION_PROPERTIES)
    for artifact in canonical["artifacts"]:
        for declaration in artifact["declarations"]:
            for relation in ("properties", "ownedEnds"):
                for property_record in declaration[relation]:
                    name = property_record["name"]
                    if name is not None and IDENTIFIER.fullmatch(name):
                        names.add(name)
    return names


def _visible_catalogs(
    canonical: dict[str, Any],
    constraints: list[dict[str, str]],
) -> tuple[
    dict[str, dict[str, list[str]]],
    dict[str, set[str]],
]:
    artifacts = {
        artifact["artifactId"]: artifact
        for artifact in canonical["artifacts"]
    }
    package_owners = {
        package["id"]: artifact["artifactId"]
        for artifact in canonical["artifacts"]
        for package in artifact["packages"]
    }
    imported_artifacts: dict[str, set[str]] = {
        artifact_id: set()
        for artifact_id in artifacts
    }
    for artifact_id, artifact in artifacts.items():
        for record in artifact["machinery"]:
            if record["kind"] != "PackageImport":
                continue
            for target in record["targets"]:
                imported = package_owners.get(target["target"])
                if imported is not None:
                    imported_artifacts[artifact_id].add(imported)

    def visible_artifacts(origin: str) -> set[str]:
        visible = {origin}
        pending = [origin]
        while pending:
            current = pending.pop()
            for imported in imported_artifacts[current]:
                if imported not in visible:
                    visible.add(imported)
                    pending.append(imported)
        return visible

    types_by_artifact: dict[str, dict[str, list[str]]] = {}
    properties_by_artifact: dict[str, set[str]] = {}
    for artifact_id in artifacts:
        type_candidates: defaultdict[str, list[str]] = defaultdict(list)
        property_names = set(STANDARD_NAVIGATION_PROPERTIES)
        for visible_id in visible_artifacts(artifact_id):
            for declaration in artifacts[visible_id]["declarations"]:
                name = declaration["name"]
                if name is not None and IDENTIFIER.fullmatch(name):
                    type_candidates[name].append(declaration["id"])
                for relation in ("properties", "ownedEnds"):
                    for property_record in declaration[relation]:
                        property_name = property_record["name"]
                        if (
                            property_name is not None
                            and IDENTIFIER.fullmatch(property_name)
                        ):
                            property_names.add(property_name)
        types_by_artifact[artifact_id] = {
            name: sorted(identities)
            for name, identities in sorted(type_candidates.items())
        }
        properties_by_artifact[artifact_id] = property_names

    return (
        {
            item["key"]: types_by_artifact[item["artifactId"]]
            for item in constraints
        },
        {
            item["key"]: properties_by_artifact[item["artifactId"]]
            for item in constraints
        },
    )


def _catalog_text(
    *,
    type_names: set[str],
    property_names: set[str],
    constraints: list[dict[str, str]],
) -> str:
    lines = [
        f"TYPE\t{_encode(name)}"
        for name in sorted(type_names)
    ]
    lines.extend(
        f"PROPERTY\t{_encode(name)}"
        for name in sorted(property_names)
    )
    lines.extend(
        "\t".join(
            (
                "CONSTRAINT",
                _encode(item["key"]),
                _encode(item["owner"]),
                _encode(item["body"]),
            )
        )
        for item in constraints
    )
    return "\n".join(lines) + "\n"


def _validate_ast_references(
    results: list[dict[str, Any]],
    *,
    visible_type_candidates: dict[str, dict[str, list[str]]],
    visible_property_names: dict[str, set[str]],
) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    for item in results:
        key = item.get("key", "<unknown>")
        type_candidates = visible_type_candidates.get(key, {})
        property_names = visible_property_names.get(key, set())
        for diagnostic in item.get("diagnostics", []):
            diagnostics.append(
                {
                    "severity": diagnostic["severity"],
                    "code": diagnostic["code"],
                    "message": f"{key}: {diagnostic['message']}",
                }
            )
        for type_name in item.get("referencedTypes", []):
            candidates = type_candidates.get(type_name, [])
            if not candidates:
                diagnostics.append(
                    {
                        "severity": "error",
                        "code": "OCL_TYPE_UNRESOLVED",
                        "message": f"{key}: unresolved type {type_name}",
                    }
                )
            elif len(candidates) > 1:
                diagnostics.append(
                    {
                        "severity": "error",
                        "code": "OCL_TYPE_AMBIGUOUS",
                        "message": (
                            f"{key}: type {type_name} has candidates "
                            f"{candidates!r}"
                        ),
                    }
                )
        for property_name in item.get("referencedProperties", []):
            if property_name not in property_names:
                diagnostics.append(
                    {
                        "severity": "error",
                        "code": "OCL_PROPERTY_UNRESOLVED",
                        "message": (
                            f"{key}: unresolved property {property_name}"
                        ),
                    }
                )
        for operation_name in item.get("referencedOperations", []):
            if operation_name not in STANDARD_OCL_OPERATIONS:
                diagnostics.append(
                    {
                        "severity": "error",
                        "code": "OCL_OPERATION_UNRESOLVED",
                        "message": (
                            f"{key}: unresolved operation {operation_name}"
                        ),
                    }
                )
        for iterator_name in item.get("referencedIterators", []):
            if iterator_name not in STANDARD_OCL_ITERATORS:
                diagnostics.append(
                    {
                        "severity": "error",
                        "code": "OCL_ITERATOR_UNRESOLVED",
                        "message": (
                            f"{key}: unresolved iterator {iterator_name}"
                        ),
                    }
                )
    return diagnostics


def _encode(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def _report(
    results: list[dict[str, Any]],
    diagnostics: list[dict[str, str]],
) -> dict[str, Any]:
    failures = sum(item["severity"] == "error" for item in diagnostics)
    return {
        "schemaVersion": "0.1.0",
        "command": "validate-ocl --all",
        "ok": failures == 0 and len(results) == 33,
        "summary": {
            "checked": len(results),
            "failed": failures,
        },
        "parser": {
            "name": "Eclipse OCL Classic Ecore",
            "version": "3.22.0.v20240902-1518",
            "mode": "parse-and-ast-name-resolution",
        },
        "results": results,
        "diagnostics": diagnostics,
    }
