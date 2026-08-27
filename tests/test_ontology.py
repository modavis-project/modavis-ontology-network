import json
import hashlib
from html.parser import HTMLParser
import importlib
from pathlib import Path
import re
import subprocess
import sys
import zipfile

import pytest
from owlrl import DeductiveClosure, OWLRL_Semantics, RDFS_Semantics
from pyshacl import validate
from rdflib import DCTERMS, OWL, RDF, RDFS, Dataset, Graph, Namespace, URIRef
from rdflib.compare import isomorphic
from rdflib.plugins.sparql import prepareQuery


ROOT = Path(__file__).resolve().parents[1]
MODAVIS_ROOT = "https://w3id.org/modavis/"
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
VS = Namespace("http://www.w3.org/2003/06/sw-vocab-status/ns#")
MODVMI = Namespace("https://w3id.org/modavis/ontology/virtual-instrument#")
MODINST = Namespace("https://w3id.org/modavis/ontology/instrument#")
MODMEDIA = Namespace("https://w3id.org/modavis/ontology/media#")
MODHERITAGE = Namespace("https://w3id.org/modavis/ontology/heritage#")
MODEVIDENCE = Namespace("https://w3id.org/modavis/ontology/evidence#")
MODAUDIO = Namespace("https://w3id.org/modavis/ontology/audio#")
MODASSERT = Namespace("https://w3id.org/modavis/ontology/assertion#")
MODCONTEXT = Namespace("https://w3id.org/modavis/ontology/context#")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
SPDX = Namespace("http://spdx.org/rdf/terms#")
SH = Namespace("http://www.w3.org/ns/shacl#")


def _graph(paths):
    graph = Graph()
    for path in sorted(paths):
        graph.parse(path, format="turtle")
    return graph


def ontology_graph():
    return _graph([*ROOT.glob("ontology/*.ttl"), *ROOT.glob("vocab/*.ttl")])


def shapes_graph():
    return _graph(ROOT.glob("shapes/*.ttl"))


def exchange_shapes_graph():
    return _graph(
        path for path in ROOT.glob("shapes/*.ttl")
        if path.name != "modavis-publication.shacl.ttl"
    )


def valid_examples_graph():
    return _graph(ROOT.glob("examples/valid/*.ttl"))


def test_all_turtle_artifacts_parse():
    paths = [
        *ROOT.glob("ontology/*.ttl"),
        *ROOT.glob("vocab/*.ttl"),
        *ROOT.glob("shapes/*.ttl"),
        *ROOT.glob("examples/**/*.ttl"),
    ]
    assert paths
    for path in paths:
        assert len(Graph().parse(path, format="turtle")) > 0, path


def test_ambiguity_prone_terms_have_explicit_scope_notes():
    graph = ontology_graph()
    terms = {
        MODINST.InstrumentConfiguration,
        MODINST.ComponentMembership,
        MODINST.FunctionalRoleAssignment,
        MODINST.hasConfiguration,
        MODINST.hasMembership,
        MODAUDIO.AudioSample,
        MODAUDIO.LoopPointSet,
        MODAUDIO.appliesToSignal,
        MODAUDIO.hasSignalRegion,
        MODAUDIO.usesPlaybackParameters,
        MODAUDIO.hasTuningMap,
        MODAUDIO.targetFrequencyHz,
        MODAUDIO.tuningOffsetCents,
        MODASSERT.assertsLiteral,
        MODASSERT.projectionLiteral,
        MODASSERT.projectionRule,
        MODCONTEXT.contextValue,
        MODMEDIA.conformsToProfile,
        MODVMI.CompatibilityStatement,
        MODVMI.realizesInstrument,
        MODVMI.implementsInstrument,
        MODVMI.compatibilityStatus,
        MODVMI.sourceRelationSubject,
    }
    assert all(graph.value(term, SKOS.scopeNote) for term in terms)


def test_every_open_signature_modavis_property_explains_the_omission():
    graph = ontology_graph()
    properties = {
        term
        for property_type in (OWL.ObjectProperty, OWL.DatatypeProperty)
        for term in graph.subjects(RDF.type, property_type)
        if str(term).startswith(f"{MODAVIS_ROOT}ontology/")
    }
    unexplained = {
        term
        for term in properties
        if (
            graph.value(term, RDFS.domain) is None
            or graph.value(term, RDFS.range) is None
        )
        and graph.value(term, SKOS.scopeNote) is None
    }
    assert not unexplained


def test_public_source_excludes_internal_working_records_and_personal_contact_data():
    assert not (ROOT / "AGENTS.md").exists()
    assert not (ROOT / "reports").exists()
    prohibited = (
        "dominik.ukolov" + "@gmail.com",
        "OpenAI" + " Codex",
        "/Users/" + "dominik/",
        "https://github.com/modavis-project/" + "modavis-ontology\"",
        "https://modavis-project.github.io/" + "modavis-ontology/",
    )
    source_paths = [
        path for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and ".venv" not in path.parts
        and ".pytest_cache" not in path.parts
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".zip"}
    ]
    for path in source_paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert not any(token in text for token in prohibited), path.relative_to(ROOT)


def test_every_shacl_sparql_constraint_is_self_contained_and_parseable():
    graph = shapes_graph()
    queries = list(graph.objects(None, SH.select))
    assert queries
    for query in queries:
        prepareQuery(str(query))


def test_shape_graphs_conform_to_meta_shacl():
    for graph in (exchange_shapes_graph(), shapes_graph()):
        conforms, _, report_text = validate(graph, meta_shacl=True, advanced=True)
        assert conforms, report_text


def test_named_shapes_resolve_to_the_profile_that_defines_them():
    exchange_namespace = "https://w3id.org/modavis/shapes/exchange/0.1.0#"
    publication_namespace = "https://w3id.org/modavis/shapes/publication/0.1.0#"
    owners = {}
    for path in sorted(ROOT.glob("shapes/*.ttl")):
        graph = Graph().parse(path, format="turtle")
        shapes = set(graph.subjects(RDF.type, SH.NodeShape))
        assert shapes, path
        expected = publication_namespace if path.name == "modavis-publication.shacl.ttl" else exchange_namespace
        assert all(str(shape).startswith(expected) for shape in shapes), path
        for shape in shapes:
            owners.setdefault(shape, set()).add(path.name)
    assert not {shape: paths for shape, paths in owners.items() if len(paths) > 1}


def test_reportable_shacl_constraints_have_stable_documented_identifiers():
    graph = shapes_graph()
    node_shapes = set(graph.subjects(RDF.type, SH.NodeShape))
    property_shapes = set(graph.objects(None, SH.property))
    sparql_constraints = set(graph.objects(None, SH.sparql))
    assert node_shapes and property_shapes and sparql_constraints

    logical_members = set()
    for predicate in (SH["or"], SH.xone, SH["and"]):
        for head in graph.objects(None, predicate):
            logical_members.update(graph.items(head))

    reportable = node_shapes | property_shapes | sparql_constraints | logical_members
    assert all(isinstance(constraint, URIRef) for constraint in reportable)
    assert all(str(constraint).startswith(f"{MODAVIS_ROOT}shapes/") for constraint in reportable)
    assert all(graph.value(constraint, RDFS.label) for constraint in reportable)
    assert all(graph.value(constraint, SH.name) for constraint in reportable)
    assert all(graph.value(constraint, SH.severity) for constraint in reportable)
    assert all(graph.value(constraint, SH.message) for constraint in property_shapes)
    assert all(graph.value(constraint, SH.message) for constraint in sparql_constraints)
    assert all((constraint, RDF.type, SH.PropertyShape) in graph for constraint in property_shapes)
    assert logical_members.issubset(node_shapes)


def test_ontology_metadata_and_public_term_documentation():
    graph = ontology_graph()
    release_metadata = json.loads((ROOT / "config/release-metadata.json").read_text(encoding="utf-8"))
    license_approved = release_metadata["licenses"]["semanticArtifactsAndDocumentation"]["approved"]
    ontologies = set(graph.subjects(RDF.type, OWL.Ontology))
    assert ontologies
    for ontology in ontologies:
        assert str(ontology).startswith(MODAVIS_ROOT)
        assert graph.value(ontology, DCTERMS.title)
        assert graph.value(ontology, DCTERMS.creator)
        assert graph.value(ontology, DCTERMS.publisher)
        assert graph.value(ontology, DCTERMS.issued)
        assert str(graph.value(ontology, DCTERMS.modified)) == "2026-08-27"
        assert bool(graph.value(ontology, DCTERMS.license)) is license_approved
        assert str(graph.value(ontology, OWL.versionInfo)) == "0.1.0"
        assert graph.value(ontology, DCTERMS.conformsTo)
        assert graph.value(ontology, OWL.versionIRI) == URIRef(f"{ontology}/0.1.0")

    public_types = {
        OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty,
        SKOS.ConceptScheme, SKOS.Concept,
    }
    for resource_type in public_types:
        for resource in graph.subjects(RDF.type, resource_type):
            if str(resource).startswith(MODAVIS_ROOT):
                assert graph.value(resource, RDFS.label) or graph.value(resource, SKOS.prefLabel), resource
                assert graph.value(resource, SKOS.definition), resource


def test_initial_release_review_is_complete_and_self_review_is_disclosed():
    metadata = json.loads((ROOT / "config/release-metadata.json").read_text(encoding="utf-8"))
    policy = metadata["reviewPolicy"]
    assert policy["independentReviewRequiredForInitialRelease"] is False
    assert policy["independentReviewRecommended"] is True
    assert policy["selfReviewLimitationDisclosed"] is True
    assert policy["rationale"]
    for role in ("domain", "ontologyEngineering", "implementation"):
        reviews = metadata["requiredReviews"][role]
        assert len(reviews) == 1
        review = reviews[0]
        assert review["name"] == "Dominik Ukolov"
        assert review["orcid"] == "https://orcid.org/0000-0002-7904-3892"
        assert review["reviewedCandidate"] == "0.1.0-rc.7"
        assert review["outcome"] == "approved-with-resolved-findings"
        assert review["findingsResolved"] is True
        assert review["independentOfLeadEditor"] is False
        assert review["independenceLimitation"]
        assert review["expertise"]


def test_final_prepublication_state_is_authorized_and_ready():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_prepublication.py"), "--publication-ready"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["errors"] == []
    assert payload["blockers"] == []
    assert payload["publicationReady"] is True


def test_every_public_term_has_one_declaration_owner_and_controlled_lifecycle_status():
    public_types = {
        OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty,
        SKOS.ConceptScheme, SKOS.Concept,
    }
    allowed_statuses = {"testing", "stable", "unstable", "deprecated"}
    paths = [*ROOT.glob("ontology/*.ttl"), *ROOT.glob("vocab/*.ttl")]
    for path in paths:
        graph = Graph().parse(path, format="turtle")
        ontologies = list(graph.subjects(RDF.type, OWL.Ontology))
        assert len(ontologies) == 1, path
        owner = ontologies[0]
        for resource_type in public_types:
            for resource in graph.subjects(RDF.type, resource_type):
                if not str(resource).startswith(MODAVIS_ROOT):
                    continue
                assert list(graph.objects(resource, RDFS.isDefinedBy)) == [owner], resource
                statuses = [str(status) for status in graph.objects(resource, VS.term_status)]
                assert len(statuses) == 1, resource
                assert statuses[0] in allowed_statuses, resource


def test_skos_concepts_have_scheme_and_preferred_label():
    graph = ontology_graph()
    concepts = set(graph.subjects(RDF.type, SKOS.Concept))
    assert concepts
    for concept in concepts:
        assert graph.value(concept, SKOS.inScheme), concept
        assert graph.value(concept, SKOS.prefLabel), concept


def test_skos_preferred_labels_and_notations_are_unique_within_scheme():
    graph = ontology_graph()
    for concept in set(graph.subjects(RDF.type, SKOS.Concept)):
        labels_by_language = {}
        for label in graph.objects(concept, SKOS.prefLabel):
            labels_by_language.setdefault(label.language, []).append(str(label))
        assert all(len(labels) == 1 for labels in labels_by_language.values()), concept
    seen = {}
    for concept in set(graph.subjects(RDF.type, SKOS.Concept)):
        scheme = graph.value(concept, SKOS.inScheme)
        for notation in graph.objects(concept, SKOS.notation):
            key = (scheme, str(notation))
            assert key not in seen, (seen.get(key), concept, notation)
            seen[key] = concept


def test_public_human_labels_are_globally_unambiguous():
    graph = ontology_graph()
    declaration_types = {
        OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty,
        SKOS.ConceptScheme, SKOS.Concept,
    }
    owners = {}
    for declaration_type in declaration_types:
        for resource in graph.subjects(RDF.type, declaration_type):
            if not str(resource).startswith(MODAVIS_ROOT):
                continue
            for predicate in (RDFS.label, SKOS.prefLabel):
                for label in graph.objects(resource, predicate):
                    key = (str(label).casefold(), label.language)
                    owners.setdefault(key, set()).add(resource)
    duplicates = {
        key: sorted(map(str, resources))
        for key, resources in owners.items()
        if len(resources) > 1
    }
    assert not duplicates


def test_owl_classes_and_skos_concepts_are_not_conflated():
    graph = ontology_graph()
    classes = set(graph.subjects(RDF.type, OWL.Class))
    concepts = set(graph.subjects(RDF.type, SKOS.Concept))
    assert not classes.intersection(concepts)


def test_local_import_graph_is_closed_and_acyclic():
    graph = ontology_graph()
    ontologies = set(graph.subjects(RDF.type, OWL.Ontology))
    import_identifier_owner = {ontology: ontology for ontology in ontologies}
    for ontology in ontologies:
        version_iri = graph.value(ontology, OWL.versionIRI)
        assert version_iri
        import_identifier_owner[version_iri] = ontology
    local_imports = {
        ontology: {
            import_identifier_owner[imported]
            for imported in graph.objects(ontology, OWL.imports)
            if str(imported).startswith(MODAVIS_ROOT) and imported in import_identifier_owner
        }
        for ontology in ontologies
    }
    unresolved = {
        imported
        for ontology in ontologies
        for imported in graph.objects(ontology, OWL.imports)
        if str(imported).startswith(MODAVIS_ROOT) and imported not in import_identifier_owner
    }
    assert not unresolved

    visiting = set()
    visited = set()

    def visit(node):
        assert node not in visiting, f"cyclic ontology import at {node}"
        if node in visited:
            return
        visiting.add(node)
        for dependency in local_imports.get(node, set()):
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for ontology in ontologies:
        visit(ontology)


def test_ci_runs_dl_reasoning_per_module_and_for_collapsed_network_closure():
    workflow = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    assert "for MODAVIS_ONTOLOGY_FILE in ontology/*.ttl vocab/*.ttl" in workflow
    assert "--reasoner HermiT" in workflow
    assert "--dump-unsatisfiable" in workflow
    assert "--collapse-import-closure true" in workflow


def test_release_workflows_are_reusable_version_neutral_and_tag_gated():
    validation = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    publication = (ROOT / ".github/workflows/publish.yml").read_text(encoding="utf-8")
    assert "workflow_call:" in validation
    assert "MODAVIS_PACKAGE_VERSION" in validation
    assert "0.1.0-rc.7.zip" not in validation
    assert 'python: ["3.11", "3.14"]' in validation
    assert "cross-python-reproducibility:" in validation
    assert "--require-hashes -r requirements-dev.txt" in validation
    assert "6aa4bb8eeb41c0d05c30f3c91a7eb065" in validation
    assert 'tags:\n      - "0.1.0"' in publication
    assert "workflow_dispatch:" in publication
    assert "uses: ./.github/workflows/validate.yml" in publication
    assert "gpg.ssh.allowedSignersFile" in publication
    assert "verify-tag refs/tags/0.1.0" in publication
    assert "verify-commit" in publication
    assert "github.event.repository.visibility == 'public'" in publication
    assert "check_prepublication.py --publication-ready" in publication
    assert "actions/deploy-pages@" in publication


def test_network_imports_complete_version_pinned_release_set_but_never_vao():
    graph = ontology_graph()
    network = URIRef("https://w3id.org/modavis/ontology")
    imports = {str(value) for value in graph.objects(network, OWL.imports)}
    expected = {
        f"{MODAVIS_ROOT}ontology/{module}/0.1.0"
        for module in (
            "core", "instrument", "evidence", "provenance", "assertion",
            "events", "organ", "media", "audio", "midi", "context", "virtual-instrument",
            "heritage",
        )
    }
    expected.add(f"{MODAVIS_ROOT}vocab/0.1.0")
    assert imports == expected
    assert not any("/vao/" in imported for imported in imports)


def test_every_local_import_is_an_immutable_version_iri():
    graph = ontology_graph()
    version_iris = set(graph.objects(None, OWL.versionIRI))
    local_imports = {
        imported
        for imported in graph.objects(None, OWL.imports)
        if str(imported).startswith(MODAVIS_ROOT)
    }
    assert local_imports
    assert local_imports.issubset(version_iris)


def test_catalog_resolves_every_local_version_iri():
    graph = ontology_graph()
    catalog = (ROOT / "catalog-v001.xml").read_text(encoding="utf-8")
    for version_iri in set(graph.objects(None, OWL.versionIRI)):
        assert f'name="{version_iri}"' in catalog, version_iri


def test_public_terms_have_one_declaration_owner():
    declaration_types = {
        OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty,
        SKOS.ConceptScheme, SKOS.Concept,
    }
    owners = {}
    for path in sorted([*ROOT.glob("ontology/*.ttl"), *ROOT.glob("vocab/*.ttl")]):
        graph = Graph().parse(path, format="turtle")
        for resource_type in declaration_types:
            for resource in graph.subjects(RDF.type, resource_type):
                if str(resource).startswith(MODAVIS_ROOT):
                    owners.setdefault(resource, set()).add(path.name)
    duplicates = {str(term): sorted(paths) for term, paths in owners.items() if len(paths) != 1}
    assert not duplicates


def test_owl_rl_closure_does_not_infer_named_resource_as_nothing():
    graph = ontology_graph()
    DeductiveClosure(OWLRL_Semantics).expand(graph)
    named_resources = {
        resource for resource in graph.subjects(RDF.type, None)
        if str(resource).startswith(MODAVIS_ROOT)
    }
    assert not any((resource, RDF.type, OWL.Nothing) in graph for resource in named_resources)


def test_formal_artifacts_do_not_use_the_legacy_draft_ontology_namespace():
    paths = [
        *ROOT.glob("ontology/*.ttl"),
        *ROOT.glob("vocab/*.ttl"),
        *ROOT.glob("shapes/*.ttl"),
        *ROOT.glob("examples/**/*.ttl"),
    ]
    for path in paths:
        assert "https://modavis.org/ontology/" not in path.read_text(encoding="utf-8"), path


def test_non_organ_example_uses_only_generic_instrument_semantics():
    text = (ROOT / "examples/valid/violin.ttl").read_text(encoding="utf-8")
    assert "https://w3id.org/modavis/ontology/instrument#" in text
    assert "https://w3id.org/modavis/ontology/organ#" not in text


def test_positive_examples_conform_to_release_shapes():
    conforms, _, report_text = validate(
        valid_examples_graph(),
        shacl_graph=shapes_graph(),
        ont_graph=ontology_graph(),
        inference=None,
        advanced=True,
    )
    assert conforms, report_text


def test_stable_iri_publication_resource_does_not_require_mdvs():
    data = Graph().parse(ROOT / "examples/valid/instrument-stable-http-iri-no-mdvs.ttl", format="turtle")
    conforms, _, report_text = validate(
        data,
        shacl_graph=shapes_graph(),
        ont_graph=ontology_graph(),
        inference=None,
        advanced=True,
    )
    assert conforms, report_text


@pytest.mark.parametrize(
    ("fixture", "message"),
    [
        ("audio-region-invalid-interval.ttl", "exclusive end frame must be greater"),
        ("checksum-invalid-sha256.ttl", "checksum declared as sha-256"),
        ("instrument-invalid-identifier.ttl", "historical lexical form"),
        ("self-representation.ttl", "cannot contain a cycle"),
        ("time-span-invalid-order.ttl", "start date cannot be later"),
        ("knowledge-identity-collapse.ttl", "cannot also be a musical instrument"),
        ("knowledge-maintenance-invalid-delta.ttl", "must exactly match the difference"),
    ],
)
def test_semantic_negative_fixtures_are_rejected(fixture, message):
    data = Graph().parse(ROOT / "examples" / "invalid" / fixture, format="turtle")
    conforms, _, report_text = validate(
        data,
        shacl_graph=shapes_graph(),
        ont_graph=ontology_graph(),
        inference=None,
        advanced=True,
    )
    assert not conforms, report_text
    assert message in report_text.lower()


def test_exchange_profile_accepts_stable_non_mdvs_iris():
    data = Graph().parse(
        data="""
            @prefix modinst: <https://w3id.org/modavis/ontology/instrument#> .
            @prefix insttype: <https://w3id.org/modavis/vocab/instrument-type/> .
            <urn:uuid:00000000-0000-4000-8000-000000000001>
                a modinst:MusicalInstrument ;
                modinst:instrumentType insttype:violin .
        """,
        format="turtle",
    )
    conforms, _, report_text = validate(
        data,
        shacl_graph=exchange_shapes_graph(),
        ont_graph=ontology_graph(),
        inference=None,
        advanced=True,
    )
    assert conforms, report_text


def test_normal_examples_do_not_mint_or_claim_legacy_mdvs_identifiers():
    graph = valid_examples_graph()
    values = list(graph.objects(None, URIRef(f"{MODAVIS_ROOT}ontology/core#mdvsIdentifier")))
    assert not values
    note = (ROOT / "docs" / "MDVS_V1_COMPATIBILITY.md").read_text(encoding="utf-8").lower()
    assert "not a persistent identifier standard" in note
    assert "collapses to the last processed symbol" in note


def test_pipe_organ_may_use_qualified_membership_without_convenience_component_triple():
    data = Graph().parse(
        data="""
            @prefix modinst: <https://w3id.org/modavis/ontology/instrument#> .
            @prefix modorgan: <https://w3id.org/modavis/ontology/organ#> .
            @prefix insttype: <https://w3id.org/modavis/vocab/instrument-type/> .
            @prefix membership: <https://w3id.org/modavis/vocab/component-membership-type/> .
            <https://example.org/organ> a modorgan:PipeOrgan ;
                modinst:instrumentType insttype:pipe-organ ;
                modinst:hasMembership <https://example.org/membership> .
            <https://example.org/pipe> a modorgan:OrganPipe .
            <https://example.org/membership> a modinst:ComponentMembership ;
                modinst:membershipInstrument <https://example.org/organ> ;
                modinst:childComponent <https://example.org/pipe> ;
                modinst:membershipType membership:structural-part .
        """,
        format="turtle",
    )
    conforms, _, report_text = validate(
        data,
        shacl_graph=exchange_shapes_graph(),
        ont_graph=ontology_graph(),
        inference=None,
        advanced=True,
    )
    assert conforms, report_text


def test_competency_queries_return_results():
    graph = ontology_graph()
    graph += valid_examples_graph()
    DeductiveClosure(RDFS_Semantics).expand(graph)
    for query_path in sorted(ROOT.glob("tests/competency/*.rq")):
        results = list(graph.query(query_path.read_text(encoding="utf-8")))
        assert results, query_path


def _query_iris(text):
    prefixes = dict(re.findall(r"PREFIX\s+([A-Za-z][\w-]*):\s*<([^>]+)>", text, re.IGNORECASE))
    iris = {URIRef(value) for value in re.findall(r"<([^>]+)>", text)}
    for prefix, local_name in re.findall(r"\b([A-Za-z][\w-]*):([A-Za-z_][\w.-]*)", text):
        if prefix in prefixes:
            iris.add(URIRef(prefixes[prefix] + local_name))
    return iris


def test_competency_question_manifest_is_complete_traceable_and_executable():
    manifest = json.loads((ROOT / "config/competency-questions.json").read_text(encoding="utf-8"))
    questions = manifest["questions"]
    assert manifest["schemaVersion"] == 1
    assert questions

    identifiers = [question["id"] for question in questions]
    query_paths = [question["query"] for question in questions]
    assert len(identifiers) == len(set(identifiers))
    assert len(query_paths) == len(set(query_paths))
    assert all(re.fullmatch(r"CQ-[A-Z]+-[0-9]{2}", identifier) for identifier in identifiers)
    assert {ROOT / path for path in query_paths} == set(ROOT.glob("tests/competency/*.rq"))

    normative_modules = {
        path.stem.removeprefix("modavis-")
        for path in ROOT.glob("ontology/modavis-*.ttl")
        if path.name != "modavis-network.ttl"
    } | {"vocab"}
    covered_modules = {module for question in questions for module in question["modules"]}
    assert normative_modules == covered_modules

    ontology = ontology_graph()
    declaration_types = {
        OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty,
        SKOS.ConceptScheme, SKOS.Concept,
    }
    public_terms = {
        term
        for declaration_type in declaration_types
        for term in ontology.subjects(RDF.type, declaration_type)
        if str(term).startswith(MODAVIS_ROOT)
    }

    for question in questions:
        assert question["question"].endswith("?")
        assert question["expectation"]
        query_path = ROOT / question["query"]
        query_text = query_path.read_text(encoding="utf-8")
        query_iris = _query_iris(query_text)
        required_terms = {URIRef(value) for value in question["requiredTerms"]}
        assert required_terms
        assert required_terms.issubset(public_terms), question["id"]
        assert required_terms.issubset(query_iris), question["id"]

        example_paths = [ROOT / path for path in question["examples"]]
        assert all(path.is_file() for path in example_paths)
        graph = ontology_graph()
        graph += _graph(example_paths)
        DeductiveClosure(RDFS_Semantics).expand(graph)
        assert list(graph.query(query_text)), question["id"]


def test_virtual_instrument_identity_layers_are_not_collapsed():
    graph = ontology_graph()
    assert (MODVMI.VirtualMusicalInstrument, RDFS.subClassOf, MODINST.MusicalInstrument) in graph
    assert (MODVMI.VirtualInstrumentPackage, RDFS.subClassOf, MODMEDIA.DigitalAsset) in graph
    assert (MODVMI.VirtualInstrumentProduct, RDFS.subClassOf, MODINST.MusicalInstrument) not in graph
    assert (MODVMI.VirtualInstrumentVersion, RDFS.subClassOf, MODINST.MusicalInstrument) not in graph
    assert (MODVMI.hasCompatibilityStatement, OWL.inverseOf, MODVMI.compatibilityVersion) in graph
    assert (MODVMI.hasSourceRelation, OWL.inverseOf, MODVMI.sourceRelationSubject) in graph
    assert not list(graph.triples((None, OWL.sameAs, None)))


def test_heritage_module_preserves_contextual_status_and_knowledge_identity():
    graph = ontology_graph()
    assert (MODHERITAGE.HeritageRecognition, RDFS.subClassOf, URIRef(f"{MODAVIS_ROOT}ontology/core#IdentifiedResource")) in graph
    assert (MODHERITAGE.CuratedKnowledgeCollection, OWL.disjointWith, MODINST.MusicalInstrument) in graph
    assert (MODHERITAGE.KnowledgeSnapshot, OWL.disjointWith, MODMEDIA.DigitalSurrogate) in graph
    assert not any(str(term).endswith("DigitalTwin") for term in graph.subjects(RDF.type, OWL.Class))
    assert not any("isl.ics.forth.gr/ontology/echoes" in str(value) for triple in graph for value in triple)


def test_knowledge_snapshot_fixity_and_delta_are_explicit():
    graph = ontology_graph()
    assert (MODHERITAGE.currentSnapshot, RDFS.subPropertyOf, MODHERITAGE.hasKnowledgeSnapshot) in graph
    assert (MODHERITAGE.snapshotCreatedBy, OWL.inverseOf, MODHERITAGE.resultingSnapshot) in graph
    for term in (
        MODHERITAGE.includesAssertion,
        MODHERITAGE.canonicalizationProfile,
        MODHERITAGE.canonicalMaterialization,
        MODHERITAGE.snapshotGraphIri,
        MODHERITAGE.addedAssertion,
        MODHERITAGE.removedAssertion,
    ):
        assert (term, RDF.type, None) in graph


def test_canonical_knowledge_snapshot_materializations_match_declared_bytes_and_scope():
    metadata = Graph().parse(ROOT / "examples/valid/heritage-knowledge.ttl", format="turtle")
    expected = {
        URIRef("https://example.org/modavis/heritage-knowledge/snapshot-1"): (
            ROOT / "examples/valid/heritage-snapshot-1.nq",
            URIRef("https://example.org/graphs/instrument-1/revision-1"),
        ),
        URIRef("https://example.org/modavis/heritage-knowledge/snapshot-2"): (
            ROOT / "examples/valid/heritage-snapshot-2.nq",
            URIRef("https://example.org/graphs/instrument-1/revision-2"),
        ),
    }
    for snapshot, (path, graph_iri) in expected.items():
        materialization = metadata.value(snapshot, MODHERITAGE.canonicalMaterialization)
        checksum = metadata.value(materialization, MODMEDIA.hasChecksum)
        payload = path.read_bytes()
        assert int(metadata.value(materialization, MODMEDIA.byteSize)) == len(payload)
        assert str(metadata.value(checksum, MODEVIDENCE.checksumValue)) == hashlib.sha256(payload).hexdigest()
        assert str(metadata.value(materialization, MODMEDIA.mediaType)) == "application/n-quads"
        assert list(metadata.objects(snapshot, MODEVIDENCE.hasChecksum)) == []

        dataset = Dataset()
        dataset.parse(path, format="nquads")
        quads = list(dataset.quads((None, None, None, None)))
        assert quads
        assert {context for _, _, _, context in quads} == {graph_iri}
        included = set(metadata.objects(snapshot, MODHERITAGE.includesAssertion))
        assert {subject for subject, _, _, _ in quads} == included
        assert payload.decode("utf-8").splitlines() == sorted(payload.decode("utf-8").splitlines())


def test_documented_identity_layers_are_disjoint_in_owl():
    graph = ontology_graph()
    required_groups = {
        frozenset({
            MODINST.MusicalInstrument,
            MODINST.InstrumentState,
            MODINST.InstrumentConfiguration,
        }),
        frozenset({
            MODVMI.VirtualMusicalInstrument,
            MODVMI.VirtualInstrumentProduct,
            MODVMI.VirtualInstrumentVersion,
            MODVMI.VirtualInstrumentPackage,
        }),
    }
    asserted_groups = set()
    for axiom in graph.subjects(RDF.type, OWL.AllDisjointClasses):
        members = graph.value(axiom, OWL.members)
        if members:
            asserted_groups.add(frozenset(graph.items(members)))
    assert required_groups.issubset(asserted_groups)


def test_modavis_agents_are_conservatively_aligned_with_prov_agents():
    graph = ontology_graph()
    prov_agent = URIRef("http://www.w3.org/ns/prov#Agent")
    modavis_agent = URIRef(f"{MODAVIS_ROOT}ontology/core#Agent")
    assert (modavis_agent, RDFS.subClassOf, prov_agent) in graph


def test_processing_activity_accepts_explicit_used_software_association():
    data = Graph().parse(
        data="""
            @prefix ex: <https://example.org/provenance/> .
            @prefix modprov: <https://w3id.org/modavis/ontology/provenance#> .
            @prefix prov: <http://www.w3.org/ns/prov#> .
            ex:activity a modprov:ProcessingActivity ; modprov:usedSoftware ex:software .
            ex:software a prov:SoftwareAgent .
        """,
        format="turtle",
    )
    conforms, _, report_text = validate(
        data,
        shacl_graph=exchange_shapes_graph(),
        ont_graph=ontology_graph(),
        inference=None,
        advanced=True,
    )
    assert conforms, report_text


def test_exact_vao_040_corelease_binding_is_downstream_and_not_imported():
    text = (ROOT / "docs" / "VAO_INTEROPERABILITY.md").read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    assert "https://w3id.org/modavis/vao/0.4.0/modavis-mapping" in text
    assert "VAO-owned" in text
    assert "modavisBinding" in text
    assert "vao:LogicalAsset rdfs:subClassOf modmedia:DigitalAsset" in text
    assert "vao:Realization rdfs:subClassOf modmedia:Bitstream" in text
    assert "VAO as a whole is not a MODAVIS ontology module" in normalized
    assert not any("/vao/" in str(value) for value in ontology_graph().objects(None, OWL.imports))


def test_jsonld_context_expands_core_virtual_instrument_terms():
    context = json.loads((ROOT / "context" / "modavis-context.jsonld").read_text(encoding="utf-8"))["@context"]
    assert "hasEvidenceRelation" not in context
    assert context["assertionEvidenceRelation"]["@id"] == "modassert:hasEvidenceRelation"
    assert context["virtualInstrumentEvidenceRelation"]["@id"] == "modvmi:hasEvidenceRelation"
    data = {
        "@context": context,
        "id": "https://example.org/instrument",
        "type": "modvmi:VirtualMusicalInstrument",
        "instrumentType": "insttype:virtual-musical-instrument",
        "label": {"en": "Context example"},
    }
    graph = Graph().parse(data=json.dumps(data), format="json-ld")
    subject = URIRef("https://example.org/instrument")
    assert (subject, RDF.type, MODVMI.VirtualMusicalInstrument) in graph
    assert (subject, MODINST.instrumentType, URIRef("https://w3id.org/modavis/vocab/instrument-type/virtual-musical-instrument")) in graph

    heritage_data = {
        "@context": context,
        "id": "https://example.org/recognition",
        "type": "modheritage:HeritageRecognition",
        "recognizesResource": "https://example.org/instrument",
        "recognitionAssignedBy": ["https://example.org/community"],
        "recognitionStatus": "recognitionstatus:recognized",
    }
    heritage_graph = Graph().parse(data=json.dumps(heritage_data), format="json-ld")
    recognition = URIRef("https://example.org/recognition")
    assert (recognition, RDF.type, MODHERITAGE.HeritageRecognition) in heritage_graph
    assert (recognition, MODHERITAGE.recognizesResource, subject) in heritage_graph


@pytest.fixture(scope="module")
def built_candidates(tmp_path_factory):
    outputs = []
    for label in ("first", "second"):
        output = tmp_path_factory.mktemp(f"release-{label}")
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "build_release_candidate.py"), "--output-directory", str(output)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        outputs.append(output)
    return outputs


def test_release_build_is_byte_reproducible(built_candidates):
    archives = [output / "modavis-ontology-0.1.0.zip" for output in built_candidates]
    assert archives[0].read_bytes() == archives[1].read_bytes()
    checksums = [output / "modavis-ontology-0.1.0.zip.sha256" for output in built_candidates]
    assert checksums[0].read_text(encoding="utf-8") == checksums[1].read_text(encoding="utf-8")
    with zipfile.ZipFile(archives[0]) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names))
        assert all(".." not in Path(name).parts for name in names)
        assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist())


def test_release_serializations_are_graph_equivalent(built_candidates):
    site = built_candidates[0] / "site"
    for source in sorted((ROOT / "ontology").glob("modavis-*.ttl")):
        module = source.stem.removeprefix("modavis-")
        expected = Graph().parse(source, format="turtle")
        base = site / "ontology" / "0.1.0" if module == "network" else site / "ontology" / module / "0.1.0"
        stem = "ontology" if module == "network" else module
        for suffix in ("ttl", "jsonld", "rdf"):
            actual = Graph().parse(base / f"{stem}.{suffix}")
            assert isomorphic(expected, actual), (module, suffix)
    expected = Graph().parse(ROOT / "vocab" / "modavis-vocab.ttl", format="turtle")
    for suffix in ("ttl", "jsonld", "rdf"):
        actual = Graph().parse(site / "vocab" / "0.1.0" / f"vocab.{suffix}")
        assert isomorphic(expected, actual), suffix
    for profile in ("exchange", "publication"):
        base = site / "shapes" / profile / "0.1.0"
        expected = Graph().parse(base / "shapes.ttl", format="turtle")
        for suffix in ("jsonld", "rdf"):
            actual = Graph().parse(base / f"shapes.{suffix}")
            assert isomorphic(expected, actual), (profile, suffix)
    release = site / "release" / "0.1.0"
    expected = Graph().parse(release / "catalog.ttl", format="turtle")
    for suffix in ("jsonld", "rdf"):
        actual = Graph().parse(release / f"catalog.{suffix}")
        assert isomorphic(expected, actual), ("catalog", suffix)


def test_release_manifest_and_checksums_cover_generated_site(built_candidates):
    site = built_candidates[0] / "site"
    release = site / "release" / "0.1.0"
    manifest = json.loads((release / "release-manifest.json").read_text(encoding="utf-8"))
    assert manifest["type"] == "MODAVISOntologyRelease"
    assert manifest["packageVersion"] == "0.1.0"
    assert manifest["candidateVersion"] is None
    assert manifest["semanticVersion"] == "0.1.0"
    assert manifest["status"] == "released"
    assert manifest["publicationBlockers"] == []
    assert len(manifest["sourceCommit"]) == 40
    expected_dirty = bool(subprocess.check_output(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT, text=True
    ).strip())
    assert manifest["sourceTreeDirty"] is expected_dirty
    assert manifest["sourceTag"] == "0.1.0"
    assert manifest["sourceTagObjectType"] == "tag"
    assert manifest["sourceTagSigned"] is True
    assert manifest["licenses"] == ["Apache-2.0", "CC-BY-4.0"]
    assert {record["license"] for record in manifest["sourceArtifacts"]} == {
        "Apache-2.0", "CC-BY-4.0"
    }
    checksum_lines = (release / "checksums.sha256").read_text(encoding="utf-8").splitlines()
    indexed = {}
    for line in checksum_lines:
        checksum, relative = line.split("  ", 1)
        indexed[relative] = checksum
        assert hashlib.sha256((site / relative).read_bytes()).hexdigest() == checksum
    assert "release/0.1.0/release-manifest.json" in indexed
    assert "release/0.1.0/checksums.sha256" not in indexed


def test_dcat_distribution_checksums_match_generated_files(built_candidates):
    site = built_candidates[0] / "site"
    catalog = Graph().parse(site / "release" / "0.1.0" / "catalog.ttl", format="turtle")
    dataset = URIRef("https://w3id.org/modavis/release/0.1.0")
    catalogs = set(catalog.subjects(RDF.type, DCAT.Catalog))
    assert catalogs
    assert any((catalog_iri, DCAT.dataset, dataset) in catalog for catalog_iri in catalogs)
    checked = 0
    for distribution in catalog.subjects(RDF.type, DCAT.Distribution):
        download = catalog.value(distribution, DCAT.downloadURL)
        media_type = catalog.value(distribution, DCAT.mediaType)
        assert isinstance(media_type, URIRef)
        assert str(media_type).startswith("https://www.iana.org/assignments/media-types/")
        checksum = catalog.value(distribution, SPDX.checksum)
        if checksum is None:
            assert str(download).endswith(("release-manifest.json", "checksums.sha256"))
            continue
        relative = str(download).removeprefix("https://modavis-project.github.io/modavis-ontology-network/")
        value = str(catalog.value(checksum, SPDX.checksumValue))
        data = (site / relative).read_bytes()
        assert hashlib.sha256(data).hexdigest() == value
        assert int(catalog.value(distribution, DCAT.byteSize)) == len(data)
        assert catalog.value(checksum, SPDX.algorithm) == SPDX.checksumAlgorithm_sha256
        checked += 1
    assert checked >= 10


def test_w3id_targets_exist_in_generated_site(built_candidates):
    site = built_candidates[0] / "site"
    assert (site / ".nojekyll").is_file()
    modules = [path.stem.removeprefix("modavis-") for path in sorted((ROOT / "ontology").glob("modavis-*.ttl"))]
    for module in modules:
        base = site / "ontology" / "0.1.0" if module == "network" else site / "ontology" / module / "0.1.0"
        stem = "ontology" if module == "network" else module
        assert all((base / f"{stem}.{suffix}").is_file() for suffix in ("ttl", "jsonld", "rdf"))
        assert (base / "index.html").is_file()
    for relative in (
        "vocab/0.1.0/vocab.ttl",
        "context/0.1.0/context.jsonld",
        "shapes/exchange/0.1.0/shapes.ttl",
        "shapes/exchange/0.1.0/shapes.jsonld",
        "shapes/exchange/0.1.0/shapes.rdf",
        "shapes/publication/0.1.0/shapes.ttl",
        "shapes/publication/0.1.0/shapes.jsonld",
        "shapes/publication/0.1.0/shapes.rdf",
        "release/0.1.0/catalog.ttl",
    ):
        assert (site / relative).is_file(), relative
    for profile in ("exchange", "publication"):
        graph = Graph().parse(site / "shapes" / profile / "0.1.0" / "shapes.ttl", format="turtle")
        profile_iri = URIRef(f"{MODAVIS_ROOT}shapes/{profile}/0.1.0")
        assert (profile_iri, RDF.type, DCTERMS.Standard) in graph
        assert graph.value(profile_iri, DCTERMS.license)
        assert graph.value(profile_iri, DCTERMS.conformsTo) == URIRef("https://www.w3.org/TR/shacl/")
        assert graph.value(profile_iri, DCTERMS.requires) == URIRef(f"{MODAVIS_ROOT}ontology/0.1.0")
        assert graph.value(profile_iri, SH.entailment) is None
    rules = (ROOT / "w3id" / ".htaccess").read_text(encoding="utf-8")
    assert "__PUBLICATION_BASE__" not in rules
    assert "https://modavis-project.github.io/modavis-ontology-network" in rules


def test_generated_site_has_no_broken_local_links(built_candidates):
    site = built_candidates[0] / "site"

    class LinkCollector(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links = []

        def handle_starttag(self, tag, attrs):
            for key, value in attrs:
                if key in {"href", "src"} and value:
                    self.links.append(value)

    broken = []
    for page in sorted(site.rglob("*.html")):
        parser = LinkCollector()
        parser.feed(page.read_text(encoding="utf-8"))
        for link in parser.links:
            if link.startswith(("http:", "https:", "mailto:", "#", "data:")):
                continue
            relative = link.split("#", 1)[0].split("?", 1)[0]
            if relative and not (page.parent / relative).resolve().exists():
                broken.append((page.relative_to(site).as_posix(), link))
    assert not broken


def test_generated_publication_design_is_restrained_and_accessible(built_candidates):
    site = built_candidates[0] / "site"
    homepage = (site / "index.html").read_text(encoding="utf-8")
    module_page = (
        site / "ontology" / "instrument" / "0.1.0" / "index.html"
    ).read_text(encoding="utf-8")

    for page in (homepage, module_page):
        lowered = page.lower()
        assert '<meta name="viewport"' in lowered
        assert "linear-gradient" not in lowered
        assert "box-shadow" not in lowered
        assert "border-radius" not in lowered
        assert "fonts.googleapis" not in lowered
        assert "@import" not in lowered

    assert '<nav class="nav" aria-label="Primary navigation">' in homepage
    assert "document.createElement('details')" in homepage
    assert '<nav aria-label="Available distributions">' in module_page
    assert '<details class="term"' in module_page
    assert "<summary>" in module_page


def test_generated_term_pages_expose_dereferenceable_html_anchors(built_candidates):
    site = built_candidates[0] / "site"

    class IdCollector(HTMLParser):
        def __init__(self):
            super().__init__()
            self.ids = set()

        def handle_starttag(self, _tag, attrs):
            for key, value in attrs:
                if key == "id" and value:
                    self.ids.add(value)

    public_types = {OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty}
    for source in sorted((ROOT / "ontology").glob("modavis-*.ttl")):
        module = source.stem.removeprefix("modavis-")
        if module == "network":
            continue
        graph = Graph().parse(source, format="turtle")
        namespace = f"{MODAVIS_ROOT}ontology/{module}#"
        expected = {
            str(resource).split("#", 1)[1]
            for resource_type in public_types
            for resource in graph.subjects(RDF.type, resource_type)
            if str(resource).startswith(namespace)
        }
        parser = IdCollector()
        parser.feed((site / "ontology" / module / "0.1.0" / "index.html").read_text(encoding="utf-8"))
        assert expected.issubset(parser.ids), module

    graph = Graph().parse(ROOT / "vocab" / "modavis-vocab.ttl", format="turtle")
    expected = {
        str(resource).removeprefix(f"{MODAVIS_ROOT}vocab/")
        for resource_type in (SKOS.ConceptScheme, SKOS.Concept)
        for resource in graph.subjects(RDF.type, resource_type)
    }
    parser = IdCollector()
    parser.feed((site / "vocab" / "0.1.0" / "index.html").read_text(encoding="utf-8"))
    assert expected.issubset(parser.ids)


def test_authorized_release_index_drops_candidate_publication_claims(tmp_path):
    scripts_directory = str(ROOT / "scripts")
    sys.path.insert(0, scripts_directory)
    try:
        builder = importlib.import_module("build_release_candidate")
        site = tmp_path / "released-site"
        manifest = builder.build_site(site, blockers=[], released=True, source_state={
            "commit": "0" * 40, "tag": "0.1.0", "treeDirty": False,
            "tagObjectType": "tag", "tagSigned": True,
        })
    finally:
        sys.path.remove(scripts_directory)
    page = (site / "index.html").read_text(encoding="utf-8").lower()
    assert manifest["type"] == "MODAVISOntologyRelease"
    assert manifest["packageVersion"] == "0.1.0"
    assert manifest["candidateVersion"] is None
    assert manifest["status"] == "released"
    assert '<meta name="robots" content="index,follow">' in page
    for forbidden in (
        "release-candidate preview", "release candidate · not published",
        "unpublished release candidate", "candidate modules",
        "candidate source artifacts", "preview completeness boundary",
    ):
        assert forbidden not in page


def test_final_release_provenance_requires_clean_signed_annotated_exact_tag():
    scripts_directory = str(ROOT / "scripts")
    sys.path.insert(0, scripts_directory)
    try:
        builder = importlib.import_module("build_release_candidate")
        valid = {
            "commit": "0" * 40, "tag": "0.1.0", "treeDirty": False,
            "tagObjectType": "tag", "tagSigned": True,
        }
        assert builder.release_provenance_errors(valid) == []
        invalid = {
            "commit": "0" * 40, "tag": None, "treeDirty": True,
            "tagObjectType": None, "tagSigned": False,
        }
        failures = builder.release_provenance_errors(invalid)
    finally:
        sys.path.remove(scripts_directory)
    assert failures == [
        "source tree is dirty",
        "HEAD is not tagged exactly 0.1.0",
        "release tag is not annotated",
        "release tag does not contain a cryptographic signature",
    ]
