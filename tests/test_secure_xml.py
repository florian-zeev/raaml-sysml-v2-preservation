from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from raaml_preservation.secure_xml import UnsafeXmlError, XmlLimits, preflight_xml


class SecureXmlTests(unittest.TestCase):
    def test_small_local_xml_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fixture.xmi"
            path.write_text(
                '<root href="#local"><child value="ok"/></root>',
                encoding="utf-8",
            )
            preflight_xml(path)

    def test_doctype_is_rejected(self) -> None:
        self.check_rejected(
            b'<!DOCTYPE root [<!ENTITY x "expanded">]><root>&x;</root>',
            "XML_DTD_FORBIDDEN",
        )

    def test_external_entity_is_rejected_without_reading_target(self) -> None:
        self.check_rejected(
            b'<!DOCTYPE root [<!ENTITY x SYSTEM "file:///etc/passwd">]><root>&x;</root>',
            "XML_DTD_FORBIDDEN",
        )

    def test_xinclude_is_rejected(self) -> None:
        self.check_rejected(
            b'<root xmlns:x="http://www.w3.org/2001/XInclude">'
            b'<x:include href="file:///etc/passwd"/></root>',
            "XML_XINCLUDE_FORBIDDEN",
        )

    def test_unpinned_remote_reference_is_rejected(self) -> None:
        self.check_rejected(
            b'<root href="https://example.invalid/model.xmi#id"/>',
            "XML_REMOTE_REFERENCE_UNPINNED",
        )

    def test_file_reference_is_rejected(self) -> None:
        self.check_rejected(
            b'<root href="file:///etc/passwd"/>',
            "XML_FILE_REFERENCE_FORBIDDEN",
        )

    def test_path_traversal_is_rejected(self) -> None:
        self.check_rejected(
            b'<root href="../outside.xmi#id"/>',
            "XML_PATH_TRAVERSAL",
        )

    def test_absolute_path_is_rejected(self) -> None:
        self.check_rejected(
            b'<root href="/etc/passwd"/>',
            "XML_ABSOLUTE_PATH_FORBIDDEN",
        )

    def test_unknown_reference_scheme_is_rejected(self) -> None:
        self.check_rejected(
            b'<root href="jar:https://example.invalid/model.jar!/model.xmi"/>',
            "XML_REFERENCE_SCHEME_FORBIDDEN",
        )

    def test_depth_limit_is_enforced(self) -> None:
        self.check_rejected(b"<a><b><c/></b></a>", "XML_DEPTH_LIMIT")

    def test_input_byte_limit_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fixture.xmi"
            path.write_bytes(b"<root/>")
            with self.assertRaises(UnsafeXmlError) as raised:
                preflight_xml(path, limits=XmlLimits(input_bytes=3))
            self.assertEqual(raised.exception.code, "XML_INPUT_LIMIT")

    def test_attribute_count_limit_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fixture.xmi"
            path.write_bytes(b'<root a="1" b="2"/>')
            with self.assertRaises(UnsafeXmlError) as raised:
                preflight_xml(
                    path,
                    limits=XmlLimits(attributes_per_element=1),
                )
            self.assertEqual(raised.exception.code, "XML_ATTRIBUTE_COUNT_LIMIT")

    def test_attribute_size_limit_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fixture.xmi"
            path.write_bytes(b'<root value="large"/>')
            with self.assertRaises(UnsafeXmlError) as raised:
                preflight_xml(
                    path,
                    limits=XmlLimits(attribute_bytes=5),
                )
            self.assertEqual(raised.exception.code, "XML_ATTRIBUTE_SIZE_LIMIT")

    def test_text_limit_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fixture.xmi"
            path.write_bytes(b"<root>large</root>")
            with self.assertRaises(UnsafeXmlError) as raised:
                preflight_xml(
                    path,
                    limits=XmlLimits(text_bytes=4),
                )
            self.assertEqual(raised.exception.code, "XML_TEXT_LIMIT")

    def test_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target.xmi"
            target.write_bytes(b"<root/>")
            path = root / "fixture.xmi"
            path.symlink_to(target)
            with self.assertRaises(UnsafeXmlError) as raised:
                preflight_xml(path)
            self.assertEqual(raised.exception.code, "XML_SYMLINK")

    def check_rejected(self, payload: bytes, code: str) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fixture.xmi"
            path.write_bytes(payload)
            limits = XmlLimits(depth=2) if code == "XML_DEPTH_LIMIT" else XmlLimits()
            with self.assertRaises(UnsafeXmlError) as raised:
                preflight_xml(path, limits=limits)
            self.assertEqual(raised.exception.code, code)


if __name__ == "__main__":
    unittest.main()
