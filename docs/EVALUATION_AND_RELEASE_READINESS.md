# MODAVIS Ontology Network 0.1.0 evaluation and release readiness

Evaluation date: 2026-08-27

Evaluated release: `0.1.0`
Decision: scientifically and technically prepared; publication authorized by the release authority

## Review conclusion

The domain, ontology-engineering, and implementation reviews are complete for
0.1.0 with resolved findings. Dominik Ukolov is the accountable reviewer of
record for all three roles. The review was maintainer-directed and supported by
tool-assisted analysis across the complete public source tree, the final VAO
0.4.0 co-release material, and multiple validation engines. This is disclosed
self-review, not independent human peer review or institutional endorsement.

No unresolved scientific or technical blocker is recorded for the stated 0.1.0
scope. Dominik Ukolov authorized the final transition on 2026-08-27. The
reserved Zenodo DOI is `10.5281/zenodo.22126086`; external publication remains
subject to the ordered artifact, hosting, and identifier checks in the release
process.

## Defensibility corrections completed in rc.7

| Risk | Resolution |
| --- | --- |
| time-specific source snapshots lacked capture provenance | every source snapshot now requires fixity, one timezone-qualified capture instant, and one accountable generating activity |
| knowledge-snapshot checksum scope was ambiguous and potentially self-referential | a snapshot now binds one exact `application/n-quads` bitstream fixed by byte size and qualified checksum; snapshot metadata is outside the RDFC input |
| arbitrary canonicalization-profile IRIs were accepted | the release profile requires the immutable dated RDFC-1.0 W3C Recommendation and defines the one-named-graph assertion-record input dataset |
| example snapshot hashes were fabricated placeholders | checked-in canonical N-Quads examples have computed byte sizes and SHA-256 values verified by tests |
| timezone-less `xsd:dateTime` values weakened chronology | normative MODAVIS date-time constraints require `Z` or an explicit numeric offset |
| VAO documentation was based on an obsolete private draft | the contract is re-audited against final VAO 0.4.0 artifacts and immutable release identifiers |
| VAO fixtures referenced nonexistent MODAVIS organ terms | VAO now uses `organ#PipeOrgan`, `organ#OrganKeyboard`, and `organ#OrganStop` and binds to MODAVIS 0.1.0 through a VAO-owned mapping |
| speculative shared W3ID aliases exceeded the VAO contract | the route registry now lists only the concrete prepared 0.4.0 standard, schema, context, profile, vocabulary, mapping, shape, security, and fixity routes |
| mixed licensing was incompletely expressed | REUSE 3.3 maps every source file to CC BY 4.0 or Apache-2.0; the release manifest records both licenses and a license per source artifact |
| dependencies were only directly pinned | the complete Python dependency closure is hash-locked and installed with `--require-hashes` |
| CI supply-chain and reproducibility controls were incomplete | current actions are commit-pinned; Apache Jena uses a reviewed hard-coded SHA-512; Python 3.11 and 3.14 builds must be byte-identical |
| release signing checked only the tag | the publication workflow verifies both the annotated tag and target commit against the repository-authorized SSH signing key |
| CI artifacts were not a durable release | after successful validation, the authorized tag workflow creates or updates a GitHub Release with the ZIP and detached checksum independently of Pages availability |
| final-state checks covered too few documents | the checker rejects stale rc.7 status wording across all current-status documents while allowing historical reports and changelog entries |
| several classes, properties, and concepts shared misleading labels | property and vocabulary labels now expose their grammatical/semantic roles without changing IRIs |
| affiliation wording drifted from the approved form | current citation, author, governance, review, and release metadata use `Digital Humanities (Image/Object), Friedrich-Schiller-University Jena` |

Earlier rc.1–rc.6 corrections remain recorded in `CHANGELOG.md`: identity-layer
separation; neutral evidence semantics; explicit assertion/conflict/projection
lineage; conservative PROV-O reuse; closed controlled vocabularies; stable SHACL
constraint identifiers; term ownership and lifecycle; complete competency
traceability; OWL 2 RL profile validation; HermiT consistency; contextual
heritage recognition; retained knowledge revisions; and explicit deferral of
underspecified external alignments.

## Scientific interpretation boundary

MODAVIS validates semantic structure, explicit provenance, evidence links,
identity distinctions, fixity, and profile completeness. It does not certify
that an attribution, historical claim, measurement, reconstruction, or heritage
recognition is true. Those conclusions remain attributable, citable, revisable,
and subject to qualified domain review.

The initial release deliberately does not standardize generic measurement and
uncertainty, spatial/acoustic models, interaction behavior, or exact CIDOC CRM,
PON, SOSA/SSN, and HDTO mappings. VAO owns its container, spatial, acoustic,
runtime, and application-profile layer. These are explicit scope boundaries,
not hidden dependencies or defects in the terms released by MODAVIS 0.1.0.

## Evidence gates

The release gate covers:

- RDF/Turtle parsing, JSON-LD expansion, SKOS integrity, import closure, OWL
  profile discipline, semantic-regression tests, competency questions,
  meta-SHACL, and positive/negative SHACL fixtures;
- pySHACL and Apache Jena SHACL behavior, ROBOT OWL 2 RL validation, and HermiT
  consistency/satisfiability for every module and the collapsed network;
- reproducible Turtle/JSON-LD/RDF/XML publication artifacts, DCAT catalog,
  release manifest, site checksums, and deterministic source-and-site ZIP;
- REUSE 3.3 compliance, hash-locked Python dependencies, W3ID behavioral tests,
  CFF validation, final-state guards, signed-commit/tag controls, and byte
  equality across Python 3.11 and 3.14; and
- exact VAO 0.4.0/MODAVIS 0.1.0 term and mapping compatibility without a
  reverse MODAVIS import.

Every generated archive carries a machine-readable source and fixity manifest.
The public tests reproduce the structural validation claims; detailed working
notes and non-public input assessments are not part of the distribution.
The final metadata transition is authorized. The external publication sequence
must still follow `RELEASE_PROCESS.md` so that the signed tag, hosted bytes,
GitHub Release assets, Zenodo deposit, and W3ID targets remain identical and
verifiable.
