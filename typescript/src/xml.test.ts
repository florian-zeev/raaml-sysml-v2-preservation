import assert from "node:assert/strict";
import test from "node:test";

import {
  RaamlPreservationError,
  attribute,
  children,
  parseXml,
} from "./index.js";

const encoder = new TextEncoder();

test("parses namespace-aware XML", () => {
  const root = parseXml(encoder.encode(
    '<xmi:XMI xmlns:xmi="urn:xmi" xmlns:uml="urn:uml">' +
      '<uml:Class xmi:id="one" name="Hazard"/>' +
    "</xmi:XMI>",
  ));

  assert.equal(root.local, "XMI");
  assert.equal(root.namespace, "urn:xmi");
  const [classElement] = children(root, "Class", "urn:uml");
  assert.ok(classElement);
  assert.equal(attribute(classElement, "id", "urn:xmi"), "one");
  assert.equal(attribute(classElement, "name"), "Hazard");
});

test("rejects DTD declarations", () => {
  assert.throws(
    () => parseXml(encoder.encode("<!DOCTYPE x><x/>")),
    hasCode("XML_DTD_FORBIDDEN"),
  );
});

test("rejects unpinned remote references", () => {
  assert.throws(
    () => parseXml(encoder.encode('<x href="https://example.com/a.xmi#id"/>')),
    hasCode("XML_REMOTE_REFERENCE_UNPINNED"),
  );
});

test("accepts pinned remote references", () => {
  const root = parseXml(
    encoder.encode('<x href="https://example.com/a.xmi#id"/>'),
    {allowedRemoteDocuments: new Set(["https://example.com/a.xmi"])},
  );
  assert.equal(attribute(root, "href"), "https://example.com/a.xmi#id");
});

test("accepts safe relative references", () => {
  const root = parseXml(encoder.encode('<x href="Other.xmi#id"/>'));
  assert.equal(attribute(root, "href"), "Other.xmi#id");
});

test("rejects path traversal", () => {
  assert.throws(
    () => parseXml(encoder.encode('<x href="../secret.xmi#id"/>')),
    hasCode("XML_PATH_TRAVERSAL"),
  );
});

test("enforces nesting limits", () => {
  assert.throws(
    () => parseXml(encoder.encode("<a><b/></a>"), {limits: {depth: 1}}),
    hasCode("XML_DEPTH_LIMIT"),
  );
});

function hasCode(code: string): (error: unknown) => boolean {
  return (error) =>
    error instanceof RaamlPreservationError && error.code === code;
}
