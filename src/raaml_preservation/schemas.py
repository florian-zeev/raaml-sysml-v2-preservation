from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .sources import LockError, load_lock


class SchemaValidationError(ValueError):
    pass


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
