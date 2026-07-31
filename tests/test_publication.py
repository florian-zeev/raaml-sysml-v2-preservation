from __future__ import annotations

from pathlib import Path
import unittest

from raaml_preservation.publication import (
    audit_ignore_rules,
    audit_paths,
    audit_repository,
    audit_workflow,
)


class PublicationPathTests(unittest.TestCase):
    def test_project_authored_xmi_fixtures_are_allowed(self) -> None:
        paths = [
            "fixtures/milestone-0/minimal-v1-invalid-reference.xmi",
            "fixtures/milestone-0/minimal-v1-library.xmi",
            "fixtures/milestone-0/minimal-v1-profile.xmi",
        ]

        self.assertEqual(audit_paths(paths, scope="test"), [])

    def test_official_and_generated_material_is_rejected(self) -> None:
        paths = [
            "sources/cache/CoreRAAML.xmi",
            "elsewhere/RAAML-1.1.pdf",
            "generated/raaml-full-corpus.sysml",
            "output/CoreRAAML.preservation.json",
            "reports/facts/canonical-raaml-facts.json",
        ]

        diagnostics = audit_paths(paths, scope="test")

        self.assertEqual(len(diagnostics), len(paths))
        self.assertTrue(
            all(item["code"] == "PUBLICATION_PATH_BLOCKED" for item in diagnostics)
        )


class PublicationPolicyTests(unittest.TestCase):
    def test_workflow_rejects_known_publishing_mechanisms(self) -> None:
        workflow = "permissions:\n  contents: read\nsteps:\n  actions/upload-artifact@v4\n"

        diagnostics = audit_workflow(workflow)

        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(
            diagnostics[0]["code"],
            "PUBLICATION_WORKFLOW_PUBLISHES_OUTPUT",
        )

    def test_missing_required_ignore_rule_is_rejected(self) -> None:
        diagnostics = audit_ignore_rules("/sources/cache/*\n")

        self.assertTrue(diagnostics)
        self.assertTrue(
            all(
                item["code"] == "PUBLICATION_IGNORE_RULE_MISSING"
                for item in diagnostics
            )
        )

    def test_current_repository_passes_automated_publication_audit(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        if not (repository_root / ".git").exists():
            self.skipTest("packaged container source tree has no Git history")

        report = audit_repository(repository_root)

        self.assertTrue(report["ok"], report["diagnostics"])
        self.assertGreater(report["summary"]["checked"], 0)


if __name__ == "__main__":
    unittest.main()
