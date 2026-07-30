import {createHash} from "node:crypto";

export type JsonPrimitive = boolean | number | string | null;
export type JsonValue = JsonPrimitive | JsonValue[] | JsonObject;
export interface JsonObject {
  [key: string]: JsonValue;
}

export function stableJson(value: JsonValue): string {
  return `${canonicalJson(value)}\n`;
}

export function canonicalJson(value: JsonValue): string {
  return JSON.stringify(sortJson(value));
}

export function asciiCanonicalJson(value: JsonValue): string {
  return escapeNonAscii(canonicalJson(value));
}

export function prettyJson(value: JsonValue): string {
  return `${JSON.stringify(sortJson(value), null, 2)}\n`;
}

export function asciiPrettyJson(value: JsonValue): string {
  return `${escapeNonAscii(JSON.stringify(sortJson(value), null, 2))}\n`;
}

export function sha256(value: Uint8Array | string): string {
  return createHash("sha256").update(value).digest("hex");
}

function sortJson(value: JsonValue): JsonValue {
  if (Array.isArray(value)) {
    return value.map(sortJson);
  }
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, child]) => [key, sortJson(child)]),
    );
  }
  return value;
}

function escapeNonAscii(value: string): string {
  let result = "";
  for (const character of value) {
    const codePoint = character.codePointAt(0)!;
    if (codePoint <= 0x7f) {
      result += character;
    } else if (codePoint <= 0xffff) {
      result += `\\u${codePoint.toString(16).padStart(4, "0")}`;
    } else {
      const offset = codePoint - 0x10000;
      const high = 0xd800 + (offset >> 10);
      const low = 0xdc00 + (offset & 0x3ff);
      result += `\\u${high.toString(16)}\\u${low.toString(16)}`;
    }
  }
  return result;
}
