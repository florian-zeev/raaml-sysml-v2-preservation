# Security policy

## Reporting

Do not publish a suspected security vulnerability in an issue, discussion,
pull request, or other public channel. Use GitHub's
[private vulnerability reporting](https://github.com/florian-zeev/raaml-sysml-v2-preservation/security/advisories/new)
to send the report directly to the maintainer.

Include the affected tag or commit, impact, reproduction steps, and a minimal
project-authored test case when possible. Do not attach official standards
files or excluded generated corpus material.

## Supported versions

Security fixes target the current `main` branch and the latest signed
candidate. Historical release candidates are retained as immutable evidence
and are not maintained as separate supported versions.

## Security boundary

XML, XMI, manifests, and model files must be treated as untrusted input.
Implementations must follow the secure XML and reference-handling requirements
in the reference implementation plan, including disabling external entities,
DTD processing, XInclude, implicit network access, and unrestricted file
resolution.

No released command may retrieve network content unless the user invokes an
explicit source-acquisition command.
