# MODAVIS Ontology Network

MODAVIS is a modular semantic standard for evidence-backed,
time-aware, and provenance-aware knowledge about musical instruments and their
digital representations. It is instrument-neutral, with pipe organs as a
demanding flagship case rather than the universal model.

**Release:** `0.1.0`, dated 2026-08-27. The accountable maintainer review and
its independence limitation are recorded. Cite the immutable release using
[doi:10.5281/zenodo.22126086](https://doi.org/10.5281/zenodo.22126086).

Canonical identifier root: `https://w3id.org/modavis/`

## Release scope

| Module | Scope |
| --- | --- |
| `core` | identity, entities, agents, places, names, identifiers, and uncertain time |
| `instrument` | musical instruments, states, configurations, components, memberships, and contextual roles |
| `evidence` | sources, fixed snapshots, fragments, selectors, qualified evidence, and checksums |
| `provenance` | conservative PROV-O processing and editorial lineage |
| `assertion` | explicit claims, conflicts, decisions, and projection lineage |
| `events` | documented historical occurrences, distinct from data-processing activities |
| `organ` | pipe-organ specialization over the generic instrument model |
| `media` | representations, digital surrogates, assets, bitstreams, status, fixity, and derivation |
| `audio` | fixed audio signals, half-open frame regions, loops, sampled playback, and tuning |
| `midi` | optional MIDI bindings for protocol-neutral audio and tuning records |
| `context` | explicit contextual applicability of identified assertions, separate from provenance |
| `virtual-instrument` | playable virtual instruments, products, versions, packages, compatibility, and evidence-qualified source relations |
| `heritage` | contextual heritage recognition, governed knowledge collections, fixed snapshots, revision deltas, and historical-claim review |
| `vocab` | reviewed SKOS concepts used by the modules and profiles |

`ontology/modavis-network.ttl` imports the complete normative module set by
immutable 0.1.0 version IRI. VAO does not belong to that import closure: it is
a downstream container and application profile. The final VAO 0.4.0 co-release
binds to MODAVIS 0.1.0 through an exact, VAO-owned mapping; MODAVIS never imports
VAO.

## Identity commitments

- a representation or surrogate is not identical to what it represents;
- a physical source instrument, its time-scoped state, a playable virtual
  instrument, a product, a version, and a package retain separate identities;
- a curated knowledge collection and its fixed snapshots are distinct from
  the documented instrument, a digital surrogate, and a playable virtual
  instrument; MODAVIS does not use “digital twin” as a synonym for any of them;
- product listings and source-similarity candidates do not establish
  instrument identity;
- function is assigned contextually rather than baked into permanent component
  identity;
- assertions and evidence remain available even when accepted facts are
  projected into a convenience graph;
- stable HTTP IRIs are normative identity; legacy MDVS v1 strings are optional
  compatibility data and are not persistent identifiers;
- absence of an assertion-context binding means unknown or unqualified scope,
  never universal validity.

The instrument/state/configuration layers and the playable virtual instrument,
product, version, and package layers are disjoint in OWL and checked in SHACL.
Every public term records its declaration owner and 0.x maturity status; every
reportable SHACL constraint has a stable versioned profile IRI.

See [DESIGN.md](DESIGN.md) for the design rationale and
[the interpretation guide](docs/INTERPRETATION_GUIDE.md) for distinctions that
implementers must preserve. The
[release-readiness evaluation](docs/EVALUATION_AND_RELEASE_READINESS.md)
states the validation scope and remaining external gates.

## Validate and build

Use a virtual environment and run:

```sh
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q
python3 scripts/build_publication_preview.py --check
python3 scripts/check_prepublication.py
python3 scripts/check_w3id.py --require-apache
python3 scripts/build_release_candidate.py --output-directory /path/to/empty/output
```

The candidate builder produces:

- a deployable, versioned static site with HTML, Turtle, JSON-LD, RDF/XML,
  SHACL profiles, JSON-LD context, examples, DCAT catalog, manifest, and
  SHA-256 checksums;
- a deterministic source-and-site ZIP and detached SHA-256 file;
- no tag, deployment, W3ID submission, DOI, or other external mutation.

The versioned SHACL artifacts validate explicit RDF data and declare no
entailment regime. Validators must support SHACL 2017 and SHACL-SPARQL. They
must also load the required versioned ontology network as class-hierarchy
knowledge unless the data graph already contains the needed
`rdfs:subClassOf` statements or explicit superclass types; this does not fill
missing domain statements or otherwise enable general RDFS entailment.

The governed competency-question manifest covers every normative module and
the vocabulary. CI executes each question over its declared examples and runs
HermiT consistency/satisfiability checks separately from the OWL 2 RL profile
gate.

Source snapshots require fixity, a timezone-qualified capture instant, and an
accountable generating activity. Knowledge snapshots bind exact assertion
membership to a single named graph and an exact checksum-fixed canonical
N-Quads bitstream produced under the immutable RDFC-1.0 Recommendation; the
snapshot metadata is outside the canonicalization input to prevent self-hash
ambiguity.

## Release and governance material

- [Release process](docs/RELEASE_PROCESS.md)
- [Interpretation guide](docs/INTERPRETATION_GUIDE.md)
- [Competency questions and traceability](docs/COMPETENCY_QUESTIONS.md)
- [MODAVIS–VAO interoperability](docs/VAO_INTEROPERABILITY.md)
- [Governance](GOVERNANCE.md), [contribution policy](CONTRIBUTING.md), and
  [security policy](SECURITY.md)
- [Release metadata](config/release-metadata.json) and
  [W3ID route registry](config/w3id-routes.json)
- [Concrete W3ID submission rules](w3id/.htaccess)
- [MDVS v1 compatibility boundary](docs/MDVS_V1_COMPATIBILITY.md)

Semantic artifacts and documentation use CC BY 4.0. Release tooling and test
code use Apache-2.0. No affiliated institution is represented as an endorser or
publisher merely through contributor affiliation.
