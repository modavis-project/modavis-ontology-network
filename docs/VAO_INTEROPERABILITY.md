# MODAVIS–VAO 0.4.0 interoperability contract

Status: MODAVIS 0.1.0 release contract; VAO 0.4.0 publication remains pending

MODAVIS target: `0.1.0` via `https://w3id.org/modavis/ontology/0.1.0`

VAO target: `0.4.0` via `https://w3id.org/modavis/vao/0.4.0/`
Review date: 2026-08-27

## Reviewed VAO release

The interoperability contract targets the immutable VAO 0.4.0 specification,
vocabulary, mapping graph, context, and release bundle. After publication, the
signed VAO version tag and release-bundle checksums are the preservation
anchors. MODAVIS does not redistribute VAO artifacts.

## Dependency direction and ownership

MODAVIS is the reusable semantic layer. VAO is a downstream application,
container, and conformance profile. MODAVIS never imports VAO. The VAO-owned
mapping at `https://w3id.org/modavis/vao/0.4.0/modavis-mapping` imports the
immutable MODAVIS network version and the immutable VAO vocabulary.

The namespace ownership is unambiguous:

- MODAVIS owns `https://w3id.org/modavis/ontology/...` terms for instruments,
  evidence, provenance, media, audio, virtual instruments, and heritage;
- VAO owns `https://w3id.org/modavis/vao/ontology#` terms for its manifest
  projection, container records, scientific application records, spatial and
  acoustic models, runtime behavior, and conformance machinery;
- VAO uses exact MODAVIS term IRIs directly where the MODAVIS meaning applies;
  it does not redeclare the MODAVIS audio namespace.

## Verified semantic binding

The final VAO examples bind to:

```text
ontologyIRI        https://w3id.org/modavis/ontology
ontologyVersion    0.1.0
ontologyVersionIRI https://w3id.org/modavis/ontology/0.1.0
mappingVersion     0.4.0
mappingIRI         https://w3id.org/modavis/vao/0.4.0/modavis-mapping
```

The cross-release audit corrected obsolete fixture references as follows:

| Obsolete development IRI | Released MODAVIS 0.1.0 IRI |
| --- | --- |
| `.../ontology/instrument#PipeOrgan` | `https://w3id.org/modavis/ontology/organ#PipeOrgan` |
| `.../ontology/instrument#Manual` | `https://w3id.org/modavis/ontology/organ#OrganKeyboard` |
| `.../ontology/instrument#Stop` | `https://w3id.org/modavis/ontology/organ#OrganStop` |

`https://w3id.org/modavis/ontology/instrument#MusicalInstrument` and
`https://w3id.org/modavis/ontology/instrument#hasComponent` were already
correct. The VAO mapping makes only two universal container claims:
`vao:LogicalAsset rdfs:subClassOf modmedia:DigitalAsset` and
`vao:Realization rdfs:subClassOf modmedia:Bitstream`. Stronger scientific,
spatial, acoustic, playback, or assertion mappings are intentionally omitted
unless their definitions support the inference in every conforming instance.

## How to connect a VAO release

The connection has three independent parts:

1. **Manifest binding.** A conforming VAO 0.4.0 manifest records the exact
   MODAVIS ontology version and VAO-owned mapping in `modavisBinding`. This pins
   semantic provenance but does not make network access necessary for core VAO
   validation.
2. **Direct term use.** VAO JSON-LD data uses MODAVIS class and concept IRIs
   directly when describing instruments, organ components, evidence, or other
   MODAVIS-owned meanings. The VAO context expands those values into RDF.
3. **Optional cross-model inference.** An RDF consumer that wants the shared
   type view loads the MODAVIS 0.1.0 network, the VAO 0.4.0 vocabulary, and
   `https://w3id.org/modavis/vao/0.4.0/modavis-mapping`. The mapping then permits
   the two conservative subclass inferences listed above.

The mapping file is an OWL ontology graph, but VAO as a whole is not a MODAVIS
ontology module. VAO is a file, container, and conformance standard with an RDF
vocabulary. It owns its mapping because the mapping specializes VAO classes;
MODAVIS stays reusable and does not acquire a reverse dependency.

## Validation boundary

VAO JSON Schema and carrier validation and MODAVIS OWL/SHACL validation remain
independent gates. Passing either does not imply the other, and neither proves
the truth, adequacy, representativeness, or rights status of scientific data.
VAO core conformance remains self-contained; the exact MODAVIS binding records
semantic provenance and enables a separately invoked cross-standard RDF/SHACL
validation pass. The OWL mapping does not cause either standard's validation
result to imply the other's.

The two projects may be released on the same date, but publication order must
be atomic in practice: publish and verify MODAVIS 0.1.0 first, then publish VAO
0.4.0 and its mapping, then enable the prepared W3ID routes. VAO release IRIs
remain prepared identifiers until those downstream steps complete.
