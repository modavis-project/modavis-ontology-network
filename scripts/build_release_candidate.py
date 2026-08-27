#!/usr/bin/env python3
"""Build the deterministic MODAVIS 0.1.0 publication and source candidate.

The command writes only to a new empty output directory. It has no deploy,
tag, push, or W3ID-submission mode.
"""

from __future__ import annotations

import argparse
from html import escape
import hashlib
import json
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET

from rdflib import DCTERMS, OWL, RDF, RDFS, Graph, Namespace
from rdflib.compare import to_canonical_graph

import build_publication_preview
import check_prepublication


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_VERSION = "0.1.0"
CANDIDATE_VERSION = "0.1.0-rc.7"
PUBLIC_BASE = "https://modavis-project.github.io/modavis-ontology-network"
W3ID = "https://w3id.org/modavis/"
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
VS = Namespace("http://www.w3.org/2003/06/sw-vocab-status/ns#")
PUBLISHER_IRI = "https://orcid.org/0000-0002-7904-3892"

ROOT_FILES = [
    ".gitignore", ".zenodo.json", "AUTHORS.md", "CHANGELOG.md", "CITATION.cff",
    "CONTRIBUTING.md", "DESIGN.md", "GOVERNANCE.md", "LICENSE", "LICENSE-CODE",
    "README.md", "REUSE.toml", "SECURITY.md", "VERSION", "catalog-v001.xml",
    "requirements-dev.in", "requirements-dev.txt",
]
TREE_DIRECTORIES = [
    ".github", "LICENSES", "config", "context", "docs", "examples",
    "ontology", "publication-preview", "shapes", "tests", "vocab", "w3id",
]
SCRIPT_FILES = [
    "scripts/check_prepublication.py",
    "scripts/build_publication_preview.py",
    "scripts/build_release_candidate.py",
    "scripts/check_w3id.py",
    "scripts/normalize_shacl_constraints.py",
    "scripts/normalize_term_metadata.py",
]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if value.endswith("\n") else value + "\n", encoding="utf-8")


def source_files() -> list[Path]:
    paths = [ROOT / relative for relative in ROOT_FILES + SCRIPT_FILES]
    for directory in TREE_DIRECTORIES:
        base = ROOT / directory
        paths.extend(path for path in base.rglob("*") if path.is_file())
    paths = [
        path for path in paths
        if "__pycache__" not in path.parts
        and ".pytest_cache" not in path.parts
        and path.name != ".DS_Store"
        and path.suffix != ".pyc"
    ]
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing candidate input: " + ", ".join(str(path) for path in missing))
    return sorted(set(paths), key=lambda path: path.relative_to(ROOT).as_posix())


def source_role(relative: str) -> str:
    if relative.startswith(("ontology/", "vocab/")):
        return "normative-semantic-artifact"
    if relative.startswith("shapes/"):
        return "normative-validation-artifact"
    if relative.startswith("examples/"):
        return "informative-evidence-artifact"
    if relative.startswith("tests/"):
        return "conformance-artifact"
    if relative.startswith("scripts/"):
        return "release-tooling"
    return "release-documentation-or-configuration"


def source_license(relative: str) -> str:
    if relative == "LICENSES/Apache-2.0.txt":
        return "Apache-2.0"
    if relative == "LICENSES/CC-BY-4.0.txt":
        return "CC-BY-4.0"
    code_paths = (".github/", "scripts/", "tests/")
    code_files = {
        ".gitignore", "LICENSE-CODE", "REUSE.toml", "requirements-dev.in",
        "requirements-dev.txt", "w3id/.htaccess",
    }
    return "Apache-2.0" if relative.startswith(code_paths) or relative in code_files else "CC-BY-4.0"


def git_source_state() -> dict:
    def git(*arguments: str) -> str:
        return subprocess.check_output(
            ["git", *arguments], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()

    commit = git("rev-parse", "HEAD")
    status = git("status", "--porcelain=v1", "--untracked-files=all")
    tags = [tag for tag in git("tag", "--points-at", "HEAD").splitlines() if tag]
    source_tag = PUBLIC_VERSION if PUBLIC_VERSION in tags else None
    tag_object_type = None
    tag_signed = False
    if source_tag:
        tag_object_type = git("cat-file", "-t", f"refs/tags/{source_tag}")
        tag_content = git("cat-file", "-p", f"refs/tags/{source_tag}") if tag_object_type == "tag" else ""
        tag_signed = "-----BEGIN PGP SIGNATURE-----" in tag_content or "-----BEGIN SSH SIGNATURE-----" in tag_content
    return {
        "commit": commit,
        "tag": source_tag,
        "treeDirty": bool(status),
        "tagObjectType": tag_object_type,
        "tagSigned": tag_signed,
    }


def release_provenance_errors(source_state: dict) -> list[str]:
    """Return final-release provenance failures for an inspected Git state."""
    errors = []
    if source_state["treeDirty"]:
        errors.append("source tree is dirty")
    if source_state["tag"] != PUBLIC_VERSION:
        errors.append(f"HEAD is not tagged exactly {PUBLIC_VERSION}")
    if source_state["tagObjectType"] != "tag":
        errors.append("release tag is not annotated")
    if not source_state["tagSigned"]:
        errors.append("release tag does not contain a cryptographic signature")
    return errors


def sorted_json(value, preserve_list_order: bool = False):
    if isinstance(value, dict):
        return {
            key: sorted_json(value[key], preserve_list_order=(key == "@list"))
            for key in sorted(value)
        }
    if isinstance(value, list):
        values = [sorted_json(item) for item in value]
        if preserve_list_order:
            return values
        return sorted(values, key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True))
    return value


def deterministic_jsonld(graph: Graph) -> str:
    raw = to_canonical_graph(graph).serialize(format="json-ld", indent=2)
    return json.dumps(sorted_json(json.loads(raw)), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def deterministic_rdfxml(graph: Graph) -> str:
    # The plain RDF/XML serializer keeps every subject flat. The pretty
    # serializer chooses an arbitrary object to inline when several subjects
    # point to it, which changes bytes between otherwise identical builds.
    root = ET.fromstring(to_canonical_graph(graph).serialize(format="xml"))

    def order(element: ET.Element) -> None:
        for child in element:
            order(child)
        element[:] = sorted(
            element,
            key=lambda child: (
                child.tag,
                tuple(sorted(child.attrib.items())),
                (child.text or "").strip(),
                ET.tostring(child, encoding="unicode"),
            ),
        )

    order(root)
    ET.indent(root, space="  ")
    return "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n" + ET.tostring(root, encoding="unicode") + "\n"


def write_serializations(source: Path, destination: Path, stem: str) -> Graph:
    graph = Graph().parse(source, format="turtle")
    destination.mkdir(parents=True, exist_ok=True)
    write_text(destination / f"{stem}.ttl", source.read_text(encoding="utf-8"))
    write_text(destination / f"{stem}.jsonld", deterministic_jsonld(graph))
    write_text(destination / f"{stem}.rdf", deterministic_rdfxml(graph))
    return graph


def value_text(graph: Graph, subject, predicate) -> str:
    values = list(graph.objects(subject, predicate))
    english = next((value for value in values if getattr(value, "language", None) == "en"), None)
    return str(english or (values[0] if values else ""))


def term_rows(graph: Graph, namespace: str) -> str:
    types = (
        (OWL.Class, "Class"),
        (OWL.ObjectProperty, "Object property"),
        (OWL.DatatypeProperty, "Datatype property"),
        (SKOS.ConceptScheme, "Concept scheme"),
        (SKOS.Concept, "Concept"),
    )
    records = []
    for rdf_type, kind in types:
        for resource in set(graph.subjects(RDF.type, rdf_type)):
            if not str(resource).startswith(namespace):
                continue
            label = value_text(graph, resource, RDFS.label) or value_text(graph, resource, SKOS.prefLabel)
            definition = value_text(graph, resource, SKOS.definition)
            status = value_text(graph, resource, VS.term_status)
            owner = value_text(graph, resource, RDFS.isDefinedBy)
            iri = str(resource)
            records.append((iri, iri.removeprefix(namespace), kind, label, definition, status, owner))
    return "\n".join(
        "<details class=\"term\" id=\"{}\"><summary><span><span class=\"kind\">{} · {}</span><strong>{}</strong></span><code class=\"local-name\">{}</code></summary><div class=\"term-body\"><p>{}</p><dl><div><dt>IRI</dt><dd><code>{}</code></dd></div><div><dt>Defined by</dt><dd><code>{}</code></dd></div></dl></div></details>".format(
            escape(local, quote=True), escape(kind), escape(status or "status not supplied"),
            escape(label or iri), escape(local), escape(definition or "No definition supplied."),
            escape(iri),
            escape(owner or "owner not supplied"),
        )
        for iri, local, kind, label, definition, status, owner in sorted(records)
    )


def artifact_page(title: str, description: str, canonical: str, body: str, stem: str) -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title><meta name="description" content="{escape(description)}">
<link rel="canonical" href="{escape(canonical)}"><link rel="alternate" type="text/turtle" href="{escape(stem)}.ttl">
<link rel="alternate" type="application/ld+json" href="{escape(stem)}.jsonld"><link rel="alternate" type="application/rdf+xml" href="{escape(stem)}.rdf">
<style>
:root{{--ink:#172126;--muted:#5d676b;--paper:#f7f6f1;--surface:#fff;--line:#cfd4d0;--line-strong:#7e8885;--accent:#0a5a55;--accent-dark:#073f3c}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.58 ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}a{{color:var(--accent-dark);text-underline-offset:3px}}:focus-visible{{outline:3px solid #c18c2d;outline-offset:3px}}code{{font:.9em/1.5 "SFMono-Regular",Consolas,"Liberation Mono",monospace;overflow-wrap:anywhere}}.page{{width:min(960px,calc(100% - 48px));margin:0 auto}}header{{padding:36px 0 28px;border-bottom:1px solid var(--line-strong);background:var(--surface)}}.kicker{{margin:0 0 17px;color:var(--accent);font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase}}h1{{max-width:800px;margin:0;font-size:clamp(2rem,5vw,3.35rem);line-height:1.08;letter-spacing:-.035em}}.description{{max-width:760px;margin:18px 0;color:#3f4b50;font-size:1.04rem}}nav{{display:flex;flex-wrap:wrap;gap:8px 18px;margin:24px 0 19px;padding-block:10px;border-block:1px solid var(--line)}}nav a{{font-size:.85rem;font-weight:650}}.canonical{{display:grid;grid-template-columns:7.5rem minmax(0,1fr);gap:14px;margin:0;font-size:.85rem}}.canonical span{{color:var(--muted);font-size:.68rem;letter-spacing:.07em;text-transform:uppercase}}main{{padding:42px 0 72px}}.term{{border-bottom:1px solid var(--line);background:var(--surface)}}.term:first-child{{border-top:1px solid var(--line-strong)}}.term summary{{display:grid;grid-template-columns:minmax(0,1fr) minmax(180px,.55fr) auto;gap:22px;align-items:center;padding:13px 15px;cursor:pointer;list-style:none}}.term summary::-webkit-details-marker{{display:none}}.term summary::after{{content:"+";color:var(--accent);font-weight:700}}.term[open] summary::after{{content:"−"}}.term summary strong{{display:block;margin-top:2px;font-size:.96rem}}.kind{{display:block;color:var(--muted);font-size:.66rem;letter-spacing:.06em;text-transform:uppercase}}.local-name{{color:var(--accent-dark);font-size:.76rem}}.term-body{{padding:0 48px 18px 15px}}.term-body>p{{max-width:760px;margin:0 0 13px;color:var(--muted)}}dl{{margin:0}}dl div{{display:grid;grid-template-columns:7.5rem minmax(0,1fr);gap:14px;padding-top:7px}}dt{{color:var(--muted);font-size:.68rem;letter-spacing:.06em;text-transform:uppercase}}dd{{margin:0}}article{{padding:18px 0;border-block:1px solid var(--line)}}article h2{{margin:0 0 8px;font-size:1.25rem}}article p,article li{{color:var(--muted)}}footer{{padding:24px 0 35px;border-top:1px solid var(--line-strong);color:var(--muted);font-size:.8rem}}@media(max-width:620px){{.page{{width:min(100% - 28px,960px)}}.term summary{{grid-template-columns:1fr auto;gap:6px 12px}}.term summary .local-name{{grid-column:1}}.term summary::after{{grid-column:2;grid-row:1/3}}.term-body{{padding-right:15px}}.canonical,dl div{{grid-template-columns:1fr;gap:2px}}}}@media(prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}}}
</style></head>
<body><header><div class="page"><p class="kicker">MODAVIS Ontology Network · immutable version {PUBLIC_VERSION}</p><h1>{escape(title)}</h1><p class="description">{escape(description)}</p><nav aria-label="Available distributions"><a href="{escape(stem)}.ttl">Turtle</a><a href="{escape(stem)}.jsonld">JSON-LD</a><a href="{escape(stem)}.rdf">RDF/XML</a><a href="{PUBLIC_BASE}/">Network overview</a></nav><p class="canonical"><span>Canonical IRI</span><code>{escape(canonical)}</code></p></div></header><main class="page">{body}</main><footer><div class="page">MODAVIS Ontology Network · CC BY 4.0 · Version {PUBLIC_VERSION}</div></footer><script>(()=>{{function openTarget(){{if(!location.hash)return;const target=document.getElementById(location.hash.slice(1));if(target?.tagName==='DETAILS')target.open=true}}openTarget();addEventListener('hashchange',openTarget)}})()</script></body></html>
"""


def build_modules(site: Path) -> list[dict]:
    distributions: list[dict] = []
    for source in sorted((ROOT / "ontology").glob("modavis-*.ttl")):
        module = source.stem.removeprefix("modavis-")
        is_network = module == "network"
        stem = "ontology" if is_network else module
        destination = site / "ontology" / PUBLIC_VERSION if is_network else site / "ontology" / module / PUBLIC_VERSION
        graph = write_serializations(source, destination, stem)
        ontology = next(graph.subjects(RDF.type, OWL.Ontology))
        title = value_text(graph, ontology, DCTERMS.title)
        description = value_text(graph, ontology, DCTERMS.description)
        canonical = f"{W3ID}ontology/{PUBLIC_VERSION}" if is_network else f"{W3ID}ontology/{module}/{PUBLIC_VERSION}"
        namespace = f"{W3ID}ontology#" if is_network else f"{W3ID}ontology/{module}#"
        write_text(destination / "index.html", artifact_page(
            title, description, canonical, term_rows(graph, namespace), stem
        ))
        for suffix, media_type in (("ttl", "text/turtle"), ("jsonld", "application/ld+json"), ("rdf", "application/rdf+xml")):
            distributions.append({
                "id": f"ontology-{module}-{suffix}",
                "title": f"{title} ({suffix})",
                "path": (
                    f"ontology/{PUBLIC_VERSION}/ontology.{suffix}" if is_network
                    else f"ontology/{module}/{PUBLIC_VERSION}/{module}.{suffix}"
                ),
                "mediaType": media_type,
            })

    source = ROOT / "vocab" / "modavis-vocab.ttl"
    destination = site / "vocab" / PUBLIC_VERSION
    graph = write_serializations(source, destination, "vocab")
    ontology = next(graph.subjects(RDF.type, OWL.Ontology))
    title = value_text(graph, ontology, DCTERMS.title)
    description = value_text(graph, ontology, DCTERMS.description)
    write_text(destination / "index.html", artifact_page(
        title, description, f"{W3ID}vocab/{PUBLIC_VERSION}", term_rows(graph, f"{W3ID}vocab/"), "vocab"
    ))
    for suffix, media_type in (("ttl", "text/turtle"), ("jsonld", "application/ld+json"), ("rdf", "application/rdf+xml")):
        distributions.append({
            "id": f"vocab-{suffix}", "title": f"{title} ({suffix})",
            "path": f"vocab/{PUBLIC_VERSION}/vocab.{suffix}", "mediaType": media_type,
        })
    return distributions


def build_profiles(site: Path, issued_date: str) -> list[dict]:
    records = []
    shape_paths = sorted((ROOT / "shapes").glob("*.ttl"))
    for profile, paths in (
        ("exchange", [path for path in shape_paths if path.name != "modavis-publication.shacl.ttl"]),
        ("publication", shape_paths),
    ):
        destination = site / "shapes" / profile / PUBLIC_VERSION
        destination.mkdir(parents=True, exist_ok=True)
        profile_iri = f"{W3ID}shapes/{profile}/{PUBLIC_VERSION}"
        metadata = f"""@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<{profile_iri}> a dcterms:Standard ;
  dcterms:title "MODAVIS {profile} SHACL profile"@en ;
  dcterms:description "Versioned {profile} conformance profile for MODAVIS 0.1.0 data."@en ;
  dcterms:creator <https://orcid.org/0000-0002-7904-3892> ;
  dcterms:publisher <https://orcid.org/0000-0002-7904-3892> ;
  dcterms:issued "{issued_date}"^^xsd:date ;
  dcterms:modified "{issued_date}"^^xsd:date ;
  dcterms:license <https://creativecommons.org/licenses/by/4.0/> ;
  dcterms:conformsTo <https://www.w3.org/TR/shacl/> ;
  dcterms:requires <https://w3id.org/modavis/ontology/0.1.0> .
"""
        combined = metadata + "\n" + "\n".join(
            f"# Source: {path.name}\n{path.read_text(encoding='utf-8').rstrip()}\n" for path in paths
        )
        write_text(destination / "shapes.ttl", combined)
        graph = Graph().parse(data=combined, format="turtle")
        write_text(destination / "shapes.jsonld", deterministic_jsonld(graph))
        write_text(destination / "shapes.rdf", deterministic_rdfxml(graph))
        sh = Namespace("http://www.w3.org/ns/shacl#")
        shape_count = len(set(graph.subjects(RDF.type, sh.NodeShape)))
        page = artifact_page(
            f"MODAVIS {profile} SHACL profile",
            f"Versioned {profile} validation profile containing {shape_count} node shapes.",
            profile_iri,
            f"<article><h2>{shape_count} node shapes</h2><p>Use the Turtle distribution with a SHACL 2017 processor supporting SHACL-SPARQL. Validation is over explicitly asserted exchange data; the profile declares no entailment regime.</p></article>",
            "shapes",
        )
        write_text(destination / "index.html", page)
        for suffix, media_type in (("ttl", "text/turtle"), ("jsonld", "application/ld+json"), ("rdf", "application/rdf+xml")):
            records.append({
                "id": f"shapes-{profile}-{suffix}", "title": f"MODAVIS {profile} SHACL profile ({suffix})",
                "path": f"shapes/{profile}/{PUBLIC_VERSION}/shapes.{suffix}", "mediaType": media_type,
            })

    context_destination = site / "context" / PUBLIC_VERSION / "context.jsonld"
    context_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "context" / "modavis-context.jsonld", context_destination)
    records.append({
        "id": "jsonld-context", "title": "MODAVIS JSON-LD context",
        "path": f"context/{PUBLIC_VERSION}/context.jsonld", "mediaType": "application/ld+json",
    })

    return records


def build_examples(site: Path) -> None:
    destination = site / "examples" / PUBLIC_VERSION
    for path in sorted((ROOT / "examples" / "valid").glob("*.ttl")):
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination / path.name)


def build_reference_files(site: Path) -> None:
    for directory in ("docs", "config"):
        destination = site / directory
        shutil.copytree(ROOT / directory, destination)
    for filename in ("CITATION.cff", "LICENSE", "LICENSE-CODE", "README.md"):
        shutil.copyfile(ROOT / filename, site / filename)


def catalog_turtle(distributions: list[dict], issued_date: str) -> str:
    lines = [
        "@prefix dcat: <http://www.w3.org/ns/dcat#> .",
        "@prefix dcterms: <http://purl.org/dc/terms/> .",
        "@prefix spdx: <http://spdx.org/rdf/terms#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "",
        f"<{W3ID}release/{PUBLIC_VERSION}#catalog> a dcat:Catalog ;",
        '  dcterms:title "MODAVIS Ontology Network release catalog"@en ;',
        '  dcterms:description "Version-pinned catalog of the immutable semantic, validation, contextualization, and release artifacts in MODAVIS 0.1.0."@en ;',
        f'  dcterms:issued "{issued_date}"^^xsd:date ;',
        f'  dcterms:modified "{issued_date}"^^xsd:date ;',
        f"  dcterms:publisher <{PUBLISHER_IRI}> ;",
        "  dcterms:conformsTo <https://www.w3.org/TR/vocab-dcat-3/> ;",
        "  dcterms:license <https://creativecommons.org/licenses/by/4.0/> ;",
        f"  dcat:dataset <{W3ID}release/{PUBLIC_VERSION}> .",
        "",
        f"<{W3ID}release/{PUBLIC_VERSION}> a dcat:Dataset ;",
        '  dcterms:title "MODAVIS Ontology Network 0.1.0"@en ;',
        '  dcterms:description "Immutable semantic and conformance artifacts for the initial MODAVIS Ontology Network release."@en ;',
        f"  dcat:version \"{PUBLIC_VERSION}\" ;",
        f'  dcterms:issued "{issued_date}"^^xsd:date ;',
        f"  dcterms:publisher <{PUBLISHER_IRI}> ;",
        "  dcterms:conformsTo <https://www.w3.org/TR/vocab-dcat-3/> ;",
        "  dcterms:license <https://creativecommons.org/licenses/by/4.0/> ;",
    ]
    for index, distribution in enumerate(distributions):
        suffix = ";" if index < len(distributions) - 1 else "."
        lines.append(f"  dcat:distribution <{W3ID}release/{PUBLIC_VERSION}/distribution/{distribution['id']}> {suffix}")
    lines.append("")
    for distribution in distributions:
        media_type_iri = f"https://www.iana.org/assignments/media-types/{distribution['mediaType']}"
        block = [
            f"<{W3ID}release/{PUBLIC_VERSION}/distribution/{distribution['id']}> a dcat:Distribution ;",
            f"  dcterms:title {json.dumps(distribution['title'])}@en ;",
            f"  dcat:mediaType <{media_type_iri}> ;",
        ]
        if distribution.get("sha256"):
            checksum_iri = f"{W3ID}release/{PUBLIC_VERSION}/checksum/{distribution['id']}-sha256"
            block.extend([
                f"  dcat:downloadURL <{PUBLIC_BASE}/{distribution['path']}> ;",
                f"  dcat:byteSize \"{distribution['byteSize']}\"^^xsd:nonNegativeInteger ;",
                f"  spdx:checksum <{checksum_iri}> .",
                "",
                f"<{checksum_iri}> a spdx:Checksum ;",
                "  spdx:algorithm spdx:checksumAlgorithm_sha256 ;",
                f"  spdx:checksumValue \"{distribution['sha256']}\"^^xsd:hexBinary .",
            ])
        else:
            block.append(f"  dcat:downloadURL <{PUBLIC_BASE}/{distribution['path']}> .")
        block.append("")
        lines.extend(block)
    return "\n".join(lines)


def build_catalog(site: Path, distributions: list[dict], issued_date: str) -> Path:
    release = site / "release" / PUBLIC_VERSION
    release.mkdir(parents=True, exist_ok=True)
    for distribution in distributions:
        path = site / distribution["path"]
        if path.is_file():
            data = path.read_bytes()
            distribution["sha256"] = digest(data)
            distribution["byteSize"] = len(data)
    turtle = catalog_turtle(distributions, issued_date)
    write_text(release / "catalog.ttl", turtle)
    graph = Graph().parse(data=turtle, format="turtle")
    write_text(release / "catalog.jsonld", deterministic_jsonld(graph))
    write_text(release / "catalog.rdf", deterministic_rdfxml(graph))
    links = "".join(
        f'<li><a href="../../{escape(record["path"])}">{escape(record["title"])}</a></li>'
        for record in distributions
    )
    write_text(release / "index.html", artifact_page(
        "MODAVIS Ontology Network 0.1.0 release",
        "Version-pinned catalog, manifest, checksums, ontology modules, validation profiles, context, and examples.",
        f"{W3ID}release/{PUBLIC_VERSION}",
        f'<article><h2>Distributions</h2><ul>{links}</ul><p><a href="release-manifest.json">Release manifest</a> · <a href="checksums.sha256">SHA-256 checksums</a></p></article>',
        "catalog",
    ))
    return release


def site_records(site: Path, excluded: set[str] | None = None) -> list[dict]:
    excluded = excluded or set()
    records = []
    for path in sorted((path for path in site.rglob("*") if path.is_file()), key=lambda item: item.relative_to(site).as_posix()):
        relative = path.relative_to(site).as_posix()
        if relative in excluded:
            continue
        data = path.read_bytes()
        records.append({"path": relative, "sha256": digest(data), "byteSize": len(data)})
    return records


def build_site(site: Path, blockers: list[str], released: bool, source_state: dict | None = None) -> dict:
    release_metadata = json.loads((ROOT / "config" / "release-metadata.json").read_text(encoding="utf-8"))
    source_state = source_state or git_source_state()
    site.mkdir(parents=True)
    write_text(site / ".nojekyll", "")
    issued_date = (release_metadata.get("publicationDate") or "2026-08-23") if released else "2026-08-23"
    distributions = build_modules(site)
    distributions.extend(build_profiles(site, issued_date))
    distributions.extend([
        {
            "id": "release-manifest", "title": "MODAVIS release manifest",
            "path": f"release/{PUBLIC_VERSION}/release-manifest.json", "mediaType": "application/json",
        },
        {
            "id": "release-checksums", "title": "MODAVIS release SHA-256 index",
            "path": f"release/{PUBLIC_VERSION}/checksums.sha256", "mediaType": "text/plain",
        },
    ])
    build_examples(site)
    build_reference_files(site)
    preview = build_publication_preview.build_html()
    public_page = preview
    if released:
        public_page = public_page.replace(
            '<meta name="robots" content="noindex,nofollow">', '<meta name="robots" content="index,follow">'
        ).replace(
            "0.1.0 release-candidate preview · not yet published or deployed",
            "MODAVIS Ontology Network · version 0.1.0",
        ).replace("0.1.0 Release-Candidate Preview", "Version 0.1.0").replace(
            "Release-candidate preview for the MODAVIS Ontology Network 0.1.0.",
            "Published term reference for the MODAVIS Ontology Network 0.1.0.",
        ).replace(
            "0.1.0 release candidate · not published", "Published version 0.1.0"
        ).replace(CANDIDATE_VERSION, "0.1.0").replace("Candidate modules", "Published modules").replace(
            "Preview links point to the checked source Turtle.", "Links point to the immutable 0.1.0 Turtle distributions."
        ).replace(
            "This preview is generated from the checked-in OWL and SKOS graphs.",
            "This reference is generated from the reviewed OWL and SKOS release graphs.",
        ).replace(
            "Technical preparation and publication authorization are intentionally reported separately. Passing tests does not imply that the ontology has been released.",
            "Technical validation, accountable review, and release authorization are recorded separately in the versioned release evidence.",
        ).replace(
            "Preview completeness boundary", "Release completeness boundary"
        ).replace(
            "from every candidate module", "from every published module"
        ).replace(
            "The candidate builder adds per-module pages, alternate serializations, versioned SHACL profiles, examples, context, DCAT catalog, manifest, and checksums. Human review, deployment, and W3ID registration remain external gates.",
            "The release includes per-module pages, alternate serializations, versioned SHACL profiles, examples, context, a DCAT catalog, a manifest, and checksums.",
        ).replace(
            "Deterministic release-candidate site, archive, catalog, manifest, and checksum builder",
            "Deterministic release site, archive, catalog, manifest, and checksum builder",
        ).replace("Candidate source artifacts", "Release artifacts").replace(
            "Release-candidate citation", "Versioned citation"
        ).replace("Unpublished release candidate.", "Ontology release.").replace(
            "Final citation text will name the immutable ontology release and its public distribution location.",
            "The citation names the immutable ontology release and its public distribution location.",
        ).replace(
            "Release-candidate preview generated from the ontology source graph.",
            "Versioned publication generated from the reviewed ontology source graph."
        ).replace(
            "The namespace and license are defined; publication, deployment, and endorsement are not asserted by this preview.",
            "CC BY 4.0 · Contributor affiliations do not imply institutional endorsement."
        ).replace(
            '<li class="pending">Accountable domain, ontology-engineering, and implementation reviews</li>',
            '<li class="done">Accountable domain, ontology-engineering, and implementation reviews recorded</li>',
        ).replace(
            '<li class="pending">Release authorization, deployment, clean tag, and W3ID registration</li>',
            '<li class="done">Release authorization and immutable publication record</li>',
        )
        forbidden_release_claims = (
            "release-candidate preview", "release candidate · not published",
            "unpublished release candidate", "candidate modules",
            "candidate source artifacts", "preview completeness boundary",
            "human review, deployment, and w3id registration remain external gates",
        )
        release_page_lower = public_page.lower()
        leftovers = [claim for claim in forbidden_release_claims if claim in release_page_lower]
        if leftovers:
            raise RuntimeError("published index retained candidate language: " + "; ".join(leftovers))
    for source in sorted((ROOT / "ontology").glob("modavis-*.ttl")):
        module = source.stem.removeprefix("modavis-")
        target = (
            f"ontology/{PUBLIC_VERSION}/ontology.ttl" if module == "network"
            else f"ontology/{module}/{PUBLIC_VERSION}/{module}.ttl"
        )
        public_page = public_page.replace(
            f'href="../ontology/{source.name}"',
            f'href="{target}"',
        )
    public_page = public_page.replace(
        'href="../vocab/modavis-vocab.ttl"', f'href="vocab/{PUBLIC_VERSION}/vocab.ttl"'
    ).replace(
        'href="../shapes/modavis-publication.shacl.ttl"',
        f'href="shapes/publication/{PUBLIC_VERSION}/shapes.ttl"',
    ).replace('href="../docs/', 'href="docs/').replace('href="../config/', 'href="config/').replace(
        'href="../CITATION.cff"', 'href="CITATION.cff"'
    ).replace(
        'href="../examples/valid/virtual-pipe-organ.ttl"',
        f'href="examples/{PUBLIC_VERSION}/virtual-pipe-organ.ttl"',
    )
    write_text(site / "index.html", public_page)
    release = build_catalog(site, distributions, issued_date)

    artifacts = site_records(site)
    source_records = []
    for path in source_files():
        data = path.read_bytes()
        relative = path.relative_to(ROOT).as_posix()
        source_records.append({
            "path": relative, "sha256": digest(data), "byteSize": len(data),
            "role": source_role(relative), "license": source_license(relative),
        })
    manifest = {
        "type": "MODAVISOntologyRelease" if released else "MODAVISOntologyReleaseCandidate",
        "packageVersion": PUBLIC_VERSION if released else CANDIDATE_VERSION,
        "candidateVersion": None if released else CANDIDATE_VERSION,
        "semanticVersion": PUBLIC_VERSION,
        "status": "released" if released else "release-candidate-not-published",
        "identifier": f"{W3ID}release/{PUBLIC_VERSION}",
        "identifierRoot": W3ID,
        "licenses": ["Apache-2.0", "CC-BY-4.0"],
        "licensePolicy": {
            "semanticArtifactsAndDocumentation": "CC-BY-4.0",
            "codeTestsAndAutomation": "Apache-2.0",
            "perSourceArtifactLicenseRecorded": True,
        },
        "publisher": release_metadata["publisher"],
        "publicationDate": release_metadata.get("publicationDate") if released else None,
        "publicationBlockers": blockers,
        "siteArtifactsExcludingManifestAndChecksums": artifacts,
        "sourceArtifacts": source_records,
        "sourceTreeSha256": digest(json.dumps(
            [{"path": record["path"], "sha256": record["sha256"]} for record in source_records],
            separators=(",", ":"), sort_keys=True,
        ).encode()),
        "sourceCommit": source_state["commit"],
        "sourceTag": source_state["tag"],
        "sourceTreeDirty": source_state["treeDirty"],
        "sourceTagObjectType": source_state["tagObjectType"],
        "sourceTagSigned": source_state["tagSigned"],
    }
    write_text(release / "release-manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
    checksum_records = site_records(site, {f"release/{PUBLIC_VERSION}/checksums.sha256"})
    write_text(release / "checksums.sha256", "".join(
        f"{record['sha256']}  {record['path']}\n" for record in checksum_records
    ))
    return manifest


def add_zip_bytes(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    info.flag_bits |= 0x800
    archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build(output_directory: Path) -> tuple[Path, Path, Path]:
    errors, blockers = check_prepublication.check(ROOT)
    if errors:
        raise RuntimeError("Preparation checks failed: " + "; ".join(errors))
    if output_directory.exists() and any(output_directory.iterdir()):
        raise FileExistsError("Candidate output directory must be empty; refusing to overwrite it")
    output_directory.mkdir(parents=True, exist_ok=True)

    metadata = json.loads((ROOT / "config" / "release-metadata.json").read_text(encoding="utf-8"))
    released = metadata.get("noPublish") is False
    if released and blockers:
        raise RuntimeError("Final release gates remain unresolved: " + "; ".join(blockers))
    source_state = git_source_state()
    if released:
        provenance_errors = release_provenance_errors(source_state)
        if provenance_errors:
            raise RuntimeError("Final release provenance gates remain unresolved: " + "; ".join(provenance_errors))
    package_version = PUBLIC_VERSION if released else CANDIDATE_VERSION
    top = f"modavis-ontology-{package_version}"
    site = output_directory / "site"
    manifest = build_site(site, blockers, released, source_state=source_state)
    archive_path = output_directory / f"{top}.zip"
    checksum_path = output_directory / f"{top}.zip.sha256"
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in source_files():
            relative = path.relative_to(ROOT).as_posix()
            add_zip_bytes(archive, f"{top}/source/{relative}", path.read_bytes())
        for path in sorted((path for path in site.rglob("*") if path.is_file()), key=lambda item: item.relative_to(site).as_posix()):
            add_zip_bytes(archive, f"{top}/site/{path.relative_to(site).as_posix()}", path.read_bytes())
        add_zip_bytes(archive, f"{top}/release-manifest.json", (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode())
        archive.comment = (
            b"MODAVIS Ontology Network 0.1.0; immutable release"
            if released else b"MODAVIS Ontology Network 0.1.0-rc.7; release candidate, not published"
        )
    write_text(checksum_path, f"{digest(archive_path.read_bytes())}  {archive_path.name}")
    return site, archive_path, checksum_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the deterministic MODAVIS 0.1.0 release candidate")
    parser.add_argument("--output-directory", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    try:
        site, archive, checksum = build(args.output_directory.resolve())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(site)
    print(archive)
    print(checksum)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
