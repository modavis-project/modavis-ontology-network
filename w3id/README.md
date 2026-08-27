# MODAVIS W3ID submission directory

The concrete `.htaccess` is ready for local redirect testing and a pull request
to the `w3id.org` registry. Submit it only after all destination files have
been deployed and checked over HTTPS.

The common identifier root is:

```text
https://w3id.org/modavis/
```

The first submission covers the MODAVIS Ontology Network, vocabularies, shapes,
JSON-LD context, and release catalog through this directory's `.htaccess`.
The sibling child directory `modavis/vao/` is prepared and governed by the VAO
repository, not by these ontology redirect rules. Its immutable 0.4.0 mapping
is VAO-owned and binds downstream to MODAVIS 0.1.0; do not enable that child
route until both signed releases and their destination bytes exist. The parent
rules intentionally leave the `vao/` path available for that separately
reviewed child directory.

HDTO informed the design analysis for the MODAVIS `heritage` module. No HDTO
namespace, RDF graph, copied definition, import, equivalence mapping, or
redirect is included in this submission.

Maintainer and contact metadata:

- Dominik Ukolov — <https://orcid.org/0000-0002-7904-3892>
- MODAVIS Project — <https://github.com/modavis-project>

The named multi-role review is recorded with its self-review limitation and the
final 0.1.0 transition is authorized. Deploy the final site at
`https://modavis-project.github.io/modavis-ontology-network`, run the redirect tests
against local Apache and the deployed HTTPS targets, then copy this directory
into a fork of the W3ID registry. Do not submit rules before the durable
versioned targets are available.
