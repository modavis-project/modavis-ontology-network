# Security policy

Ontology publication can create integrity and supply-chain risks through
mutable imports, misleading redirects, compromised release artifacts,
over-broad mappings, or unsafe examples and tooling.

Report suspected ontology-integrity, redirect, artifact, or supply-chain
vulnerabilities through the repository's
[private vulnerability-reporting form](https://github.com/modavis-project/modavis-ontology-network/security/advisories/new).
Do not publish exploit details in an unrestricted issue before the maintainer
has assessed disclosure and migration impact.

Release preparation must use locked imports, checksum-indexed artifacts,
reproducible builds, protected branches, immutable tags/releases, and tested
W3ID redirects. A security correction may tighten a `0.x` patch only when the
previous behavior is unsafe and the release notes identify the change.
