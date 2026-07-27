from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from urllib.parse import urlsplit
from xml.parsers import expat


MAX_XML_BYTES = 10 * 1024 * 1024
MAX_XML_DEPTH = 256
MAX_ATTRIBUTES_PER_ELEMENT = 256
MAX_ATTRIBUTE_BYTES = 1024 * 1024
MAX_TEXT_BYTES = 32 * 1024 * 1024
XINCLUDE_NAMESPACE = "http://www.w3.org/2001/XInclude"
REFERENCE_ATTRIBUTES = {"href"}
PATH_TRAVERSAL = re.compile(r"(^|[\\/])\.\.([\\/]|$)")


@dataclass(frozen=True)
class XmlLimits:
    input_bytes: int = MAX_XML_BYTES
    depth: int = MAX_XML_DEPTH
    attributes_per_element: int = MAX_ATTRIBUTES_PER_ELEMENT
    attribute_bytes: int = MAX_ATTRIBUTE_BYTES
    text_bytes: int = MAX_TEXT_BYTES


class UnsafeXmlError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def preflight_xml(
    path: Path,
    *,
    allowed_remote_documents: frozenset[str] = frozenset(),
    limits: XmlLimits = XmlLimits(),
) -> None:
    if path.is_symlink():
        raise UnsafeXmlError("XML_SYMLINK", "XML input must not be a symbolic link")
    try:
        size = path.stat().st_size
    except FileNotFoundError as error:
        raise UnsafeXmlError("XML_MISSING", "XML input does not exist") from error
    if not path.is_file():
        raise UnsafeXmlError("XML_NOT_REGULAR", "XML input must be a regular file")
    if size > limits.input_bytes:
        raise UnsafeXmlError(
            "XML_INPUT_LIMIT",
            f"XML input exceeds {limits.input_bytes} bytes",
        )

    parser = expat.ParserCreate(namespace_separator="}")
    depth = 0
    text_bytes = 0

    def reject_doctype(*_args: object) -> None:
        raise UnsafeXmlError("XML_DTD_FORBIDDEN", "DTD declarations are forbidden")

    def reject_entity(*_args: object) -> None:
        raise UnsafeXmlError(
            "XML_ENTITY_FORBIDDEN",
            "entity declarations and expansion are forbidden",
        )

    def reject_external(*_args: object) -> int:
        raise UnsafeXmlError(
            "XML_EXTERNAL_ENTITY_FORBIDDEN",
            "external entities are forbidden",
        )

    def start(name: str, attributes: dict[str, str]) -> None:
        nonlocal depth
        depth += 1
        if depth > limits.depth:
            raise UnsafeXmlError(
                "XML_DEPTH_LIMIT",
                f"XML nesting exceeds {limits.depth}",
            )
        if name == f"{XINCLUDE_NAMESPACE}}}include":
            raise UnsafeXmlError("XML_XINCLUDE_FORBIDDEN", "XInclude is forbidden")
        if len(attributes) > limits.attributes_per_element:
            raise UnsafeXmlError(
                "XML_ATTRIBUTE_COUNT_LIMIT",
                f"element has more than {limits.attributes_per_element} attributes",
            )
        attribute_bytes = sum(
            len(key.encode("utf-8")) + len(value.encode("utf-8"))
            for key, value in attributes.items()
        )
        if attribute_bytes > limits.attribute_bytes:
            raise UnsafeXmlError(
                "XML_ATTRIBUTE_SIZE_LIMIT",
                f"element attributes exceed {limits.attribute_bytes} bytes",
            )
        for raw_name, value in attributes.items():
            local_name = raw_name.rsplit("}", 1)[-1]
            if local_name in REFERENCE_ATTRIBUTES:
                _check_reference(value, allowed_remote_documents)

    def end(_name: str) -> None:
        nonlocal depth
        depth -= 1

    def characters(value: str) -> None:
        nonlocal text_bytes
        text_bytes += len(value.encode("utf-8"))
        if text_bytes > limits.text_bytes:
            raise UnsafeXmlError(
                "XML_TEXT_LIMIT",
                f"XML text exceeds {limits.text_bytes} bytes",
            )

    parser.StartDoctypeDeclHandler = reject_doctype
    parser.EntityDeclHandler = reject_entity
    parser.ExternalEntityRefHandler = reject_external
    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.CharacterDataHandler = characters

    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                parser.Parse(block, False)
            parser.Parse(b"", True)
    except UnsafeXmlError:
        raise
    except (OSError, expat.ExpatError) as error:
        raise UnsafeXmlError("XML_MALFORMED", str(error)) from error


def _check_reference(value: str, allowed_remote_documents: frozenset[str]) -> None:
    document = value.split("#", 1)[0]
    if not document:
        return
    if PATH_TRAVERSAL.search(document):
        raise UnsafeXmlError(
            "XML_PATH_TRAVERSAL",
            f"reference contains path traversal: {document}",
        )
    parsed = urlsplit(document)
    if parsed.scheme == "file":
        raise UnsafeXmlError(
            "XML_FILE_REFERENCE_FORBIDDEN",
            "file references are forbidden",
        )
    if parsed.scheme in {"http", "https"}:
        if document not in allowed_remote_documents:
            raise UnsafeXmlError(
                "XML_REMOTE_REFERENCE_UNPINNED",
                f"remote reference is not in the pinned catalog: {document}",
            )
        return
    if parsed.scheme:
        raise UnsafeXmlError(
            "XML_REFERENCE_SCHEME_FORBIDDEN",
            f"reference scheme is forbidden: {parsed.scheme}",
        )
    if document.startswith(("/", "\\")):
        raise UnsafeXmlError(
            "XML_ABSOLUTE_PATH_FORBIDDEN",
            "absolute filesystem references are forbidden",
        )
