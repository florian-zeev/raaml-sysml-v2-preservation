# Native TypeScript implementation

This directory contains the smallest native TypeScript implementation of the
RAAML 1.1 preservation mapping. It is intended for Node.js applications,
including TypeScript applications such as M45.

It does not call Python, Java, Docker, or a network service at runtime.

## What it does

The library:

1. reads the 17 locked normative RAAML 1.1 XMI definition files;
2. extracts and canonicalizes the facts covered by the preservation contract;
3. creates the SysML v2 representation and one preservation manifest per
   source artifact;
4. reconstructs the SysML v1 XMI artifacts from those outputs; and
5. lets a caller compare the reconstructed canonical facts with the source
   canonical facts.

It does not define a new version of RAAML. It also does not claim to transform
arbitrary user-authored RAAML models.

## Requirements

- Node.js 24 or newer
- npm
- the locked source files fetched by the repository's `./raaml sources fetch`
  command

## Build and test it

From the repository root:

```text
./raaml sources fetch
npm ci --prefix typescript
npm test --prefix typescript
```

The test processes all 17 source artifacts and requires:

- the TypeScript canonical facts to have the reference SHA-256;
- the generated SysML v2 text to have the reference SHA-256;
- all 17 artifacts to be reconstructed; and
- the reconstructed canonical facts to equal the source canonical facts.

To compile the library without running the tests:

```text
npm ci --prefix typescript
npm run build --prefix typescript
```

The compiled JavaScript and declarations are written to `typescript/dist/`.

## Add it to another TypeScript application

Until this package is published, build it and install it from its local
directory. Replace the example path with the path to this repository:

```text
cd /path/to/raaml-sysml-v2-preservation
npm ci --prefix typescript
npm run build --prefix typescript

cd /path/to/your-application
npm install /path/to/raaml-sysml-v2-preservation/typescript
```

For a pnpm application, use this final command instead:

```text
pnpm add /path/to/raaml-sysml-v2-preservation/typescript
```

This adds the compiled TypeScript library to the application. It does not add
the Python reference implementation or the Java validators.

## Call it from TypeScript

The API accepts data supplied by the caller. It does not assume a directory
layout and does not read files by itself.

```ts
import fs from "node:fs";

import {
  extractFacts,
  forward,
  reverse,
  type StandardsLock,
} from "@florian-zeev/raaml-sysml-v2-preservation";

const lock = JSON.parse(
  fs.readFileSync("standards.lock.json", "utf8"),
) as StandardsLock;

const lockedDefinitions = lock.artifacts.filter(
  (artifact) => artifact.collection === "raaml-1.1-definitions",
);
const sources = new Map(
  lockedDefinitions.map((artifact) => [
    artifact.filename,
    fs.readFileSync(`sources/cache/${artifact.filename}`),
  ]),
);

const source = extractFacts({lock, sources});
const mapped = forward(source.canonical);
const reconstructed = reverse({
  lock,
  sysml: mapped.sysml,
  manifests: mapped.manifests,
});
```

The caller decides where the source bytes come from and where the outputs go.
They may come from files, object storage, a database, or an application upload.

## Why there is one runtime dependency

The only direct runtime dependency is
[`saxes`](https://www.npmjs.com/package/saxes), a streaming XML parser. It
provides standards-compliant, namespace-aware XML parsing and reports malformed
XML. The library adds its own size, depth, reference, DTD, and XInclude
restrictions before treating the result as engineering data.

`saxes` does not understand RAAML, SysML, the canonical fact contract,
preservation manifests, or the forward and reverse mappings. Those parts are
implemented here.

## Scope of the Python and Java code

Python remains the reference implementation and is used to check that the
TypeScript implementation produces the same canonical and mapped outputs.
Java is used only by the repository's SysML v1 validation evidence. Neither is
required by an application calling the TypeScript library.
