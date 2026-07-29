from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from src.raaml_preservation.facts import extract_facts
from src.raaml_preservation.roundtrip import (
    FULL_CORPUS_V2_FILENAME,
    RoundTripError,
    create_full_corpus_manifest,
    create_manifest,
    forward_full_corpus,
    render_full_corpus_v2,
    render_v2,
    select_milestone_three_slice,
    synthetic_id,
    verify_manifest,
)
from src.raaml_preservation.schemas import validate_instance_against_schema


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


class MilestoneFourForwardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _, cls.canonical = extract_facts(ROOT)

    def test_full_model_covers_every_declaration_and_constraint(self) -> None:
        text = render_full_corpus_v2(self.canonical)
        self.assertIn("package RaamlFullCorpus {", text)
        self.assertIn("private import ScalarValues::*;", text)
        self.assertIn("metadata def Raaml_BaseAnnotation;", text)
        self.assertIn("#RaamlFullCorpus::Raaml_LibraryClass", text)
        self.assertIn("#RaamlFullCorpus::Raaml_LibraryAssociation", text)
        self.assertIn("#RaamlFullCorpus::Raaml_AssociationClass", text)
        self.assertEqual(
            sum(
                len(artifact["declarations"])
                for artifact in self.canonical["artifacts"]
            ),
            283,
        )
        self.assertEqual(
            sum(
                len(declaration["constraints"])
                for artifact in self.canonical["artifacts"]
                for declaration in artifact["declarations"]
            ),
            60,
        )

    def test_full_manifest_is_scoped_to_one_source(self) -> None:
        v2_bytes = render_full_corpus_v2(self.canonical).encode("utf-8")
        artifact = self.canonical["artifacts"][0]
        manifest = create_full_corpus_manifest(
            self.canonical,
            artifact,
            v2_bytes,
        )
        payload = manifest["payload"]
        self.assertEqual(payload["sourceFilename"], artifact["filename"])
        self.assertEqual(payload["v2Filename"], FULL_CORPUS_V2_FILENAME)
        self.assertEqual(len(payload["canonicalFacts"]["artifacts"]), 1)
        self.assertEqual(
            payload["canonicalFacts"]["artifacts"][0]["artifactId"],
            artifact["artifactId"],
        )
        self.assertTrue(
            all("qualifiedName" in target for target in payload["nativeTargets"])
        )
        validate_instance_against_schema(
            manifest,
            ROOT / "schemas" / "preservation-manifest.schema.json",
        )

    def test_full_forward_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory(prefix="raaml-m4-unit-") as temporary:
            root = Path(temporary)
            first = forward_full_corpus(ROOT, root / "first")
            second = forward_full_corpus(ROOT, root / "second")
            first_files = sorted(
                path.relative_to(root / "first")
                for path in (root / "first").rglob("*")
                if path.is_file()
            )
            second_files = sorted(
                path.relative_to(root / "second")
                for path in (root / "second").rglob("*")
                if path.is_file()
            )
            self.assertEqual(first_files, second_files)
            self.assertEqual(len(first["manifests"]), 17)
            self.assertEqual(len(second["manifests"]), 17)
            self.assertEqual(len(first_files), 18)
            for relative in first_files:
                self.assertEqual(
                    (root / "first" / relative).read_bytes(),
                    (root / "second" / relative).read_bytes(),
                )

    def test_design_fragments_are_explicitly_labeled_pseudocode(self) -> None:
        proposal = (
            ROOT / "proposal" / "normative-encoding-v0.1.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "fragments below are **illustrative pseudocode**",
            proposal,
        )
        self.assertIn(
            "generated `.sysml` files are the parser-tested concrete",
            proposal,
        )


if __name__ == "__main__":
    unittest.main()
