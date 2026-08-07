# Publishing the TypeScript package

The package `@florian-zeev/raaml-sysml-v2-preservation` is independently
versioned from RAAML, the preservation contract, and the signed community
proposal candidates.

Package releases use signed tags of the form:

```text
typescript-v<package-version>
```

For example, package `0.1.0-rc.1` maps to tag
`typescript-v0.1.0-rc.1`.

## First publication

npm requires a package to exist before trusted publishing or staged publishing
can be configured. The first release is therefore the only exception to the
automated staging path:

1. merge the package preparation and publishing-control pull requests;
2. confirm the resulting `main` validation run passes;
3. create and verify the signed package tag;
4. check out that exact tag with a clean working tree;
5. run the package tests and inspect `npm pack --dry-run`;
6. publish the public release candidate under the `next` tag using the
   maintainer's authenticated npm session and two-factor authentication; and
7. configure the package's trusted publisher immediately afterward.

## Subsequent publications

Pushing a signed `typescript-v*` tag starts
`.github/workflows/publish-npm.yml`. The workflow:

- verifies that the tag is signed by an allowed signer;
- requires the tag version to equal `typescript/package.json`;
- runs the TypeScript check and test suite;
- inspects the npm tarball boundary;
- authenticates to npm through GitHub OIDC without a stored publish token; and
- stages the package under the `next` tag.

The trusted publisher is restricted to `npm stage publish`. A maintainer must
review and approve the staged package with npm two-factor authentication before
it becomes public.

The GitHub deployment environment is named `npm`. The npm trusted-publisher
configuration must name `publish-npm.yml` as the workflow and `npm` as the
environment. The npm package should disallow traditional publish tokens after
the trusted publisher is working.

The npm tarball contains the compiled native TypeScript implementation,
declarations, package README, Apache-2.0 license, and notice. It must not contain
the official RAAML source corpus, generated evidence, Python or Java code, or
test files.
