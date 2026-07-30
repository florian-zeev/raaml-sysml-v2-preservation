from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from raaml_preservation.facts import extract_facts
from raaml_preservation.release import (
    build_controlled_diff,
    repository_identity,
    write_checksums,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORPUS_AVAILABLE = (
    REPOSITORY_ROOT / "sources" / "cache" / "FTALib.xmi"
).is_file()


class ReleaseFoundationTests(unittest.TestCase):
    def test_packaged_repository_identity_requires_explicit_provenance(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(
                repository_identity(
                    root,
                    supplied_commit="a" * 40,
                    supplied_state="clean",
                ),
                ("a" * 40, "clean"),
            )

    def test_checksums_are_sorted_and_do_not_include_themselves(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "z.txt").write_text("z\n", encoding="utf-8")
            (root / "nested").mkdir()
            (root / "nested" / "a.txt").write_text("a\n", encoding="utf-8")
            records = write_checksums(root)
            self.assertEqual(
                [item["path"] for item in records],
                ["nested/a.txt", "z.txt"],
            )
            checksums = (root / "SHA256SUMS").read_text(encoding="utf-8")
            self.assertNotIn("SHA256SUMS", checksums)


@unittest.skipUnless(
    CORPUS_AVAILABLE,
    "locked RAAML corpus is not in the local cache",
)
class ControlledDiffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _raw, cls.canonical = extract_facts(REPOSITORY_ROOT)

    def test_one_fact_diff_is_byte_deterministic(self) -> None:
        with (
            tempfile.TemporaryDirectory() as first_temporary,
            tempfile.TemporaryDirectory() as second_temporary,
        ):
            first = Path(first_temporary)
            second = Path(second_temporary)
            first_report = build_controlled_diff(self.canonical, first)
            second_report = build_controlled_diff(self.canonical, second)

            self.assertEqual(first_report, second_report)
            self.assertEqual(
                first_report["summary"]["inputFactsChanged"],
                1,
            )
            for filename in ("report.json", "v2.diff", "manifest.diff"):
                self.assertEqual(
                    (first / filename).read_bytes(),
                    (second / filename).read_bytes(),
                )
            parsed = json.loads((first / "report.json").read_text())
            self.assertEqual(
                parsed["changedFact"]["before"],
                "NOT_OCCUR",
            )
            self.assertEqual(
                parsed["changedFact"]["after"],
                "DOES_NOT_OCCUR",
            )


if __name__ == "__main__":
    unittest.main()
