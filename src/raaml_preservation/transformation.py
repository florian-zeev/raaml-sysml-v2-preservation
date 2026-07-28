from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from .schemas import (
    SchemaValidationError,
    validate_instance_against_schema,
)
from .sources import LockError, verify_sources


XMI_ID = "{http://www.omg.org/spec/XMI/20161101}id"
XMI_TYPE = "{http://www.omg.org/spec/XMI/20161101}type"


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
