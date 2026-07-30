export interface XmlOutputNode {
  readonly name: string;
  readonly attributes: Map<string, string>;
  readonly children: XmlOutputNode[];
  text?: string;
}

export function xmlElement(
  name: string,
  attributes: Record<string, string> = {},
): XmlOutputNode {
  return {
    name,
    attributes: new Map(Object.entries(attributes)),
    children: [],
  };
}

export function appendXml(
  parent: XmlOutputNode,
  name: string,
  attributes: Record<string, string> = {},
): XmlOutputNode {
  const child = xmlElement(name, attributes);
  parent.children.push(child);
  return child;
}

export function serializeXml(root: XmlOutputNode): Uint8Array {
  const lines = ["<?xml version='1.0' encoding='utf-8'?>"];
  render(root, 0, lines);
  return new TextEncoder().encode(`${lines.join("\n")}\n`);
}

function render(node: XmlOutputNode, depth: number, lines: string[]): void {
  const indent = "  ".repeat(depth);
  const attributes = [...node.attributes]
    .map(([name, value]) => ` ${name}="${escapeAttribute(value)}"`)
    .join("");
  if (node.children.length === 0 && node.text === undefined) {
    lines.push(`${indent}<${node.name}${attributes} />`);
    return;
  }
  if (node.children.length === 0) {
    lines.push(
      `${indent}<${node.name}${attributes}>${escapeText(node.text ?? "")}</${node.name}>`,
    );
    return;
  }
  lines.push(`${indent}<${node.name}${attributes}>`);
  for (const child of node.children) {
    render(child, depth + 1, lines);
  }
  lines.push(`${indent}</${node.name}>`);
}

function escapeAttribute(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("\r", "&#13;")
    .replaceAll("\n", "&#10;")
    .replaceAll("\t", "&#09;");
}

function escapeText(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}
