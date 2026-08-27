# MODAVIS Ontology Network changelog

## 0.1.0 — 2026-08-27

- finalized the reviewed rc.7 semantics without changing the public ontology
  term set or conformance contract;
- recorded release authorization, the publication date, and the reserved
  Zenodo DOI `10.5281/zenodo.22126086`;
- changed current documentation, citation, dependency, and ontology metadata
  from release-candidate state to the immutable 0.1.0 release; and
- retained the disclosed self-review limitation, conservative mapping policy,
  reproducible release machinery, and complete scientific validation boundary.

## 0.1.0-rc.7 — 2026-08-27

- completed the maintainer-directed domain, ontology-engineering, and
  implementation reviews, recorded all resolved findings, and disclosed the
  tool-assisted self-review and independence boundary without implying external
  peer review or institutional endorsement;
- reduced the public source boundary by retaining detailed working reports,
  non-public input assessments, staging handoff material, and agent instructions
  outside the release repository; replaced them with durable quality,
  interpretation, release-process, and VAO-interoperability documentation;
- clarified the interpretation of open-domain properties, identity layers,
  qualified records, audio coordinates, compatibility statements, and VAO
  mapping ownership through normative scope notes and an interpretation guide;
- closed validation gaps for mismatched membership discovery owners,
  configuration owners, and role-assignment state/configuration scopes;
- adopted `modavis-ontology-network` as the public repository and Pages slug
  and replaced the personal security email with private repository reporting;
- made source-snapshot capture accountable through qualified fixity, a
  timezone-qualified capture instant, and an explicit generating PROV-O
  activity;
- defined knowledge-snapshot fixity without self-reference by binding exact
  assertion membership to one named graph and one checksum-fixed canonical
  N-Quads bitstream under the dated RDFC-1.0 Recommendation;
- checked in the two canonical snapshot materializations with their computed
  sizes and SHA-256 digests, and added conformance constraints for media type,
  timestamp, profile, and materialization identity;
- required timezone offsets for comparable `xsd:dateTime` values and
  disambiguated duplicate public human labels while preserving every IRI;
- replaced the obsolete private VAO 0.2.2 notes with an exact, checksum-pinned
  VAO 0.4.0 co-release contract, corrected VAO's MODAVIS organ IRIs, and added
  a conservative VAO-owned mapping with no unjustified equivalence claims;
- completed mixed-license REUSE coverage and per-source release-manifest
  licensing, and transitively hash-locked the Python validation environment;
- redesigned the generated network, module, profile, vocabulary, and release
  pages as a restrained standards publication with compact metadata, ruled
  records, accessible term disclosures, responsive layouts, and no decorative
  gradients, shadows, remote fonts, or marketing-style card grid; and
- commit-pinned the GitHub Actions supply chain, checksum-pinned Apache Jena,
  required byte-identical Python 3.11/3.14 builds, verified both release tag
  and target commit signatures, and added durable GitHub Release assets.

## 0.1.0-rc.6 — 2026-08-23

- evaluated HDTO 1.1 as a cited, non-normative requirements source and recorded
  an explicit originality and licensing boundary without importing or copying
  its terms, definitions, axioms, diagrams, or RDF structure;
- added a MODAVIS-native `heritage` module in which heritage recognition is an
  evidence-backed, agent-assigned, time-scoped, supersedable record rather than
  an intrinsic class of an instrument;
- separated curated knowledge collections and immutable knowledge snapshots
  from physical instruments, digital surrogates, virtual instruments, products,
  versions, packages, and snapshot serializations in OWL and SHACL;
- required snapshot assertion membership, named-graph identity,
  canonicalization profile, qualified checksum, creation time, and accountable
  generation activity, with exact retained revision deltas, acyclic revision
  chains, and forward creation chronology;
- added accountable historical-claim review over existing MODAVIS assertions
  while preserving the distinction between object history and PROV-O processing
  lineage; and
- completed the extension with governed recognition statuses, JSON-LD terms,
  examples, negative constraints, competency coverage, catalog and W3ID routes,
  public documentation, and release regression tests.

## 0.1.0-rc.5 — 2026-08-23

- recorded Dominik Ukolov, affiliated with Digital Humanities (Image/Object)
  at Friedrich-Schiller-University Jena, as the named
  domain, ontology-engineering, and implementation reviewer;
- documented the multi-role review as lead-editor self-review, including its
  independence limitation, rather than implying external endorsement;
- prepared a deterministic one-commit public-source snapshot without inherited
  development history or a configured remote;
- added a tag-gated GitHub Pages workflow that reuses the full validation gate,
  requires a repository-authorized annotated signature, rebuilds the final release,
  and deploys only the exact 0.1.0 tag;
- made the validation workflow reusable and candidate/final-version neutral;
- sanitized local filesystem paths and non-public workspace routing from the
  prospective public source inventory; and
- documented the clean Git, signing, hosting, and W3ID handoff procedure.

## 0.1.0-rc.4 — 2026-08-23

- enforced the documented distinction between instrument, state, and
  configuration identities and between virtual instrument, product, version,
  and package identities in both OWL and SHACL;
- introduced a governed competency-question manifest with stable identifiers,
  natural-language questions, explicit required terms, example dependencies,
  and executable coverage for every normative module and the vocabulary;
- assigned stable profile IRIs, labels, messages, and explicit severity to all
  reportable SHACL node, property, logical-alternative, and SPARQL constraints;
- added `rdfs:isDefinedBy` declaration ownership and controlled
  `vs:term_status` lifecycle metadata to every public ontology and vocabulary
  term;
- added HermiT consistency and satisfiability validation for every module and
  the collapsed network import closure to CI;
- expanded ontology-quality regression tests and release documentation for
  identity, constraint, competency, lifecycle, and reasoning practices.

## 0.1.0-rc.3 — 2026-08-23

- completed a fresh ontology-engineering audit across OWL, SKOS, SHACL,
  imports, JSON-LD, examples, competency tests, and release tooling;
- added the controlled-vocabulary ontology to the network import closure and
  completed XML-catalog resolution for the network and vocabulary version IRIs;
- made qualified evidence relations single-target and made closed-profile
  snapshot, bitstream, and parameter-set fixity unambiguous;
- validated the 0.1.0 `has-builder` assertion signature, added identified
  conflict criteria, rejected supersession and derivation cycles, and required
  a projection to name its target graph or include its exact RDF statement;
- aligned MODAVIS agents conservatively with PROV-O agents, accepted the
  `usedSoftware` subproperty as an explicit processing association, and added
  missing identifier, label-language, temporal, organ, and source-type checks;
- corrected MIDI 1.0 note-on selection bounds to 1–127 because velocity zero
  denotes note-off, and clarified the boundary of virtual-instrument products;
- expanded the JSON-LD context and regression fixtures, with pySHACL, Apache
  Jena, and ROBOT independently confirming the revised candidate.

## 0.1.0-rc.2 — 2026-08-23

- corrected digital-asset versus digital-representation identity;
- separated MIDI bindings from protocol-neutral audio semantics;
- renamed evidence support resources to neutral evidence relations;
- completed assertion-projection lineage and consistency constraints;
- made stable HTTP IRIs normative and demoted MDVS v1 to legacy compatibility;
- added an RDF 1.1 assertion-context module following review of the
  multidimensional-KG WIP, while deferring its unresolved Boolean algebra;
- removed the unauditable private-source VAO alignment from public artifacts;
- closed normative seed vocabularies in SHACL, removed implicit RDFS
  entailment, enumerated W3ID vocabulary routes, and hardened release provenance;
- declared borrowed external entities in the local import closure and moved
  `xsd:date`/`rdf:langString` validation to SHACL so ROBOT independently
  confirms the network is in OWL 2 RL;
- removed compact algorithm-less hash properties, required qualified,
  closed-algorithm fixity for snapshots and parameter
  sets, added cross-resource consistency constraints, and removed hollow
  audio/control-profile, envelope, and calibration placeholders from 0.1.0.

## 0.1.0-rc.1 — 2026-08-23

- established the generic instrument, evidence, assertion, event, provenance,
  organ, validation, and vocabulary development modules;
- adopted the common `https://w3id.org/modavis/` identifier architecture;
- separated general IRI identity from the MDVS-managed publication profile;
- clarified instrument state versus configuration and added explicit state
  scope;
- introduced structured selector and qualified checksum foundations;
- prepared governance, citation, W3ID routing, release metadata, and
  prepublication validation;
- recorded the MODAVIS Release 1.3 vocabulary snapshot as a selective release
  dependency, not a blocker for other preparation;
- added representation/media, audio and sampled-playback, and virtual musical
  instrument modules with matching SHACL constraints;
- separated physical source instrument, playable virtual instrument, product,
  version, and distribution package identities;
- adopted exact half-open frame intervals, qualified fixity, source-state
  evidence, representation-status vocabularies, and a virtual pipe-organ
  example;
- separated historical events from their provenance-bearing event records so
  later normalization or ingestion runs cannot be mistaken for the cause of a
  past restoration, relocation, or digitization event;
- recorded a conservative VAO 0.2.2 alignment without importing VAO into the
  MODAVIS ontology network;
- added a JSON-LD context, concrete W3ID rules, versioned multi-serialization
  publication artifacts, a DCAT catalog with SPDX SHA-256 fixity and byte
  sizes, and reproducible release manifests;
- pinned every local import to an immutable 0.1.0 dependency version, allowed
  pipe organs to use qualified memberships without convenience triples, added
  time-order validation and governed compatibility outcomes, and hardened the
  authorization-to-publication transition against stale candidate metadata;
- made SHACL-SPARQL constraints self-contained, assigned profile-owned shape
  IRIs, declared the required RDFS entailment contract, added dereferenceable
  term anchors, enforced checksum-valid canonical MDVS examples, and exercised
  the W3ID rules through behavioral Apache tests.

No public MODAVIS ontology release has been made.
