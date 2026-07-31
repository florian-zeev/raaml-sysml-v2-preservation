from __future__ import annotations

from pathlib import Path
import unittest


BASE_REFERENCE = (
    "python:3.14.4-slim-bookworm@"
    "sha256:fc74d22ffd0d5ac395a4b7bdda75a453"
    "9758862c49ebf3005647084631e63789"
)


class ContainerDefinitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository_root = Path(__file__).resolve().parents[1]

    def test_base_image_is_pinned_by_digest(self) -> None:
        dockerfile = (self.repository_root / "Dockerfile").read_text(
            encoding="utf-8"
        )

        self.assertIn(f"FROM --platform=linux/amd64 {BASE_REFERENCE}\n", dockerfile)

    def test_build_context_excludes_third_party_and_generated_material(self) -> None:
        ignored = {
            line.strip()
            for line in (self.repository_root / ".dockerignore")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }

        self.assertTrue(
            {
                ".git",
                "sources/cache/*",
                "tooling/cache",
                "tooling/java/build",
                "reports/*",
                "generated/*",
                "review-evidence",
                "container-evidence",
            }.issubset(ignored)
        )

    def test_build_context_includes_validation_workflow_for_unit_tests(self) -> None:
        rules = (
            self.repository_root / ".dockerignore"
        ).read_text(encoding="utf-8").splitlines()

        self.assertIn("!.github/workflows/validate.yml", rules)

    def test_image_build_has_no_time_dependent_run_layer(self) -> None:
        dockerfile = (self.repository_root / "Dockerfile").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("\nRUN ", dockerfile)

    def test_workflow_separates_development_and_tagged_candidates(self) -> None:
        workflow = (
            self.repository_root / ".github" / "workflows" / "validate.yml"
        ).read_text(encoding="utf-8")

        self.assertIn('release_tag="v0.0.0-dev.$short_commit"', workflow)
        self.assertIn('if [[ "$GITHUB_REF_TYPE" == "tag" ]]', workflow)
        self.assertIn(
            'tagged_commit="$(git rev-parse "$GITHUB_REF_NAME^{commit}")"',
            workflow,
        )
        self.assertNotIn("--release-tag v0.9.0-rc.1", workflow)
        self.assertIn("### Consolidated validation result", workflow)

    def test_workflow_does_not_publish_derived_corpus(self) -> None:
        workflow = (
            self.repository_root / ".github" / "workflows" / "validate.yml"
        ).read_text(encoding="utf-8")

        self.assertNotIn("actions/upload-artifact@", workflow)
        self.assertNotIn("Retain development-build evidence", workflow)
        self.assertNotIn("Retain tagged-candidate evidence", workflow)
        self.assertNotIn("gh release ", workflow)
        self.assertNotIn("docker push ", workflow)
        self.assertNotIn("packages: write", workflow)

    def test_workflow_runs_publication_boundary_audit(self) -> None:
        workflow = (
            self.repository_root / ".github" / "workflows" / "validate.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("./raaml publication audit", workflow)

    def test_workflow_runs_native_typescript_conformance_tests(self) -> None:
        workflow = (
            self.repository_root / ".github" / "workflows" / "validate.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("actions/setup-node@", workflow)
        self.assertIn('node-version: "24"', workflow)
        self.assertIn("npm ci --prefix typescript", workflow)
        self.assertIn("npm test --prefix typescript", workflow)

    def test_independent_review_runs_offline_and_retains_only_summary(self) -> None:
        script = (self.repository_root / "review-reproduce").read_text(
            encoding="utf-8"
        )

        self.assertIn("--network none", script)
        self.assertIn(
            "sources/cache:/workspace/sources/cache:ro",
            script,
        )
        self.assertIn("./raaml sources fetch", script)
        self.assertLess(
            script.index("./raaml sources fetch"),
            script.index("--network none"),
        )
        self.assertNotIn("command -v python3", script)
        self.assertNotIn("python3 --version", script)
        self.assertIn("EXPECTED_CANONICAL_SHA256=", script)
        self.assertIn(
            "--comparison-output /tmp/full-corpus-comparison.json",
            script,
        )
        self.assertNotIn(
            "--comparison-output /evidence/",
            script,
        )
        self.assertNotIn("actions/upload-artifact@", script)


if __name__ == "__main__":
    unittest.main()
