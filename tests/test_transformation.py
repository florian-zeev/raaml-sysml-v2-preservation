from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from raaml_preservation.schemas import validate_instance_against_schema
from raaml_preservation.transformation import (
    _check_machine_rules,
    audit_transformation_matrix,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = (
    REPOSITORY_ROOT
    / "analysis"
    / "transformation-matrix-v0.1.json"
)
MODEL_PATH = (
    REPOSITORY_ROOT
    / "sources"
    / "cache"
    / "SysMLv1Tov2.xmi"
)


@unittest.skipUnless(
    MODEL_PATH.is_file(),
    "pinned transformation model is not in the local cache",
)
class TransformationMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))

    def test_matrix_is_schema_valid(self) -> None:
        validate_instance_against_schema(
            self.matrix,
            REPOSITORY_ROOT
            / "schemas"
            / "transformation-matrix.schema.json",
        )

    def test_every_cited_machine_rule_exists_as_a_class(self) -> None:
        diagnostics: list[dict[str, str]] = []
        _check_machine_rules(self.matrix, MODEL_PATH, diagnostics)
        self.assertEqual(diagnostics, [])

    def test_missing_machine_rule_is_rejected(self) -> None:
        changed = copy.deepcopy(self.matrix)
        changed["rows"][0]["machineRuleIds"].append("missing-rule")
        diagnostics: list[dict[str, str]] = []
        _check_machine_rules(changed, MODEL_PATH, diagnostics)
        self.assertEqual(
            [item["code"] for item in diagnostics],
            ["TRANSFORMATION_RULE_MISSING"],
        )

    def test_require_resolved_fails_while_open_rows_remain(self) -> None:
        report = audit_transformation_matrix(
            REPOSITORY_ROOT,
            require_resolved=True,
        )
        self.assertFalse(report["ok"])
        self.assertGreater(report["summary"]["open"], 0)
        self.assertIn(
            "TRANSFORMATION_RULE_OPEN",
            {item["code"] for item in report["diagnostics"]},
        )

    def test_wrong_machine_rule_kind_is_rejected(self) -> None:
        changed = copy.deepcopy(self.matrix)
        root = ET.parse(MODEL_PATH).getroot()
        XMI = "{http://www.omg.org/spec/XMI/20161101}"
        non_class_id = next(
            element.get(XMI + "id")
            for element in root.iter()
            if element.get(XMI + "id")
            and element.get(XMI + "type") not in {None, "uml:Class"}
        )
        changed["rows"][0]["machineRuleIds"] = [non_class_id]
        diagnostics: list[dict[str, str]] = []
        _check_machine_rules(changed, MODEL_PATH, diagnostics)
        self.assertEqual(
            [item["code"] for item in diagnostics],
            ["TRANSFORMATION_RULE_WRONG_KIND"],
        )
