from __future__ import annotations

import hashlib
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from raaml_preservation.cli import main
from raaml_preservation.sources import (
    LockError,
    fetch_sources,
    load_lock,
    verify_sources,
)


class FakeResponse:
    def __init__(self, payload: bytes, url: str) -> None:
        self.payload = payload
        self.url = url
        self.consumed = False

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def geturl(self) -> str:
        return self.url

    def read(self, size: int) -> bytes:
        del size
        if self.consumed:
            return b""
        self.consumed = True
        return self.payload


def make_artifact(filename: str, payload: bytes) -> dict[str, object]:
    return {
        "id": "fixture",
        "collection": "fixture-collection",
        "standard": "Fixture",
        "standardVersion": "1.0",
        "kind": "xmi",
        "normativeStatus": "test",
        "omgFileId": "test/fixture",
        "authoritativeUrl": "https://example.invalid/fixture.xmi",
        "filename": filename,
        "byteSize": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "redistribution": {
            "status": "redistributable",
            "committed": True,
        },
    }


def write_lock(root: Path, artifact: dict[str, object]) -> Path:
    path = root / "standards.lock.json"
    path.write_text(
        json.dumps(
            {
                "schemaVersion": "0.1.0",
                "status": "partial",
                "retrievedAt": "2026-07-27",
                "artifacts": [artifact],
            }
        ),
        encoding="utf-8",
    )
    return path


class SourceVerificationTests(unittest.TestCase):
    def test_repository_lock_contains_the_17_official_definitions(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        lock = load_lock(repository_root / "standards.lock.json")

        artifacts = [
            artifact
            for artifact in lock["artifacts"]
            if artifact["collection"] == "raaml-1.1-definitions"
        ]
        self.assertEqual(len(artifacts), 17)
        self.assertEqual(len({artifact["id"] for artifact in artifacts}), 17)
        self.assertEqual(len({artifact["filename"] for artifact in artifacts}), 17)

    def test_repository_lock_contains_the_complete_milestone_zero_baseline(
        self,
    ) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        lock = load_lock(repository_root / "standards.lock.json")
        artifact_ids = {artifact["id"] for artifact in lock["artifacts"]}

        self.assertEqual(lock["status"], "complete")
        self.assertTrue(
            {
                "raaml-1.1-specification",
                "sysml-2.0-language-specification",
                "sysml-2.0-transformation-specification",
                "sysml-2.0-abstract-syntax",
                "sysml-2.0-v1-to-v2-transformation-model",
                "kerml-1.0-specification",
                "kerml-1.0-abstract-syntax",
                "uml-2.5.1-specification",
                "sysml-1.6-specification",
                "ocl-2.4-specification",
                "ocl-2.4-metamodel",
                "ocl-2.4-essential-metamodel",
                "xmi-2.5.1-specification",
                "xmi-2.5.1-model",
                "xmi-2.5.1-schema",
                "sysml-v2-pilot-2026-04-distribution",
                "temurin-jdk-21.0.11-macos-aarch64",
                "temurin-jdk-21.0.11-linux-x64",
            }.issubset(artifact_ids)
        )

    def test_matching_regular_file_passes(self) -> None:
        payload = b"<fixture/>"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / "cache"
            cache.mkdir()
            (cache / "fixture.xmi").write_bytes(payload)
            lock = write_lock(root, make_artifact("fixture.xmi", payload))

            report = verify_sources(lock_path=lock, source_dir=cache)

            self.assertTrue(report["ok"])
            self.assertEqual(report["summary"], {"checked": 1, "failed": 0})

    def test_changed_byte_fails_hash_and_size_when_appended(self) -> None:
        payload = b"<fixture/>"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / "cache"
            cache.mkdir()
            (cache / "fixture.xmi").write_bytes(payload + b"!")
            lock = write_lock(root, make_artifact("fixture.xmi", payload))

            report = verify_sources(lock_path=lock, source_dir=cache)

            self.assertFalse(report["ok"])
            codes = {item["code"] for item in report["diagnostics"]}
            self.assertEqual(
                codes,
                {"SOURCE_HASH_MISMATCH", "SOURCE_SIZE_MISMATCH"},
            )

    def test_changed_byte_with_same_size_fails_hash(self) -> None:
        payload = b"<fixture/>"
        changed = b"<fiXture/>"
        self.assertEqual(len(payload), len(changed))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / "cache"
            cache.mkdir()
            (cache / "fixture.xmi").write_bytes(changed)
            lock = write_lock(root, make_artifact("fixture.xmi", payload))

            report = verify_sources(lock_path=lock, source_dir=cache)

            self.assertFalse(report["ok"])
            self.assertEqual(
                [item["code"] for item in report["diagnostics"]],
                ["SOURCE_HASH_MISMATCH"],
            )

    def test_symlinked_source_file_is_rejected(self) -> None:
        payload = b"<fixture/>"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / "cache"
            cache.mkdir()
            target = root / "outside.xmi"
            target.write_bytes(payload)
            (cache / "fixture.xmi").symlink_to(target)
            lock = write_lock(root, make_artifact("fixture.xmi", payload))

            report = verify_sources(lock_path=lock, source_dir=cache)

            self.assertFalse(report["ok"])
            self.assertEqual(report["diagnostics"][0]["code"], "SOURCE_SYMLINK")

    def test_filename_with_path_is_rejected(self) -> None:
        payload = b"<fixture/>"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact = make_artifact("../fixture.xmi", payload)
            lock = write_lock(root, artifact)

            with self.assertRaisesRegex(LockError, "must not contain a path"):
                load_lock(lock)

    def test_unknown_collection_is_rejected(self) -> None:
        payload = b"<fixture/>"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / "cache"
            cache.mkdir()
            lock = write_lock(root, make_artifact("fixture.xmi", payload))

            with self.assertRaisesRegex(LockError, "collection not found"):
                verify_sources(
                    lock_path=lock,
                    source_dir=cache,
                    collection="missing",
                )

    def test_fetch_skips_an_existing_verified_file_without_network(self) -> None:
        payload = b"<fixture/>"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / "cache"
            cache.mkdir()
            (cache / "fixture.xmi").write_bytes(payload)
            lock = write_lock(root, make_artifact("fixture.xmi", payload))

            report = fetch_sources(lock_path=lock, source_dir=cache)

            self.assertTrue(report["ok"])
            self.assertEqual(report["summary"]["fetched"], 0)

    def test_fetch_refuses_to_replace_an_unverified_file(self) -> None:
        payload = b"<fixture/>"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / "cache"
            cache.mkdir()
            (cache / "fixture.xmi").write_bytes(b"changed")
            lock = write_lock(root, make_artifact("fixture.xmi", payload))

            report = fetch_sources(lock_path=lock, source_dir=cache)

            self.assertFalse(report["ok"])
            self.assertEqual(
                report["diagnostics"][0]["code"],
                "SOURCE_EXISTS_UNVERIFIED",
            )

    def test_fetch_retries_a_transient_server_failure(self) -> None:
        payload = b"<fixture/>"
        url = "https://example.invalid/fixture.xmi"
        transient_error = HTTPError(url, 503, "Unavailable", {}, None)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / "cache"
            lock = write_lock(root, make_artifact("fixture.xmi", payload))

            with (
                patch(
                    "raaml_preservation.sources.urlopen",
                    side_effect=[
                        transient_error,
                        FakeResponse(payload, url),
                    ],
                ) as opener,
                patch("raaml_preservation.sources.sleep") as retry_sleep,
            ):
                report = fetch_sources(lock_path=lock, source_dir=cache)

            self.assertTrue(report["ok"])
            self.assertEqual(report["summary"]["fetched"], 1)
            self.assertEqual(opener.call_count, 2)
            retry_sleep.assert_called_once_with(1)
            self.assertEqual((cache / "fixture.xmi").read_bytes(), payload)

    def test_fetch_does_not_retry_an_integrity_failure(self) -> None:
        payload = b"<fixture/>"
        changed = b"<fiXture/>"
        url = "https://example.invalid/fixture.xmi"
        self.assertEqual(len(payload), len(changed))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / "cache"
            lock = write_lock(root, make_artifact("fixture.xmi", payload))

            with (
                patch(
                    "raaml_preservation.sources.urlopen",
                    return_value=FakeResponse(changed, url),
                ) as opener,
                patch("raaml_preservation.sources.sleep") as retry_sleep,
            ):
                with self.assertRaisesRegex(
                    LockError,
                    "downloaded SHA-256 does not match",
                ):
                    fetch_sources(lock_path=lock, source_dir=cache)

            opener.assert_called_once()
            retry_sleep.assert_not_called()

    def test_fetch_reports_the_artifact_after_transient_retries_are_exhausted(
        self,
    ) -> None:
        payload = b"<fixture/>"
        url = "https://example.invalid/fixture.xmi"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / "cache"
            lock = write_lock(root, make_artifact("fixture.xmi", payload))

            with (
                patch(
                    "raaml_preservation.sources.urlopen",
                    side_effect=[
                        HTTPError(url, 503, "Unavailable", {}, None),
                        HTTPError(url, 503, "Unavailable", {}, None),
                        HTTPError(url, 503, "Unavailable", {}, None),
                    ],
                ) as opener,
                patch("raaml_preservation.sources.sleep") as retry_sleep,
            ):
                with self.assertRaisesRegex(
                    LockError,
                    "fixture: failed to download .* after 3 attempts",
                ):
                    fetch_sources(lock_path=lock, source_dir=cache)

            self.assertEqual(opener.call_count, 3)
            self.assertEqual(
                [call.args for call in retry_sleep.call_args_list],
                [(1,), (2,)],
            )

    def test_fetch_cli_prints_the_failure_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            diagnostics = root / "fetch.json"
            stderr = StringIO()

            with (
                patch(
                    "raaml_preservation.cli.fetch_sources",
                    side_effect=OSError("network unavailable"),
                ),
                patch("sys.stderr", stderr),
            ):
                result = main(
                    [
                        "sources",
                        "fetch",
                        "--diagnostics",
                        str(diagnostics),
                    ]
                )

            self.assertEqual(result, 1)
            self.assertIn("SOURCE_FETCH_FAILED: network unavailable", stderr.getvalue())
            report = json.loads(diagnostics.read_text(encoding="utf-8"))
            self.assertEqual(
                report["diagnostics"][0]["message"],
                "network unavailable",
            )


if __name__ == "__main__":
    unittest.main()
