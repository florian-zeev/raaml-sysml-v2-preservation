# Security policy

## Reporting

Do not publish a security vulnerability in a public issue before the
maintainer has had a reasonable opportunity to investigate it. Until a
dedicated reporting address is published, contact the repository owner
privately through GitHub.

## Security boundary

XML, XMI, manifests, and model files must be treated as untrusted input.
Implementations must follow the secure XML and reference-handling requirements
in the reference implementation plan, including disabling external entities,
DTD processing, XInclude, implicit network access, and unrestricted file
resolution.

No released command may retrieve network content unless the user invokes an
explicit source-acquisition command.
