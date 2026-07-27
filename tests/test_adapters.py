from __future__ import annotations

import io
from pathlib import Path
import tarfile
import tempfile
import unittest
import zipfile

from raaml_preservation.adapters import (
    AdapterError,
    _extract_tar_safely,
    _extract_zip_safely,
)


class ArchiveExtractionTests(unittest.TestCase):
    def test_safe_zip_extracts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "fixture.zip"
            destination = root / "output"
            destination.mkdir()
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("tool/bin/run", b"ok")

            _extract_zip_safely(archive, destination)

            self.assertEqual((destination / "tool/bin/run").read_bytes(), b"ok")

    def test_zip_path_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "fixture.zip"
            destination = root / "output"
            destination.mkdir()
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("../outside", b"unsafe")

            with self.assertRaises(AdapterError):
                _extract_zip_safely(archive, destination)

            self.assertFalse((root / "outside").exists())

    def test_zip_windows_absolute_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "fixture.zip"
            destination = root / "output"
            destination.mkdir()
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("C:\\outside", b"unsafe")

            with self.assertRaises(AdapterError):
                _extract_zip_safely(archive, destination)

    def test_tar_symbolic_link_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "fixture.tar.gz"
            destination = root / "output"
            destination.mkdir()
            with tarfile.open(archive, "w:gz") as bundle:
                member = tarfile.TarInfo("tool/link")
                member.type = tarfile.SYMTYPE
                member.linkname = "../../outside"
                bundle.addfile(member)

            with self.assertRaises(AdapterError):
                _extract_tar_safely(archive, destination)

    def test_tar_path_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "fixture.tar.gz"
            destination = root / "output"
            destination.mkdir()
            with tarfile.open(archive, "w:gz") as bundle:
                payload = b"unsafe"
                member = tarfile.TarInfo("../outside")
                member.size = len(payload)
                bundle.addfile(member, io.BytesIO(payload))

            with self.assertRaises(AdapterError):
                _extract_tar_safely(archive, destination)

            self.assertFalse((root / "outside").exists())


if __name__ == "__main__":
    unittest.main()
