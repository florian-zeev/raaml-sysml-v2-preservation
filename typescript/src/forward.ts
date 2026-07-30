import path from "node:path";

import {RaamlPreservationError} from "./errors.js";
import {sha256, stableJson, type JsonObject, type JsonValue} from "./json.js";
import type {CanonicalRaamlFacts} from "./types.js";

const FULL_CORPUS_ID = "milestone-4-full-corpus";
export const FULL_CORPUS_V2_FILENAME = "raaml-full-corpus.sysml";
const SAFE_NAME = /[^A-Za-z0-9_]/g;

type RecordValue = Record<string, any>;

export interface PreservationManifest extends JsonObject {
  readonly schemaVersion: "0.1.0";
  readonly documentKind: "raaml-preservation-manifest";
  readonly payloadSha256: string;
  readonly payload: JsonObject;
}

export interface ForwardResult {
  readonly sysml: string;
  readonly manifests: ReadonlyMap<string, PreservationManifest>;
  readonly canonical: CanonicalRaamlFacts;
}

export function forward(canonical: CanonicalRaamlFacts): ForwardResult {
  requireFullCorpusCoverage(canonical);
  requireReferenceClosure(canonical);
  const sysml = renderFullCorpusSysml(canonical);
  const sysmlBytes = new TextEncoder().encode(sysml);
  const manifests = new Map<string, PreservationManifest>();
  for (const artifact of canonical.artifacts as RecordValue[]) {
    const filename =
      `${path.parse(artifact.filename as string).name}.preservation.json`;
    manifests.set(
      filename,
      createManifest(canonical, artifact, sysmlBytes),
    );
  }
  return {sysml, manifests, canonical};
}

export function renderFullCorpusSysml(
  canonical: CanonicalRaamlFacts,
): string {
  const lines = [
    "package RaamlFullCorpus {",
    "    private import ScalarValues::*;",
    "    private occurrence def PreservedAssociationEnd;",
    "    metadata def Raaml_BaseAnnotation;",
    "    metadata def Raaml_LibraryClass :> Raaml_BaseAnnotation;",
    "    metadata def Raaml_AssociationClass :> Raaml_BaseAnnotation;",
    "    metadata def Raaml_LibraryAssociation :> Raaml_BaseAnnotation;",
  ];
  for (const artifact of canonical.artifacts as RecordValue[]) {
    const packageName = identifier(path.parse(artifact.filename).name);
    lines.push(`    package ${packageName} {`);
    for (const declaration of artifact.declarations as RecordValue[]) {
      const name = identifier(declaration.name ?? declaration.id);
      switch (declaration.kind) {
        case "Stereotype":
          lines.push(
            `        metadata def ${name} :> RaamlFullCorpus::Raaml_BaseAnnotation;`,
          );
          break;
        case "Class":
          lines.push("        #RaamlFullCorpus::Raaml_LibraryClass");
          lines.push(`        occurrence def ${name};`);
          break;
        case "Association":
        case "AssociationClass": {
          const marker = declaration.kind === "AssociationClass"
            ? "Raaml_AssociationClass"
            : "Raaml_LibraryAssociation";
          lines.push(`        #RaamlFullCorpus::${marker}`);
          lines.push(`        connection def ${name} {`);
          for (
            const [endName, endType] of associationEnds(
              canonical,
              artifact,
              declaration,
            )
          ) {
            lines.push(`            end ${endName} : ${endType};`);
          }
          lines.push("        }");
          break;
        }
        case "Enumeration":
          lines.push(`        enum def ${name} {`);
          for (const literal of declaration.literals as RecordValue[]) {
            lines.push(`            ${identifier(literal.name)};`);
          }
          lines.push("        }");
          break;
        default:
          fail(
            "FORWARD_DECLARATION_KIND",
            `unsupported declaration kind: ${declaration.kind}`,
          );
      }
      for (const constraint of declaration.constraints as RecordValue[]) {
        const constraintName = identifier(
          `${name}_${constraint.name ?? "Constraint"}`,
        );
        lines.push(`        constraint def ${constraintName};`);
      }
    }
    lines.push("    }");
  }
  lines.push("}");
  return `${lines.join("\n")}\n`;
}

function createManifest(
  canonical: CanonicalRaamlFacts,
  artifact: RecordValue,
  sysmlBytes: Uint8Array,
): PreservationManifest {
  const artifactFacts = structuredClone(canonical) as CanonicalRaamlFacts;
  (artifactFacts.artifacts as RecordValue[]).splice(
    0,
    artifactFacts.artifacts.length,
    structuredClone(artifact),
  );
  const payload: JsonObject = {
    scopeId: FULL_CORPUS_ID,
    artifactId: artifact.artifactId,
    sourceFilename: artifact.filename,
    sourceSha256: artifact.sha256,
    v2Filename: FULL_CORPUS_V2_FILENAME,
    v2Sha256: sha256(sysmlBytes),
    nativeTargets: nativeTargets(artifactFacts),
    canonicalFacts: artifactFacts,
  };
  return {
    schemaVersion: "0.1.0",
    documentKind: "raaml-preservation-manifest",
    payloadSha256: sha256(stableJson(payload)),
    payload,
  };
}

function nativeTargets(canonical: CanonicalRaamlFacts): JsonObject[] {
  const targets: JsonObject[] = [];
  for (const artifact of canonical.artifacts as RecordValue[]) {
    const packageName = identifier(path.parse(artifact.filename).name);
    for (const declaration of artifact.declarations as RecordValue[]) {
      const name = identifier(declaration.name ?? declaration.id);
      const carrier = ({
        Stereotype: "metadata def",
        Class: "occurrence def",
        Association: "connection def",
        AssociationClass: "connection def",
        Enumeration: "enum def",
      } as Record<string, string>)[declaration.kind];
      if (!carrier) {
        fail(
          "FORWARD_DECLARATION_KIND",
          `unsupported declaration kind: ${declaration.kind}`,
        );
      }
      const terminator = carrier === "connection def" || carrier === "enum def"
        ? " {"
        : ";";
      targets.push({
        canonicalId: declaration.id,
        carrier,
        declaration: `${carrier} ${name}${terminator}`,
        qualifiedName: `RaamlFullCorpus::${packageName}::${name}`,
      });
      for (const constraint of declaration.constraints as RecordValue[]) {
        const constraintName = identifier(
          `${name}_${constraint.name ?? "Constraint"}`,
        );
        targets.push({
          canonicalId: constraint.id,
          carrier: "constraint def",
          declaration: `constraint def ${constraintName};`,
          qualifiedName:
            `RaamlFullCorpus::${packageName}::${constraintName}`,
        });
      }
    }
  }
  return targets.sort((left, right) =>
    compare(left.canonicalId as string, right.canonicalId as string)
  );
}

function associationEnds(
  canonical: CanonicalRaamlFacts,
  currentArtifact: RecordValue,
  declaration: RecordValue,
): [string, string][] {
  const properties = new Map<string, RecordValue>();
  const declarations = new Map<
    string,
    {artifact: RecordValue; declaration: RecordValue}
  >();
  for (const artifact of canonical.artifacts as RecordValue[]) {
    for (const candidate of artifact.declarations as RecordValue[]) {
      declarations.set(candidate.id, {artifact, declaration: candidate});
      for (
        const propertyRecord of [
          ...candidate.properties,
          ...candidate.ownedEnds,
        ] as RecordValue[]
      ) {
        properties.set(propertyRecord.id, propertyRecord);
      }
    }
  }

  const result: [string, string][] = [];
  const usedNames = new Set<string>();
  (declaration.memberEnds as RecordValue[]).forEach((reference, offset) => {
    const ordinal = offset + 1;
    const propertyRecord = properties.get(reference.target);
    let endName: string;
    let endType: string;
    if (!propertyRecord || propertyRecord.type === null) {
      endName = `end${ordinal}`;
      endType = "PreservedAssociationEnd";
    } else {
      endName = identifier(`end_${propertyRecord.name ?? ordinal}`);
      const target = declarations.get(propertyRecord.type.target);
      if (!target) {
        endType = "PreservedAssociationEnd";
      } else {
        const targetName = identifier(
          target.declaration.name ?? target.declaration.id,
        );
        endType = target.artifact.artifactId === currentArtifact.artifactId
          ? targetName
          : `${identifier(path.parse(target.artifact.filename).name)}::${targetName}`;
      }
    }
    if (usedNames.has(endName)) {
      endName = `${endName}${ordinal}`;
    }
    usedNames.add(endName);
    result.push([endName, endType]);
  });
  while (result.length < 2) {
    const ordinal = result.length + 1;
    result.push([`end${ordinal}`, "PreservedAssociationEnd"]);
  }
  return result;
}

function requireFullCorpusCoverage(canonical: CanonicalRaamlFacts): void {
  if (canonical.artifacts.length !== 17) {
    fail(
      "FULL_CORPUS_ARTIFACTS",
      `expected 17 artifacts, got ${canonical.artifacts.length}`,
    );
  }
  const declarationCount = canonical.artifacts.reduce(
    (total, artifact) =>
      total + ((artifact as RecordValue).declarations as unknown[]).length,
    0,
  );
  if (declarationCount !== 283) {
    fail(
      "FULL_CORPUS_DECLARATIONS",
      `expected 283 declarations, got ${declarationCount}`,
    );
  }
}

function requireReferenceClosure(value: JsonValue): void {
  const known = new Set<string>();
  const references: string[] = [];
  const visit = (child: JsonValue): void => {
    if (Array.isArray(child)) {
      child.forEach(visit);
    } else if (child !== null && typeof child === "object") {
      const identifierValue = child.id;
      if (typeof identifierValue === "string") {
        known.add(identifierValue);
      }
      if (
        typeof child.role === "string" &&
        typeof child.sourceForm === "string" &&
        typeof child.target === "string"
      ) {
        references.push(child.target);
      }
      Object.values(child).forEach(visit);
    }
  };
  visit(value);
  const missing = references.filter(
    (target) => !target.startsWith("external::") && !known.has(target),
  );
  if (missing.length > 0) {
    fail(
      "REFERENCE_TARGET_MISSING",
      `corpus has ${missing.length} unresolved target(s): ${missing.slice(0, 3).join(", ")}`,
    );
  }
}

function identifier(value: string): string {
  let result = value.replace(SAFE_NAME, "_");
  if (!result || /^\d/.test(result)) {
    result = `_${result}`;
  }
  return result;
}

function compare(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0;
}

function fail(code: string, message: string): never {
  throw new RaamlPreservationError(code, message);
}
