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
            }.issubset(ignored)
        )

    def test_image_build_has_no_time_dependent_run_layer(self) -> None:
        dockerfile = (self.repository_root / "Dockerfile").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("\nRUN ", dockerfile)


if __name__ == "__main__":
    unittest.main()
