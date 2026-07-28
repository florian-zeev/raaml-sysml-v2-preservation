from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from .sources import LockError, load_lock


class SchemaValidationError(ValueError):
    pass


def validate_instance_against_schema(
    value: Any,
    schema_path: Path,
) -> None:
    schema = _read_json(schema_path)
    _validate_schema_node(value, schema, schema, "$")


def validate_schemas(repository_root: Path) -> dict[str, Any]:
    diagnostics: list[dict[str, str]] = []
    checked = 0
    schemas = sorted((repository_root / "schemas").glob("*.schema.json"))
    for path in schemas:
        checked += 1
        try:
            value = _read_json(path)
            if value.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                raise SchemaValidationError("must declare JSON Schema draft 2020-12")
            if not isinstance(value.get("$id"), str) or not value["$id"]:
                raise SchemaValidationError("must declare a non-empty $id")
            if value.get("type") != "object":
                raise SchemaValidationError("root type must be object")
        except SchemaValidationError as error:
            diagnostics.append(_error("SCHEMA_INVALID", f"{path.name}: {error}"))

    checked += 1
    try:
        load_lock(repository_root / "standards.lock.json")
    except LockError as error:
        diagnostics.append(_error("STANDARDS_LOCK_INVALID", str(error)))

    diagnostics_dir = repository_root / "reports" / "diagnostics"
    if diagnostics_dir.is_dir():
        for path in sorted(diagnostics_dir.glob("*.json")):
            checked += 1
            try:
                _validate_diagnostics(_read_json(path))
            except SchemaValidationError as error:
                diagnostics.append(
                    _error("DIAGNOSTICS_INVALID", f"{path.name}: {error}")
                )

    failed = len(diagnostics)
    return {
        "schemaVersion": "0.1.0",
        "command": "schemas validate",
        "ok": failed == 0,
        "summary": {"checked": checked, "failed": failed},
        "diagnostics": diagnostics,
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SchemaValidationError(str(error)) from error
    if not isinstance(value, dict):
        raise SchemaValidationError("root must be an object")
    return value


def _validate_schema_node(
    value: Any,
    node: dict[str, Any],
    root: dict[str, Any],
    path: str,
) -> None:
    if "$ref" in node:
        reference = node["$ref"]
        if not isinstance(reference, str) or not reference.startswith("#/"):
            raise SchemaValidationError(f"{path}: unsupported $ref {reference!r}")
        target: Any = root
        for segment in reference[2:].split("/"):
            segment = segment.replace("~1", "/").replace("~0", "~")
            if not isinstance(target, dict) or segment not in target:
                raise SchemaValidationError(
                    f"{path}: unresolved schema reference {reference}"
                )
            target = target[segment]
        if not isinstance(target, dict):
            raise SchemaValidationError(
                f"{path}: schema reference does not target an object"
            )
        _validate_schema_node(value, target, root, path)
        return

    if "oneOf" in node:
        matches = 0
        errors = []
        for option in node["oneOf"]:
            try:
                _validate_schema_node(value, option, root, path)
                matches += 1
            except SchemaValidationError as error:
                errors.append(str(error))
        if matches != 1:
            raise SchemaValidationError(
                f"{path}: expected exactly one oneOf match, got {matches}; "
                + "; ".join(errors[:2])
            )
        return

    if "const" in node and value != node["const"]:
        raise SchemaValidationError(
            f"{path}: expected constant {node['const']!r}, got {value!r}"
        )
    if "enum" in node and value not in node["enum"]:
        raise SchemaValidationError(
            f"{path}: value {value!r} is not in {node['enum']!r}"
        )

    declared_type = node.get("type")
    if declared_type is not None:
        choices = declared_type if isinstance(declared_type, list) else [declared_type]
        if not any(_matches_json_type(value, choice) for choice in choices):
            raise SchemaValidationError(
                f"{path}: expected type {declared_type!r}, "
                f"got {type(value).__name__}"
            )

    if isinstance(value, dict):
        required = node.get("required", [])
        for field in required:
            if field not in value:
                raise SchemaValidationError(f"{path}: missing required field {field}")
        properties = node.get("properties", {})
        if node.get("additionalProperties") is False:
            unexpected = sorted(set(value) - set(properties))
            if unexpected:
                raise SchemaValidationError(
                    f"{path}: unexpected fields: {', '.join(unexpected)}"
                )
        for key, child in value.items():
            child_schema = properties.get(key)
            if child_schema is not None:
                _validate_schema_node(
                    child,
                    child_schema,
                    root,
                    f"{path}.{key}",
                )

    if isinstance(value, list):
        minimum = node.get("minItems")
        if isinstance(minimum, int) and len(value) < minimum:
            raise SchemaValidationError(
                f"{path}: expected at least {minimum} item(s), got {len(value)}"
            )
        items = node.get("items")
        if isinstance(items, dict):
            for index, child in enumerate(value):
                _validate_schema_node(
                    child,
                    items,
                    root,
                    f"{path}[{index}]",
                )

    if isinstance(value, str):
        minimum = node.get("minLength")
        if isinstance(minimum, int) and len(value) < minimum:
            raise SchemaValidationError(
                f"{path}: string is shorter than {minimum}"
            )
        pattern = node.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, value) is None:
            raise SchemaValidationError(
                f"{path}: value does not match pattern {pattern!r}"
            )

    if isinstance(value, int) and not isinstance(value, bool):
        minimum = node.get("minimum")
        if isinstance(minimum, int) and value < minimum:
            raise SchemaValidationError(
                f"{path}: value {value} is less than {minimum}"
            )


def _matches_json_type(value: Any, declared: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
        ),
        "null": value is None,
    }.get(declared, False)


def _validate_diagnostics(value: dict[str, Any]) -> None:
    if value.get("schemaVersion") != "0.1.0":
        raise SchemaValidationError("schemaVersion must be 0.1.0")
    if not isinstance(value.get("command"), str) or not value["command"]:
        raise SchemaValidationError("command must be a non-empty string")
    if not isinstance(value.get("ok"), bool):
        raise SchemaValidationError("ok must be boolean")
    summary = value.get("summary")
    if not isinstance(summary, dict):
        raise SchemaValidationError("summary must be an object")
    for field in ("checked", "failed"):
        field_value = summary.get(field)
        if (
            not isinstance(field_value, int)
            or isinstance(field_value, bool)
            or field_value < 0
        ):
            raise SchemaValidationError(f"summary.{field} must be non-negative integer")
    items = value.get("diagnostics")
    if not isinstance(items, list):
        raise SchemaValidationError("diagnostics must be an array")
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise SchemaValidationError(f"diagnostics[{index}] must be an object")
        if item.get("severity") not in {"error", "warning", "info"}:
            raise SchemaValidationError(f"diagnostics[{index}].severity is invalid")
        if not isinstance(item.get("code"), str) or not item["code"]:
            raise SchemaValidationError(f"diagnostics[{index}].code is invalid")
        if not isinstance(item.get("message"), str):
            raise SchemaValidationError(f"diagnostics[{index}].message is invalid")


def _error(code: str, message: str) -> dict[str, str]:
    return {"severity": "error", "code": code, "message": message}
