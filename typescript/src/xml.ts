import { SaxesParser, type SaxesAttributeNS, type SaxesTagNS } from "saxes";

import { RaamlPreservationError } from "./errors.js";

const XINCLUDE_NAMESPACE = "http://www.w3.org/2001/XInclude";
const PATH_TRAVERSAL = /(^|[\\/])\.\.([\\/]|$)/;

export interface XmlLimits {
  readonly inputBytes: number;
  readonly depth: number;
  readonly attributesPerElement: number;
  readonly attributeBytes: number;
  readonly textBytes: number;
}

export const DEFAULT_XML_LIMITS: XmlLimits = Object.freeze({
  inputBytes: 10 * 1024 * 1024,
  depth: 256,
  attributesPerElement: 256,
  attributeBytes: 1024 * 1024,
  textBytes: 32 * 1024 * 1024,
});

export interface XmlName {
  readonly local: string;
  readonly namespace: string;
  readonly prefix: string;
}

export interface XmlAttribute extends XmlName {
  readonly value: string;
}

export interface XmlElement extends XmlName {
  readonly attributes: ReadonlyMap<string, XmlAttribute>;
  readonly children: readonly XmlElement[];
  readonly text: string;
}

interface MutableXmlElement extends XmlName {
  readonly attributes: Map<string, XmlAttribute>;
  readonly children: MutableXmlElement[];
  text: string;
}

export interface ParseXmlOptions {
  readonly allowedRemoteDocuments?: ReadonlySet<string>;
  readonly limits?: Partial<XmlLimits>;
}

export function parseXml(
  bytes: Uint8Array,
  options: ParseXmlOptions = {},
): XmlElement {
  const limits = {...DEFAULT_XML_LIMITS, ...options.limits};
  if (bytes.byteLength > limits.inputBytes) {
    throw new RaamlPreservationError(
      "XML_INPUT_LIMIT",
      `XML input exceeds ${limits.inputBytes} bytes`,
    );
  }

  const allowedRemoteDocuments =
    options.allowedRemoteDocuments ?? new Set<string>();
  const decoder = new TextDecoder("utf-8", {fatal: true});
  let xml: string;
  try {
    xml = decoder.decode(bytes);
  } catch (error) {
    throw new RaamlPreservationError(
      "XML_MALFORMED",
      "XML input is not valid UTF-8",
      {cause: error},
    );
  }

  const stack: MutableXmlElement[] = [];
  let root: MutableXmlElement | undefined;
  let textBytes = 0;
  let parseError: unknown;

  const parser = new SaxesParser({xmlns: true});
  parser.on("doctype", () => {
    throw new RaamlPreservationError(
      "XML_DTD_FORBIDDEN",
      "DTD declarations are forbidden",
    );
  });
  parser.on("error", (error) => {
    parseError = error;
    throw error;
  });
  parser.on("opentag", (tag: SaxesTagNS) => {
    if (stack.length + 1 > limits.depth) {
      throw new RaamlPreservationError(
        "XML_DEPTH_LIMIT",
        `XML nesting exceeds ${limits.depth}`,
      );
    }
    if (tag.uri === XINCLUDE_NAMESPACE && tag.local === "include") {
      throw new RaamlPreservationError(
        "XML_XINCLUDE_FORBIDDEN",
        "XInclude is forbidden",
      );
    }

    const sourceAttributes = Object.values(tag.attributes);
    if (sourceAttributes.length > limits.attributesPerElement) {
      throw new RaamlPreservationError(
        "XML_ATTRIBUTE_COUNT_LIMIT",
        `element has more than ${limits.attributesPerElement} attributes`,
      );
    }

    const attributes = new Map<string, XmlAttribute>();
    let attributeBytes = 0;
    for (const source of sourceAttributes) {
      const attribute = toAttribute(source);
      attributeBytes += Buffer.byteLength(source.name) +
        Buffer.byteLength(source.value);
      if (attribute.local === "href") {
        checkReference(attribute.value, allowedRemoteDocuments);
      }
      attributes.set(expandedName(attribute.namespace, attribute.local), attribute);
    }
    if (attributeBytes > limits.attributeBytes) {
      throw new RaamlPreservationError(
        "XML_ATTRIBUTE_SIZE_LIMIT",
        `element attributes exceed ${limits.attributeBytes} bytes`,
      );
    }

    const element: MutableXmlElement = {
      local: tag.local,
      namespace: tag.uri,
      prefix: tag.prefix,
      attributes,
      children: [],
      text: "",
    };
    const parent = stack.at(-1);
    if (parent) {
      parent.children.push(element);
    } else if (root) {
      throw new RaamlPreservationError(
        "XML_MALFORMED",
        "XML input contains more than one root element",
      );
    } else {
      root = element;
    }
    stack.push(element);
  });
  parser.on("text", (value) => {
    textBytes += Buffer.byteLength(value);
    if (textBytes > limits.textBytes) {
      throw new RaamlPreservationError(
        "XML_TEXT_LIMIT",
        `XML text exceeds ${limits.textBytes} bytes`,
      );
    }
    const current = stack.at(-1);
    if (current) {
      current.text += value;
    }
  });
  parser.on("cdata", (value) => {
    textBytes += Buffer.byteLength(value);
    if (textBytes > limits.textBytes) {
      throw new RaamlPreservationError(
        "XML_TEXT_LIMIT",
        `XML text exceeds ${limits.textBytes} bytes`,
      );
    }
    const current = stack.at(-1);
    if (current) {
      current.text += value;
    }
  });
  parser.on("closetag", () => {
    stack.pop();
  });

  try {
    parser.write(xml).close();
  } catch (error) {
    if (error instanceof RaamlPreservationError) {
      throw error;
    }
    throw new RaamlPreservationError(
      "XML_MALFORMED",
      error instanceof Error ? error.message : String(parseError ?? error),
      {cause: error},
    );
  }
  if (!root || stack.length !== 0) {
    throw new RaamlPreservationError(
      "XML_MALFORMED",
      "XML input does not contain one complete root element",
    );
  }
  return root;
}

export function attribute(
  element: XmlElement,
  local: string,
  namespace = "",
): string | undefined {
  return element.attributes.get(expandedName(namespace, local))?.value;
}

export function children(
  element: XmlElement,
  local?: string,
  namespace?: string,
): readonly XmlElement[] {
  return element.children.filter(
    (child) =>
      (local === undefined || child.local === local) &&
      (namespace === undefined || child.namespace === namespace),
  );
}

export function descendants(
  element: XmlElement,
  predicate: (candidate: XmlElement) => boolean,
): XmlElement[] {
  const matches: XmlElement[] = [];
  const visit = (candidate: XmlElement): void => {
    for (const child of candidate.children) {
      if (predicate(child)) {
        matches.push(child);
      }
      visit(child);
    }
  };
  visit(element);
  return matches;
}

function toAttribute(source: SaxesAttributeNS): XmlAttribute {
  return {
    local: source.local,
    namespace: source.uri,
    prefix: source.prefix,
    value: source.value,
  };
}

function expandedName(namespace: string, local: string): string {
  return `{${namespace}}${local}`;
}

function checkReference(
  value: string,
  allowedRemoteDocuments: ReadonlySet<string>,
): void {
  const [document = ""] = value.split("#", 1);
  if (!document) {
    return;
  }
  if (PATH_TRAVERSAL.test(document)) {
    throw new RaamlPreservationError(
      "XML_PATH_TRAVERSAL",
      `reference contains path traversal: ${document}`,
    );
  }

  if (document.startsWith("/") || document.startsWith("\\")) {
    throw new RaamlPreservationError(
      "XML_ABSOLUTE_PATH_FORBIDDEN",
      "absolute filesystem references are forbidden",
    );
  }
  const scheme = /^([A-Za-z][A-Za-z0-9+.-]*):/.exec(document)?.[1]?.toLowerCase();
  if (!scheme) {
    return;
  }
  if (scheme === "file") {
    throw new RaamlPreservationError(
      "XML_FILE_REFERENCE_FORBIDDEN",
      "file references are forbidden",
    );
  }
  if (scheme === "http" || scheme === "https") {
    if (!allowedRemoteDocuments.has(document)) {
      throw new RaamlPreservationError(
        "XML_REMOTE_REFERENCE_UNPINNED",
        `remote reference is not in the pinned catalog: ${document}`,
      );
    }
    return;
  }
  throw new RaamlPreservationError(
    "XML_REFERENCE_SCHEME_FORBIDDEN",
    `reference scheme is forbidden: ${scheme}`,
  );
}
