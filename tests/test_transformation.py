from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from raaml_preservation.schemas import validate_instance_against_schema
from raaml_preservation.transformation import (
    _check_corpus_surface_counts,
    _check_machine_rules,
    _check_property_surface,
    analyze_corpus_transformation_surface,
    analyze_property_transformation_surface,
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
SURFACE_PATH = (
    REPOSITORY_ROOT
    / "analysis"
    / "corpus-transformation-surface-v0.1.json"
)
PROPERTY_SURFACE_PATH = (
    REPOSITORY_ROOT
    / "analysis"
    / "property-transformation-surface-v0.1.json"
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

    def test_corpus_transformation_surface_is_reproducible(self) -> None:
        expected = json.loads(SURFACE_PATH.read_text(encoding="utf-8"))
        actual = analyze_corpus_transformation_surface(REPOSITORY_ROOT)
        self.assertEqual(actual, expected)

    def test_corpus_transformation_surface_is_schema_valid(self) -> None:
        surface = json.loads(SURFACE_PATH.read_text(encoding="utf-8"))
        validate_instance_against_schema(
            surface,
            REPOSITORY_ROOT
            / "schemas"
            / "corpus-transformation-surface.schema.json",
        )

    def test_specialized_sysml_application_counts_cover_the_corpus(self) -> None:
        surface = json.loads(SURFACE_PATH.read_text(encoding="utf-8"))
        counts = {
            row["name"]: row["count"]
            for row in surface["stereotypes"]
        }
        self.assertEqual(
            counts,
            {
                "BindingConnector": 90,
                "Block": 8,
                "ConstraintBlock": 36,
                "NestedConnectorEnd": 125,
                "ValueType": 4,
            },
        )
        self.assertEqual(sum(counts.values()), 263)

    def test_specialized_matrix_count_must_match_source_surface(self) -> None:
        changed = copy.deepcopy(self.matrix)
        block = next(row for row in changed["rows"] if row["id"] == "block")
        block["corpusCount"] = 0
        surface = json.loads(SURFACE_PATH.read_text(encoding="utf-8"))
        diagnostics: list[dict[str, str]] = []
        _check_corpus_surface_counts(changed, surface, diagnostics)
        self.assertEqual(
            [item["code"] for item in diagnostics],
            ["TRANSFORMATION_SURFACE_COUNT_MISMATCH"],
        )

    def test_property_transformation_surface_is_reproducible(self) -> None:
        expected = json.loads(
            PROPERTY_SURFACE_PATH.read_text(encoding="utf-8")
        )
        actual = analyze_property_transformation_surface(REPOSITORY_ROOT)
        self.assertEqual(actual, expected)

    def test_property_transformation_surface_is_schema_valid(self) -> None:
        surface = json.loads(
            PROPERTY_SURFACE_PATH.read_text(encoding="utf-8")
        )
        validate_instance_against_schema(
            surface,
            REPOSITORY_ROOT
            / "schemas"
            / "property-transformation-surface.schema.json",
        )

    def test_property_categories_are_total_and_mutually_exclusive(self) -> None:
        surface = json.loads(
            PROPERTY_SURFACE_PATH.read_text(encoding="utf-8")
        )
        self.assertEqual(
            sum(row["count"] for row in surface["categories"]),
            surface["propertyCount"],
        )
        self.assertEqual(surface["propertyCount"], 267)

    def test_property_matrix_count_must_match_source_surface(self) -> None:
        changed = copy.deepcopy(self.matrix)
        attribute = next(
            row
            for row in changed["rows"]
            if row["id"] == "attribute-property"
        )
        attribute["corpusCount"] = 44
        surface = json.loads(
            PROPERTY_SURFACE_PATH.read_text(encoding="utf-8")
        )
        diagnostics: list[dict[str, str]] = []
        _check_property_surface(changed, surface, diagnostics)
        self.assertEqual(
            [item["code"] for item in diagnostics],
            ["TRANSFORMATION_PROPERTY_COUNT_MISMATCH"],
        )
