# MODAVIS interpretation guide

This guide resolves recurring ambiguities that are easy to introduce when RDF,
ontology, validation, and domain-language conventions are read as if they were
the same thing. The ontology graphs and versioned SHACL profiles remain the
machine-readable contracts.

## OWL statements are not validation rules

An `rdfs:domain` or `rdfs:range` produces type inferences; it does not reject a
triple. MODAVIS therefore uses global domains and ranges only where the
inference is valid for every intended use. A property without a global domain
or range is not unconstrained: the applicable SHACL profile, term definition,
and scope note determine its exchange use. A consumer that validates data must
load the versioned MODAVIS ontology hierarchy as documented in `README.md`.

## Identity layers must remain separate

- a musical instrument is not its state or configuration;
- a persistent component is not a time-scoped membership or role assignment;
- a represented object is not its representation, digital asset, or bitstream;
- a playable virtual musical instrument is not its product, version, or
  package; and
- a curated knowledge collection is not a fixed snapshot or snapshot
  serialization.

An IRI should identify one thing at one identity layer. Similarity, derivation,
representation, source use, or high fidelity never establishes `owl:sameAs`.

## Qualified records and convenience links

Direct links such as `modinst:hasComponent` are discovery projections. Use
`modinst:ComponentMembership` when structural kind, parent, instrument, time,
state, configuration, evidence, or provenance matters. The subject of
`modinst:hasMembership` may be the membership instrument or its parent
component; it does not by itself reveal which role that subject has. Inspect
the qualified record.

The absence of a parent component means direct membership at the instrument
level. The absence of time, state, or configuration on a membership or role
assignment means that its scope is not further qualified; it must not be read
as proof of eternal, universal, or configuration-independent validity.

## Assertions, evidence, and truth

An assertion records an attributable claim. An evidence relation records how a
source fragment bears on an evaluated resource. A review decision records an
accountable editorial outcome. SHACL conformance shows that these records have
the required structure; it does not prove that a claim, attribution,
measurement, reconstruction, compatibility result, or heritage recognition is
true. Conflicting and superseded assertions remain citable.

Literal-valued assertions and projections intentionally accept RDF literals of
different datatypes and languages. An application profile should narrow the
datatype when comparison or calculation requires it. Raw source wording belongs
in `modassert:rawValue`; it is not a substitute for a typed assertion value.

## Context, time, and applicability

Provenance answers who or what produced a record. `modcontext:ContextBinding`
answers where, when, under which configuration, from which perspective, or
under which other named dimension an assertion applies. Multiple context
bindings have no implicit Boolean combination. The dimension's `valueModel` or
an application profile must define comparison and combination semantics.

No context binding means unknown or unqualified applicability, not universal
applicability. Open or uncertain time boundaries likewise express missing or
bounded knowledge; they do not silently mean infinity or exactness.

## Audio coordinates and digital fixity

An `AudioSignal` supplies a sample-clock coordinate system. An `AudioSample` is
an identified signal prepared for bounded or triggered playback, not merely a
region of a larger signal and not automatically a file. A `SignalRegion` is a
zero-based half-open interval `[startFrame, endFrameExclusive)` bound to one
fixed signal. Resampling, trimming, rechanneling, or otherwise changing that
signal requires a new signal identity and new region bindings.

A `DigitalAsset` is a citable digital object; a `Bitstream` is its exact byte
sequence when byte identity matters. A retrieval URL is a location, not the
asset's persistent identity. Checksums establish fixity for specified bytes,
not authenticity, truth, rights clearance, or semantic equivalence.

`LoopPointSet` groups signal-bound loop regions and playback policy. Class
membership alone does not say whether the grouping is tentative or accepted;
that lifecycle decision must be recorded by the governing workflow or profile.
Target frequency and tuning offset are used only on sampled-playback parameter
records or tuning entries in the release profile.

## Virtual instruments and compatibility

`modvmi:realizesInstrument` is the product-level association between a stable
product identity and a playable instrument. `modvmi:implementsInstrument` is
the version-level association for a particular edition. A product-level link
does not imply that every version implements the same playable instrument.

A compatibility statement reports an evidence-backed result for one version
and one identified target. It is not a certification, a guarantee about future
versions, or a claim about targets that were not evaluated. An `indeterminate`
status means the evidence does not support a positive or negative result.

## Extension and mapping rule

Reuse an existing MODAVIS term only when its definition and inference hold for
every intended instance. Put narrower project rules in a versioned SHACL
profile. Put cross-ontology subclass, subproperty, equivalence, or
transformation claims in a separately owned and versioned mapping graph.
Conservative mappings may be strengthened later after review; an over-broad
released equivalence cannot be repaired without compatibility consequences.
