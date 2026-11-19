# MODAVIS and VAO 0.6.0

[VAO 0.6.0](https://github.com/modavis-project/vao-standard/releases/tag/v0.6.0)
binds to the [MODAVIS Ontology Network 0.1.0](https://w3id.org/modavis/ontology/0.1.0).
MODAVIS supplies terms for instruments, their components, digital representations,
and evidence. VAO defines how to describe a release and exchange its files in one
or more carriers.

## Manifest and RDF mapping

Use this binding in a VAO 0.6.0 manifest:

```json
{
  "modavisBinding": {
    "ontologyIRI": "https://w3id.org/modavis/ontology",
    "ontologyStatus": "released",
    "ontologyVersion": "0.1.0",
    "ontologyVersionIRI": "https://w3id.org/modavis/ontology/0.1.0",
    "mappingVersion": "0.6.0",
    "mappingIRI": "https://w3id.org/modavis/vao/0.6.0/modavis-mapping"
  }
}
```

Use MODAVIS term IRIs where they fit the data. For a pipe organ, use
[`organ:PipeOrgan`](https://w3id.org/modavis/ontology/organ#PipeOrgan).
The organ module also defines
[`organ:OrganKeyboard`](https://w3id.org/modavis/ontology/organ#OrganKeyboard)
and [`organ:OrganStop`](https://w3id.org/modavis/ontology/organ#OrganStop).
The VAO JSON-LD context expands the manifest to RDF.

Load the [VAO-owned mapping](https://w3id.org/modavis/vao/0.6.0/modavis-mapping)
if you want the shared media types in the RDF view. The mapping imports the
VAO 0.6.0 vocabulary and MODAVIS 0.1.0. It adds two subclass statements:

```turtle
@prefix vao: <https://w3id.org/modavis/vao/ontology#> .
@prefix modmedia: <https://w3id.org/modavis/ontology/media#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

vao:LogicalAsset rdfs:subClassOf modmedia:DigitalAsset .
vao:Realization rdfs:subClassOf modmedia:Bitstream .
```

The dependency runs from VAO to MODAVIS. The Network's imports are its own
versioned modules and vocabularies. For an older VAO package, use the mapping
named in its manifest. The [VAO migration guide](https://github.com/modavis-project/vao-standard/blob/v0.6.0/Docs/MIGRATION_0.5_TO_0.6.0.md)
describes how to create a 0.6.0 release from a complete 0.5.0 workspace.

## Mechanical music carriers

[MMIC 1.0.0](https://github.com/modavis-project/vao-standard/blob/v0.6.0/Docs/VAO_MMIC_PROFILE_1.0.0.md)
is an optional VAO profile for rolls, discs, barrels, and other carriers that
encode mechanical music. VAO maintains its
[mechanical-music ontology](https://github.com/modavis-project/vao-standard/blob/v0.6.0/Profiles/MMIC/1.0.0/mechanical-music.ttl)
and [profile files](https://github.com/modavis-project/vao-standard/tree/v0.6.0/Profiles/MMIC/1.0.0).
The MMIC version identifies the profile; 0.6.0 identifies the VAO format.
Use the files from the release tag while the MMIC W3ID routes are unavailable.

## Validation

Use the VAO reference tools to check the manifest, carrier, and any declared
MMIC capabilities. Apply the appropriate MODAVIS SHACL profile separately to
records exchanged as MODAVIS RDF. These checks cover different requirements.
The two subclass statements describe media types and carry no conformance claim.

The [versioned VAO bundle](https://w3id.org/modavis/vao/0.6.0/specification-bundle)
lists the core schemas, context, vocabulary, and mapping. The release files
are available from [GitHub](https://github.com/modavis-project/vao-standard/releases/tag/v0.6.0)
and [Zenodo](https://doi.org/10.5281/zenodo.23287792).
