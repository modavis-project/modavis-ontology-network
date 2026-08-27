# MODAVIS Ontology Network governance

## Development authority

The initial ontology-network release is `0.1.0`. Dominik Ukolov is the recorded
lead developer, editor, release authority, and initial publisher,
identified by ORCID and affiliated with Digital Humanities (Image/Object) at
Friedrich-Schiller-University Jena. “MODAVIS
Project” is the project name, not a separate legal or publishing agent. The
affiliations in `AUTHORS.md` are contributor metadata and do not establish
institutional publication authority or endorsement.

## Decision roles

- **Lead editor:** maintains the native semantic model, coordinates releases,
  records decisions, and classifies compatibility impact.
- **Domain reviewer:** reviews musical-instrument and heritage meaning.
- **Ontology-engineering reviewer:** reviews OWL, SKOS, SHACL, imports,
  alignments, and inference consequences.
- **Implementation reviewer:** verifies at least one independent consumer; a
  separately governed VAO application profile may serve as one consumer but is
  not a hidden MODAVIS release dependency.
- **Release authority:** approves the publisher, licenses, public repository,
  publication host, W3ID submission, and announcement.

The lead editor may prepare release candidates but must not invent missing
review or release-authority decisions. The first public release requires named
reviewers for the domain, ontology-engineering, and implementation roles. One
qualified person may hold multiple roles when the release record states the
overlap and its independence limitation. Independent semantic review is
strongly recommended but is not a precondition for the individually stewarded
initial 0.1.0 release. A self-review must never be described as independent,
and the absence of independent review must remain visible in the release
record and public documentation.

For 0.1.0, Dominik Ukolov holds all three review roles. The review covers
organological meaning, digital-humanities use, OWL/SKOS/SHACL design, data
modeling, and implementation behavior. It is an accountable self-review by the
lead editor, with method, findings, and limitations recorded in
`docs/EVALUATION_AND_RELEASE_READINESS.md` and structured release metadata.
Tool-assisted technical auditing is not represented as a human reviewer,
independent peer review, or release authority.

## Change control

Every public-term proposal must include a definition, module, competency
question, examples, SHACL impact, external alignments, and compatibility
classification. Mapping strength must be conservative. Public IRIs are never
reused for a different meaning; released terms are deprecated rather than
deleted.

Every public term identifies its declaration-owning ontology with
`rdfs:isDefinedBy` and records semantic maturity with `vs:term_status`.
The initial 0.x terms use `testing`: this is a maturity statement, not a license
to reuse an IRI for another meaning. Promotion to `stable` or transition to
`deprecated` is a reviewed release change; deprecation also uses
`owl:deprecated true` and names its replacement where one exists.

Every reportable SHACL node, property, logical-alternative, and SPARQL
constraint has a stable profile IRI, label, message where it can produce a
result, and explicit severity. Constraints are changed under the same
compatibility rules as ontology terms.

During `0.x`, a logical breaking change increments the minor version. Patch
releases may not invalidate conforming data except for a documented security
correction. Ontology releases and VAO releases have independent version lines.

## Release rule

No tag, deployment, W3ID request, DOI deposit, or announcement is authorized
while `config/release-metadata.json` has `noPublish` set to `true` or any
required approval is unresolved. Publication actions belong to the release
authority and, within the wider framework, the Persistor publication boundary.
Removing the guard requires an authorization agent and timestamp, a publication
date, structured completed reviewer records, explicit disclosure of any review
independence limitation, final citation and public-facing wording, and
`VERSION` equal to the semantic release version. The builder then produces a
final archive but still performs no deployment, tag, or W3ID submission itself.
