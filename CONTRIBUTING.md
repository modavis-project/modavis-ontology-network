# Contributing to the MODAVIS Ontology Network

The current release is `0.1.0`. Contributions should be submitted as
reviewable changes with:

1. the problem or competency question;
2. proposed native MODAVIS semantics;
3. examples for organ and non-organ contexts where relevant;
4. OWL, SKOS, SHACL, mapping, and migration consequences;
5. positive and negative tests;
6. provenance and external sources used for the decision;
7. a compatibility classification.

Do not copy third-party ontology text or examples without recording their
license and provenance. Prefer external IRIs and versioned alignment artifacts
over copied definitions. Database tables, workflow state, and implementation
details do not become ontology terms merely because they exist operationally.

Run before review:

```sh
python3 scripts/normalize_term_metadata.py
python3 scripts/normalize_shacl_constraints.py
python3 -m pytest -q
python3 scripts/check_prepublication.py
```

The two normalization commands are idempotent. They assign missing public-term
ownership/lifecycle annotations and stable, documented SHACL constraint IRIs;
review their diffs rather than treating generated metadata as semantic review.

Vocabulary mappings that claim derivation from MODAVIS Release 1.3 require a
reviewed, immutable vocabulary snapshot and artifact manifest. The inspected
baseline contains no such release artifact. Operational terms may be studied,
but matching labels do not establish identity and must not be copied into a
public scheme without semantic and licensing review.
