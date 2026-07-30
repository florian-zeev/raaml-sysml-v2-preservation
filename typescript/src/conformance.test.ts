import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";

import {
  RaamlPreservationError,
  asciiPrettyJson,
  extractFacts,
  extractReconstructedFacts,
  forward,
  reverse,
  sha256,
  type PreservationManifest,
  type StandardsLock,
} from "./index.js";

const REPOSITORY_ROOT = path.resolve(import.meta.dirname, "../..");
const EXPECTED_CANONICAL_SHA256 =
  "5203f5704cf086e43605a36c10f4a00182e6d2c75a2584031a3d701514a33967";
const EXPECTED_SYSML_SHA256 =
  "f9fc79f0fc8c8fb1a816edaec5913513a3a58d3c44f492eb952193ace54e2268";

const lock = JSON.parse(
  fs.readFileSync(path.join(REPOSITORY_ROOT, "standards.lock.json"), "utf8"),
) as StandardsLock;
const lockedArtifacts = lock.artifacts.filter(
  (artifact) => artifact.collection === "raaml-1.1-definitions",
);
const sourcesAvailable = lockedArtifacts.every((artifact) =>
  fs.existsSync(
    path.join(REPOSITORY_ROOT, "sources", "cache", artifact.filename),
  )
);

test(
  "TypeScript reproduces the complete canonical round trip",
  {skip: sourcesAvailable ? false : "locked RAAML corpus is not in the local cache"},
  () => {
    const sources = new Map(
      lockedArtifacts.map((artifact) => [
        artifact.filename,
        fs.readFileSync(
          path.join(REPOSITORY_ROOT, "sources", "cache", artifact.filename),
        ),
      ]),
    );
    const source = extractFacts({lock, sources}).canonical;
    assert.equal(
      sha256(asciiPrettyJson(source)),
      EXPECTED_CANONICAL_SHA256,
    );

    const mapped = forward(source);
    assert.equal(sha256(mapped.sysml), EXPECTED_SYSML_SHA256);
    assert.equal(mapped.manifests.size, 17);

    const reconstructed = reverse({
      lock,
      sysml: mapped.sysml,
      manifests: mapped.manifests,
    });
    assert.equal(reconstructed.artifacts.size, 17);
    const actual = extractReconstructedFacts({
      lock,
      sources: reconstructed.artifacts,
    }).canonical;
    assert.equal(asciiPrettyJson(actual), asciiPrettyJson(source));
  },
);

test(
  "TypeScript rejects a changed preservation payload",
  {skip: sourcesAvailable ? false : "locked RAAML corpus is not in the local cache"},
  () => {
    const sources = new Map(
      lockedArtifacts.map((artifact) => [
        artifact.filename,
        fs.readFileSync(
          path.join(REPOSITORY_ROOT, "sources", "cache", artifact.filename),
        ),
      ]),
    );
    const mapped = forward(extractFacts({lock, sources}).canonical);
    const manifests = new Map(mapped.manifests);
    const [name, original] = manifests.entries().next().value as [
      string,
      PreservationManifest,
    ];
    const changed = structuredClone(original);
    (changed.payload as Record<string, unknown>).sourceFilename = "changed.xmi";
    manifests.set(name, changed);

    assert.throws(
      () => reverse({lock, sysml: mapped.sysml, manifests}),
      (error) =>
        error instanceof RaamlPreservationError &&
        error.code === "MANIFEST_DIGEST",
    );
  },
);
