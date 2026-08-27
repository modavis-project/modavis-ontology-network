# MODAVIS Ontology Design Decisions

Status: design record for release `0.1.0`

> **Documentation classification:** release design record. The published 0.1.0
> ontology graphs and SHACL profiles are the stable machine-
> readable contracts; this file explains their intended interpretation.

## Semantic center

The ontology network models musical-instrument heritage as evidence-backed,
time-aware, provenance-aware knowledge. Pipe organs are the flagship
specialization, not the universal instrument model.

The released ontology and SHACL profiles are the normative public semantic
contract. An operational MODAVIS database may remain a system of record for
application data, but its private schema does not silently define public term
meaning. Implementation, authorization, cache, and workflow tables that have
no public domain meaning are deliberately omitted.

## Module boundaries

| Module | Responsibility |
| --- | --- |
| `core` | Stable identity, entities, continuants, agents, names, identifiers, places, and uncertain time spans |
| `instrument` | Generic instruments, states, configurations, components, qualified membership, and contextual roles |
| `evidence` | Sources, captured snapshots, precise fragments, selectors, and qualified evidence relations |
| `provenance` | Conservative PROV-O profile for processing, editorial, digitization, and release activities |
| `assertion` | Explicit claims, evidence links, conflicts, decisions, and convenience-graph projection lineage |
| `events` | Historical/domain occurrences and activities, separate from the processing activity that records them |
| `organ` | Pipe-organ specialization over the generic instrument model |
| `media` | Representations, digital surrogates, assets, bitstreams, fixity, status, and derivation |
| `audio` | Fixed audio signals, half-open frame regions, loop decisions, sampled playback, and tuning |
| `midi` | Optional MIDI note/velocity bindings layered over protocol-neutral audio records |
| `context` | Explicit assertion applicability dimensions and values, separate from attribution/provenance |
| `virtual-instrument` | Playable virtual instruments, products, versions, packages, compatibility, and qualified source relations |
| `heritage` | Qualified heritage recognition, governed knowledge collections, immutable snapshots, revision deltas, and historical-claim review |
| `vocab` | SKOS classifications used by data and SHACL profiles |

## Identity model

`modavis:IdentifiedResource` is the shared IRI identity root. It allows an
exchange graph to identify domain entities, events, assertions, memberships,
and provenance activities without claiming that MODAVIS has allocated every
identifier. `modavis:MODAVISManagedResource` is the narrower publication class
for resources admitted to a governed MODAVIS public record. Stable HTTP IRIs
are normative; `mdvsIdentifier` is optional legacy v1 compatibility data and
is neither an allocation claim nor a persistent-identifier standard.

`modavis:Entity` covers physical, digital, conceptual, and informational
things. `modavis:Continuant` covers persistent entities capable of changing
state. A musical instrument and its components are continuants. An
`InstrumentState` is a time-scoped entity describing the instrument's
condition; it is neither the instrument itself nor an
`InstrumentConfiguration`. Configurations may apply within a state.
These three identity layers form an OWL all-disjoint set, and the exchange
profile rejects explicit typing through more than one layer. This makes the
identity commitment testable for RDF consumers that do not run an OWL
consistency reasoner.

Public examples use `https://example.org/` IRIs. Production datasets must use
stable, governed HTTP IRIs under their own authority. W3ID is used for MODAVIS
ontology terms, vocabularies, shapes, contexts, and releases.

## Digital and virtual instrument identity

A digital representation does not become the represented instrument by being
high-fidelity, interactive, or playable. `modmedia:representationOf` never
asserts identity or completeness. A `modmedia:DigitalSurrogate` may stand in
for selected aspects of a physical instrument or state.

A playable `modvmi:VirtualMusicalInstrument` is itself a musical instrument. It
may additionally be a digital surrogate, but it remains distinct from:

1. the physical or other source instrument and its time-scoped source state;
2. the stable `VirtualInstrumentProduct` identity;
3. each `VirtualInstrumentVersion`;
4. every downloadable or preservable `VirtualInstrumentPackage`.

The playable instrument, stable product, version, and package classes form a
second OWL all-disjoint set with matching SHACL validation. A playable virtual
instrument may still also be a `DigitalSurrogate`; the disjointness concerns
the four product lifecycle identities, not legitimate media perspectives.

`InstrumentSourceRelation` qualifies sampled-from, modeled-after,
reconstruction, composite-source, and inspiration relations with evidence and
confidence. It deliberately does not use `owl:sameAs`.

Audio regions use zero-based half-open frame intervals (`[start,end)`) bound to
one fixed `AudioSignal`. This eliminates inclusive-end ambiguity and prevents
coordinates from silently surviving resampling or trimming. MIDI note and
velocity numbers live only in the optional `midi` module. Other runtime
formats, plugin formats, and archive paths remain application-profile concerns.

## Heritage recognition and curated knowledge

MODAVIS does not treat heritage significance as an intrinsic property of an
instrument. A `modheritage:HeritageRecognition` records the resource, assigning
agent, citable basis, governed status, validity interval, evidence, and record-
generation activity. Several agents may therefore make concurrent or
conflicting determinations without changing the resource's class identity.

A `modheritage:CuratedKnowledgeCollection` is an evolving, governed body of
assertions. Each publishable state is a distinct `KnowledgeSnapshot` with exact
assertion membership, a named-graph IRI, the immutable RDFC-1.0 profile, one
checksum-fixed canonical N-Quads bitstream, a timezone-qualified creation time,
and a generation activity. The canonical dataset contains only the outgoing
triples of member assertions in the declared graph; snapshot metadata is
excluded, so the digest cannot become self-referential. A maintenance activity
records the complete assertion delta between retained states. An assertion
removed from a later snapshot remains citable in the earlier snapshot.

The following identities are deliberately separate:

```text
documented musical instrument
  != digital representation or surrogate
  != playable virtual musical instrument
  != curated knowledge collection
  != fixed knowledge snapshot
  != snapshot serialization or package
```

No MODAVIS class is named `DigitalTwin`. External projects may map a precisely
defined knowledge-twin concept to `CuratedKnowledgeCollection`, or a simulation
concept to a virtual-instrument or media term, only after checking the external
definition. HDTO informed the competency analysis but is not imported,
redeclared, or treated as a normative dependency.

`HistoricalClaimReview` specializes the existing editorial provenance model.
It consumes assertions about one identified subject and generates a distinct
conclusion assertion with its own evidence and status. “Historical claim” is
used to avoid confusing physical-object origin, attribution, ownership, or
custody questions with PROV-O processing lineage.

## Domain events and provenance

Historical events and processing provenance are intentionally separate:

```text
modevent:Event
  an occurrence in the documented world

modevent:EventRecord
  a provenance-bearing information entity describing that occurrence

modprov:ProcessingActivity / prov:Activity
  a computational or editorial process that captured, normalized, reviewed,
  projected, or released a record or knowledge about that occurrence
```

No equivalence or global disjointness is asserted between domain events and
`prov:Activity`. This avoids conflating roles while leaving room for a real
activity to be described from more than one perspective when justified.

## Components and memberships

`modinst:hasComponent` is a discovery-oriented convenience relation.
`modinst:ComponentMembership` is the scholarly representation when the
relation carries type, time, configuration, evidence, or provenance.

The membership model always identifies the instrument and child component. A
parent component is optional, allowing both instrument-to-component and
component-to-component membership without inventing a synthetic root
component.

## Functional roles

Physical component identity is distinct from function.

`modinst:FunctionalRoleAssignment` qualifies a role assignment. The assigned
role is a governed SKOS concept, such as sound generator, resonator, selector,
playing interface, or action mechanism. Configuration and time may scope the
assignment.

This avoids permanent subclass claims such as “every organ pipe is always a
sound generator” while still supporting cross-instrument queries about
function.

`modevidence:EvidenceRelation` neutrally records that a source fragment
evaluates a resource, with a separate supporting, opposing, or contextual
role. Assertions, events, compatibility statements, and source relations link
to that generic relation through their module-specific evidence properties;
the relation identifies its evaluated resource with `modevidence:evaluates`.

## Assertions and convenience graphs

An assertion explicitly records subject, predicate, exactly one identified-
resource or literal object, status, optional confidence, evidence relation,
provenance, and supersession. Conflicting assertions remain first-class
members of a conflict set, and editorial resolution is a separate accountable
decision.

Assertion predicates are governed SKOS concepts, matching the operational
`types.assertion_predicate` model. They are not OWL properties used as
individual values. A reviewed projection maps an accepted predicate concept
to a native OWL property such as `modinst:hasBuilder`. This preserves OWL 2 DL
discipline and keeps raw scholarly claims separate from convenience triples.

Two data views are intended:

1. the research graph retains assertions, evidence, conflicts, and provenance;
2. the convenience graph projects accepted assertions as direct triples.

Projection lineage records the exact subject, predicate IRI, resource or
literal object, optional graph, rule IRI, rule version, and generating
activity. SHACL requires these values to reproduce the source assertion and
the predicate concept's explicit property-IRI mapping.

## Assertion context

Contextual applicability is attached to an identified assertion through a
`ContextBinding` with exactly one dimension, relation, and identified value.
It is not attribution or provenance. No binding means unknown or unqualified
scope, not universal validity. Multiple bindings have no implicit conjunction
or disjunction semantics; application profiles must define their combination
or use distinct assertions. This conservative RDF 1.1 model incorporates the
sound separation found in the multidimensional-KG WIP without standardizing
its unresolved five-operator algebra.

## OWL and SHACL responsibilities

OWL defines durable semantics and safe inferences. SHACL defines the exchange
and publication profiles: cardinalities, datatype constraints, evidence
requirements, and self-relation checks.

Every public OWL/SKOS term identifies its declaration-owning graph with
`rdfs:isDefinedBy` and carries a controlled `vs:term_status`. The initial 0.x
term set is marked `testing` to communicate semantic maturity without weakening
the rule that public IRIs are never reassigned. Every reportable SHACL node,
property, logical-alternative, and SPARQL constraint has a stable profile IRI,
label, message where it can emit a result, and explicit severity.

The SHACL profiles require the versioned ontology network as their class-
hierarchy graph unless equivalent subclass axioms or explicit superclass types
are already present in the data graph. This follows SHACL 2017 class-target and
`sh:class` semantics without declaring a general entailment regime.

Global domains, ranges, disjointness, and equivalence axioms are used
conservatively. A missing global domain or range avoids an invalid universal
inference; it does not make the property semantically unrestricted. Intended
exchange uses are stated by definitions, scope notes, and SHACL profiles.
Completeness constraints remain in SHACL because OWL uses the open-world
assumption. The public interpretation rules and ambiguity boundaries are
collected in `docs/INTERPRETATION_GUIDE.md`.

## Initial schema-to-ontology interpretation

The mapping is curated rather than mechanical:

| PostgreSQL surface | Ontology interpretation |
| --- | --- |
| `core.entity` | Public identity anchor; normally `modavis:Entity`, or another `IdentifiedResource` class when the record identifies an event-like resource |
| `core.continuant` | `modavis:Continuant` and domain subclasses such as `modinst:MusicalInstrument` |
| `core.manifestation` | Source for instrument-state/configuration projections when the record has that meaning; not automatically an OWL class |
| `core.activity` | `modevent:Event` or `modevent:Activity`; a separate `EventRecord` carries lineage to the `prov:Activity` that generated the record |
| `types.*` | Governed SKOS concepts unless a reviewed semantic case justifies an OWL class |
| `organs.component` | `modinst:InstrumentComponent` plus an organ subclass |
| `organs.component_membership` | `modinst:ComponentMembership` with relationship concept, time, configuration, and assertion links |
| `organs.detail`, `stop`, `rank`, `pipe`, `keyboard`, `coupler`, `accessory` | Organ specializations and properties, linked to generic component identity |
| `assertion.statement` | `modassert:Assertion` with exactly one entity or literal object |
| `assertion.support` | `modevidence:EvidenceRelation` |
| `assertion.conflict_*` | Conflict set and accountable editorial decision resources |
| `assertion.projection` | `modassert:Projection` lineage for accepted convenience triples or domain rows |
| `evidence.source_resource/snapshot/fragment` | Source, captured state, and precise selector-bearing fragment |
| `prov.activity`, `prov.used`, `prov.generated` | PROV-O activities and relations with MODAVIS processing specializations |

Workflow, cache, authorization, monitoring, and staging tables are not public
ontology classes merely because they are present in the database.

## Vocabulary policy

Instrument types, functional roles, membership kinds, statuses, evidence
roles, and event types are SKOS concepts. They are not automatically OWL
classes. A term may be promoted only when it denotes a stable category with
real reasoning value and the promotion is reviewed as a semantic change.

## Resolved and deferred release decisions

- The identifier root is `https://w3id.org/modavis/`; public terms use stable
  unversioned IRIs, each ontology graph has an immutable 0.1.0 version IRI,
  every local import in the release closure is version-pinned, and the network
  directly imports the governed vocabulary ontology as well as every domain
  module.
- The initial release publisher is the named creator identified by ORCID.
  Contributor affiliations do not imply institutional endorsement.
- Semantic artifacts and documentation use CC BY 4.0; code uses Apache-2.0.
- Web Annotation selectors and PROV-O are reused directly and conservatively.
- The exchange and publication SHACL profiles are separate; neither requires
  MDVS allocation and neither declares implicit RDFS entailment.
- Media, reusable audio, virtual-instrument identity, and heritage knowledge
  governance join 0.1.0.
- The Release 1.3 database has no immutable vocabulary-snapshot artifact. The
  ontology records this honestly and makes no nonexistent release pin.
- The final checksum-pinned VAO 0.4.0 co-release owns its conservative mapping
  to MODAVIS 0.1.0. MODAVIS does not import VAO, and the mapping claims only
  universally valid container relationships while VAO examples use exact
  MODAVIS instrument and organ term IRIs directly.
- CIDOC CRM, PON, SOSA/SSN measurement, spatial semantics, and
  interaction-event semantics remain future reviewed alignments or modules.
  Their absence does not change the meaning of the 0.1.0 terms.
- HDTO 1.1 is a cited design input, not a normative dependency. MODAVIS adds no
  HDTO import or equivalence mapping, and its heritage terms are independently
  defined around MODAVIS assertions, evidence, fixity, and identity rules.
- Additional native assertion predicates and R2RML projections remain
  implementation-driven extensions, not prerequisites for namespace freeze.

## Current proof points

- All OWL, SKOS, SHACL, and example Turtle files parse.
- The combined positive examples conform to the combined SHACL profiles.
- Apache Jena independently accepts the valid graph and rejects every checked-
  in invalid fixture; ROBOT reports the version-pinned closure in OWL 2 RL.
- A stable-IRI instrument without MDVS data conforms; malformed retained MDVS
  lexical data fails the compatibility shape.
- The violin example uses the same component, membership, and role model as the
  pipe-organ example.
- Competency queries cover cross-instrument roles, evidence-backed assertions,
  event provenance, source fixity, conflict decisions, contextual scope,
  organ structure, representation and audio lineage, MIDI bindings,
  virtual-instrument source/sample lineage, contextual heritage recognition,
  fixed knowledge revision, historical-claim review, and governed vocabulary
  discovery.
- A machine-readable competency manifest assigns a stable question ID,
  required terms, example inputs, and a non-empty result expectation to every
  executable query and covers every normative module.
- HermiT checks every module and the collapsed network closure for consistency
  and unintended unsatisfiable classes in CI; ROBOT separately verifies OWL 2
  RL profile membership.
- Versioned Turtle, JSON-LD, and RDF/XML distributions, a JSON-LD context,
  DCAT catalog, manifest, checksums, and concrete W3ID rules are generated and
  tested reproducibly.

These prove technical coherence and release completeness within the
stated scope. The named initial-release review, method, and independence
limitation are summarized in `docs/EVALUATION_AND_RELEASE_READINESS.md` and
`config/release-metadata.json`. Neither the technical proof points nor that
review authorize deployment.
