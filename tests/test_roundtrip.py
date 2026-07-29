from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from src.raaml_preservation.facts import extract_facts
from src.raaml_preservation.roundtrip import (
    RoundTripError,
    create_manifest,
    render_v2,
    select_milestone_three_slice,
    synthetic_id,
    verify_manifest,
)


ROOT = Path(__file__).resolve().parents[1]


class MilestoneThreeRoundTripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _, canonical = extract_facts(ROOT)
        cls.slice = select_milestone_three_slice(canonical)

    def test_slice_exercises_required_artifacts_and_constructs(self) -> None:
        filenames = {
            artifact["filename"] for artifact in self.slice["artifacts"]
        }
        self.assertEqual(
            filenames,
            {
                "CoreRAAML.xmi",
                "CoreRAAMLLib.xmi",
                "GeneralRAAML.xmi",
                "GeneralRAAMLLib.xmi",
                "STPA.xmi",
                "STPALib.xmi",
            },
        )
        undeveloped = next(
            declaration
            for artifact in self.slice["artifacts"]
            for declaration in artifact["declarations"]
            if declaration["name"] == "Undeveloped"
        )
        self.assertEqual(undeveloped["properties"][0]["name"], "base_Element")
        self.assertEqual(undeveloped["icons"][0]["format"]["value"], "SVG")
        self.assertTrue(undeveloped["icons"][0]["location"]["present"])

    def test_manifest_digest_detects_fact_mutation(self) -> None:
        manifest = create_manifest(self.slice)
        corrupted = copy.deepcopy(manifest)
        corrupted["payload"]["canonicalFacts"]["artifacts"][0]["filename"] = (
            "changed.xmi"
        )
        with self.assertRaisesRegex(RoundTripError, "payloadSha256"):
            verify_manifest(corrupted)

    def test_v2_view_uses_resolved_native_carriers(self) -> None:
        text = render_v2(self.slice)
        self.assertIn("metadata def Undeveloped;", text)
        self.assertIn("occurrence def Loss;", text)
        self.assertIn("connection def Causality {", text)
        self.assertIn("constraint def ControllingMeasure_SupplierIsSituation;", text)

    def test_synthetic_id_matches_normative_example(self) -> None:
        self.assertEqual(
            synthetic_id("STPA", "Controller"),
            "_raaml_91a0d44384d4417f8bb0389b94d928b88f545a34",
        )

    def test_manifest_serialization_is_deterministic(self) -> None:
        first = json.dumps(create_manifest(self.slice), sort_keys=True)
        second = json.dumps(create_manifest(self.slice), sort_keys=True)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
