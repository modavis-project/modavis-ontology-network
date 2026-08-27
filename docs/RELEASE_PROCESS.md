# MODAVIS release process

This process applies to every public MODAVIS Ontology Network release. The
release authority remains responsible for deciding whether a prepared release
may be published.

## Prepare

1. Classify every term change as editorial, backward compatible, deprecating,
   or breaking under `GOVERNANCE.md`.
2. Update definitions, scope notes, examples, competency questions, SHACL
   constraints, documentation, `CHANGELOG.md`, `VERSION`, citation metadata,
   and release metadata together.
3. Pin every normative import and external release dependency to an immutable
   version IRI. Keep experimental alignments in a separately versioned mapping
   graph.
4. Record the named reviewers, scope, outcome, resolved findings, and whether
   the review is independent of the lead editor.

## Verify

Run the complete local gate:

```sh
python3 -m pip install --require-hashes -r requirements-dev.txt
python3 -m pytest -q
python3 scripts/build_publication_preview.py --check
python3 scripts/check_prepublication.py
python3 scripts/check_w3id.py --require-apache
python3 scripts/build_release_candidate.py --output-directory /path/to/empty/output
```

CI repeats the checks with the supported Python versions and verifies that the
archives are byte-identical. Review the generated site, manifest, catalog,
checksums, archive contents, and W3ID targets before authorization.

## Authorize and publish

1. Record release authorization, the publication date, and final version in
   `config/release-metadata.json`, `VERSION`, `CITATION.cff`, current-status
   documentation, and the ontology metadata.
2. Run the strict publication gate:

   ```sh
   python3 scripts/check_prepublication.py --publication-ready
   ```

3. Commit the exact release tree, create a signed annotated version tag, and
   verify both objects before publishing artifacts.
4. Publish the GitHub release and Pages site, verify the deployed bytes, and
   only then submit or enable W3ID redirects.
5. Record the immutable tag, release archive digest, and any DOI in the release
   notes. Never replace bytes behind an immutable version IRI.

The builder and checkers do not push, tag, deploy, submit W3ID rules, or mint a
DOI. A failed gate or unresolved approval stops publication.
