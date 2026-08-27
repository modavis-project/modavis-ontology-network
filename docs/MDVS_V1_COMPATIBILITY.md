# MDVS v1 compatibility boundary

Status: informative compatibility note for MODAVIS 0.1.0

Stable HTTP IRIs are the normative identity mechanism in MODAVIS 0.1.0.
`modavis:mdvsIdentifier` exists only to retain identifiers already present in
Release 1.3 or another governed legacy dataset. It is optional and must not be
used as evidence of global uniqueness, public resolution, or allocation.

The historical v1 lexical form is `MDVS:TYPE:XXXX-XXXX-C`, using a four-letter
type token and Crockford Base32 characters. The publication SHACL profile checks
only that lexical form when the property is present.

## Known limitations

- The eight-character payload provides only 40 bits and has material collision
  risk under distributed or large-scale independent allocation.
- The historical recurrence `checksum = (checksum * 32 + value) mod 32`
  collapses to the last processed symbol. Its final character therefore detects
  neither substitutions nor transpositions in the preceding content.
- There is no public, globally authoritative allocation ledger, resolution
  protocol, type registry, tombstone policy, or federation contract.
- An existing operational database evaluation found legacy invalid identifiers;
  the ontology does not silently normalize or bless them.

Consequently MDVS v1 is not a persistent identifier standard and new independent
allocation is prohibited by this profile. A future identifier version would
need a public authority model, high-entropy allocation, effective error
detection, a durable resolver, lifecycle governance, migration semantics, and
an independently reviewed conformance suite. That work is outside 0.1.0.
