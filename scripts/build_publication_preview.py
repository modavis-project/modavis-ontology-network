#!/usr/bin/env python3
"""Build the deterministic MODAVIS ontology release-candidate preview."""

from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import sys

from rdflib import DCTERMS, OWL, RDF, RDFS, Graph, Namespace


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "publication-preview/index.html"
MODAVIS_ROOT = "https://w3id.org/modavis/"
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
VS = Namespace("http://www.w3.org/2003/06/sw-vocab-status/ns#")

PREFIXES = {
    "https://w3id.org/modavis/ontology/core#": "modavis",
    "https://w3id.org/modavis/ontology/instrument#": "modinst",
    "https://w3id.org/modavis/ontology/organ#": "modorgan",
    "https://w3id.org/modavis/ontology/events#": "modevent",
    "https://w3id.org/modavis/ontology/evidence#": "modevidence",
    "https://w3id.org/modavis/ontology/assertion#": "modassert",
    "https://w3id.org/modavis/ontology/provenance#": "modprov",
    "https://w3id.org/modavis/ontology/media#": "modmedia",
    "https://w3id.org/modavis/ontology/audio#": "modaudio",
    "https://w3id.org/modavis/ontology/midi#": "modmidi",
    "https://w3id.org/modavis/ontology/context#": "modcontext",
    "https://w3id.org/modavis/ontology/virtual-instrument#": "modvmi",
    "https://w3id.org/modavis/ontology/heritage#": "modheritage",
    "https://w3id.org/modavis/vocab/": "mdvsv",
    "https://w3id.org/modavis/vocab/instrument-type/": "insttype",
    "https://w3id.org/modavis/vocab/functional-role/": "role",
    "https://w3id.org/modavis/vocab/component-membership-type/": "membership",
    "https://w3id.org/modavis/vocab/assertion-status/": "assertionstatus",
    "https://w3id.org/modavis/vocab/assertion-predicate/": "assertionpredicate",
    "https://w3id.org/modavis/vocab/evidence-role/": "evidencerole",
    "https://w3id.org/modavis/vocab/event-type/": "eventtype",
    "https://w3id.org/modavis/vocab/representation-status/": "repstatus",
    "https://w3id.org/modavis/vocab/virtual-instrument-production-method/": "vmiproduction",
    "https://w3id.org/modavis/vocab/virtual-instrument-source-relation/": "vmisource",
    "https://w3id.org/modavis/vocab/compatibility-status/": "compatstatus",
    "https://w3id.org/modavis/vocab/heritage-recognition-status/": "recognitionstatus",
    "https://w3id.org/modavis/vocab/checksum-algorithm/": "checksum",
}


def compact(iri: str) -> str:
    for namespace, prefix in sorted(PREFIXES.items(), key=lambda item: len(item[0]), reverse=True):
        if iri.startswith(namespace):
            return f"{prefix}:{iri[len(namespace):]}"
    return iri


def literal_text(graph: Graph, subject, predicate) -> str:
    values = list(graph.objects(subject, predicate))
    preferred = next((value for value in values if getattr(value, "language", None) == "en"), None)
    return str(preferred or (values[0] if values else ""))


def module_name(path: Path) -> str:
    if path.parent.name == "vocab":
        return "vocabularies"
    return path.stem.removeprefix("modavis-")


def collect() -> tuple[list[dict], list[dict], dict]:
    module_paths = sorted(ROOT.glob("ontology/*.ttl")) + sorted(ROOT.glob("vocab/*.ttl"))
    modules: list[dict] = []
    terms: list[dict] = []
    combined = Graph()
    type_specs = (
        (OWL.Class, "Class"),
        (OWL.ObjectProperty, "Object property"),
        (OWL.DatatypeProperty, "Datatype property"),
        (SKOS.ConceptScheme, "Concept scheme"),
        (SKOS.Concept, "Concept"),
    )

    for path in module_paths:
        graph = Graph().parse(path, format="turtle")
        combined += graph
        ontology = next(graph.subjects(RDF.type, OWL.Ontology), None)
        name = module_name(path)
        module_terms: list[dict] = []
        for rdf_type, kind in type_specs:
            for resource in sorted(set(graph.subjects(RDF.type, rdf_type)), key=str):
                iri = str(resource)
                if not iri.startswith(MODAVIS_ROOT):
                    continue
                label = literal_text(graph, resource, RDFS.label) or literal_text(graph, resource, SKOS.prefLabel)
                definition = literal_text(graph, resource, SKOS.definition)
                status = literal_text(graph, resource, VS.term_status)
                domains = [compact(str(value)) for value in graph.objects(resource, RDFS.domain)]
                ranges = [compact(str(value)) for value in graph.objects(resource, RDFS.range)]
                schemes = [compact(str(value)) for value in graph.objects(resource, SKOS.inScheme)]
                relationships: list[str] = []
                relation_specs = (
                    (RDFS.subClassOf, "Subclass of"),
                    (RDFS.subPropertyOf, "Subproperty of"),
                    (OWL.equivalentClass, "Equivalent class"),
                    (OWL.equivalentProperty, "Equivalent property"),
                    (OWL.inverseOf, "Inverse of"),
                    (SKOS.broader, "Broader"),
                    (SKOS.narrower, "Narrower"),
                    (SKOS.exactMatch, "Exact match"),
                    (SKOS.closeMatch, "Close match"),
                )
                for predicate, relation_label in relation_specs:
                    for value in graph.objects(resource, predicate):
                        if str(value).startswith(("http://", "https://")):
                            relationships.append(f"{relation_label}: {compact(str(value))}")
                if (resource, RDF.type, OWL.FunctionalProperty) in graph:
                    relationships.append("Characteristic: functional")
                record = {
                    "iri": iri,
                    "qname": compact(iri),
                    "label": label or compact(iri),
                    "kind": kind,
                    "module": name,
                    "definition": definition,
                    "status": status,
                    "domain": domains,
                    "range": ranges,
                    "scheme": schemes,
                    "relationships": relationships,
                }
                terms.append(record)
                module_terms.append(record)
        imports = [compact(str(value)) for value in graph.objects(ontology, OWL.imports)] if ontology else []
        modules.append({
            "name": name,
            "title": literal_text(graph, ontology, DCTERMS.title) if ontology else "MODAVIS controlled vocabularies",
            "description": literal_text(graph, ontology, DCTERMS.description) if ontology else "Reviewed SKOS concept schemes used across the ontology network.",
            "iri": str(ontology) if ontology else "https://w3id.org/modavis/vocab/",
            "file": path.relative_to(ROOT).as_posix(),
            "imports": imports,
            "termCount": len(module_terms),
        })

    shape_graph = Graph()
    for path in ROOT.glob("shapes/*.ttl"):
        shape_graph.parse(path, format="turtle")
    SH = Namespace("http://www.w3.org/ns/shacl#")
    stats = {
        "triples": len(combined),
        "modules": len(set(combined.subjects(RDF.type, OWL.Ontology))),
        "classes": len(set(combined.subjects(RDF.type, OWL.Class))),
        "objectProperties": len(set(combined.subjects(RDF.type, OWL.ObjectProperty))),
        "datatypeProperties": len(set(combined.subjects(RDF.type, OWL.DatatypeProperty))),
        "concepts": len(set(combined.subjects(RDF.type, SKOS.Concept))),
        "shapes": len(set(shape_graph.subjects(RDF.type, SH.NodeShape))),
    }
    terms.sort(key=lambda record: (record["kind"], record["qname"]))
    return modules, terms, stats


def module_cards(modules: list[dict]) -> str:
    cards = []
    for module in modules:
        imports = " · ".join(module["imports"]) if module["imports"] else "No imports"
        cards.append(f"""
          <article class="module-record" data-module="{escape(module['name'])}">
            <div class="module-topline"><span>{escape(module['name'])}</span><span>{module['termCount']} terms</span></div>
            <div class="module-summary"><h3>{escape(module['title'])}</h3><p>{escape(module['description'])}</p></div>
            <div class="module-details"><dl>
              <div><dt>Canonical IRI</dt><dd><code>{escape(module['iri'])}</code></dd></div>
              <div><dt>Imports</dt><dd>{escape(imports)}</dd></div>
            </dl><a href="../{escape(module['file'])}">Turtle source</a></div>
          </article>""")
    return "\n".join(cards)


def build_html() -> str:
    modules, terms, stats = collect()
    metadata = json.loads((ROOT / "config/release-metadata.json").read_text(encoding="utf-8"))
    creator = metadata["creator"]
    affiliations = " · ".join(creator["affiliations"])
    term_json = json.dumps(terms, ensure_ascii=False).replace("<", "\\u003c")
    module_json = json.dumps(modules, ensure_ascii=False).replace("<", "\\u003c")
    cards = module_cards(modules)
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

    template = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <title>MODAVIS Ontology Network — 0.1.0 Release-Candidate Preview</title>
  <meta name="description" content="Release-candidate preview for the MODAVIS Ontology Network 0.1.0.">
  <style>
    :root {
      color-scheme: light;
      --ink: #172126;
      --muted: #5d676b;
      --paper: #f7f6f1;
      --surface: #ffffff;
      --soft: #eaf0ed;
      --line: #cfd4d0;
      --line-strong: #7e8885;
      --accent: #0a5a55;
      --accent-dark: #073f3c;
      --note: #725019;
      --note-bg: #f4ecd9;
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body { margin: 0; background: var(--paper); color: var(--ink); font: 16px/1.58 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    a { color: var(--accent-dark); text-decoration-thickness: 1px; text-underline-offset: 3px; }
    a:hover { text-decoration-thickness: 2px; }
    :focus-visible { outline: 3px solid #c18c2d; outline-offset: 3px; }
    .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
    code { font: .92em/1.5 "SFMono-Regular", Consolas, "Liberation Mono", monospace; overflow-wrap: anywhere; }
    .preview-bar { background: var(--note-bg); color: var(--note); border-bottom: 1px solid #d8c69d; padding: 7px 20px; text-align: center; font-size: .78rem; font-weight: 650; letter-spacing: .035em; }
    .site-head { background: var(--surface); border-bottom: 1px solid var(--line-strong); }
    .head-inner, main, .footer-inner { width: min(1140px, calc(100% - 48px)); margin: 0 auto; }
    .nav { display: flex; justify-content: space-between; align-items: center; gap: 26px; min-height: 62px; border-bottom: 1px solid var(--line); }
    .brand { display: flex; align-items: baseline; gap: 9px; color: var(--ink); text-decoration: none; }
    .brand strong { font-size: .96rem; letter-spacing: .08em; }
    .brand small { color: var(--muted); font-size: .82rem; }
    .nav-links { display: flex; flex-wrap: wrap; gap: 19px; }
    .nav-links a { color: var(--muted); text-decoration: none; font-size: .84rem; }
    .nav-links a:hover { color: var(--ink); }
    .hero { padding: 52px 0 48px; display: grid; grid-template-columns: minmax(0, 1.42fr) minmax(300px, .58fr); gap: 64px; align-items: start; }
    .eyebrow { margin: 0 0 15px; color: var(--accent); font-weight: 700; text-transform: uppercase; letter-spacing: .12em; font-size: .7rem; }
    h1, h2, h3 { line-height: 1.18; }
    h1 { max-width: 780px; margin: 0; font-size: clamp(2.35rem, 5vw, 4.05rem); font-weight: 650; letter-spacing: -.04em; }
    .lede { max-width: 760px; color: #3f4b50; font-size: 1.06rem; margin: 23px 0 26px; }
    .namespace { display: grid; grid-template-columns: auto minmax(0, 1fr); max-width: 650px; gap: 14px; align-items: baseline; padding-top: 12px; border-top: 1px solid var(--line); }
    .namespace span { color: var(--muted); font-size: .72rem; text-transform: uppercase; letter-spacing: .08em; }
    .namespace code { color: var(--accent-dark); }
    .hero-meta { border-top: 3px solid var(--accent); }
    .hero-meta dl { margin: 0; }
    .hero-meta div { display: grid; grid-template-columns: 7.6rem minmax(0, 1fr); gap: 14px; padding: 10px 0; border-bottom: 1px solid var(--line); }
    .hero-meta dt { color: var(--muted); font-size: .7rem; text-transform: uppercase; letter-spacing: .08em; }
    .hero-meta dd { margin: 0; font-size: .9rem; }
    main { padding: 66px 0 88px; }
    section { scroll-margin-top: 20px; margin-bottom: 76px; }
    .section-head { display: grid; grid-template-columns: minmax(190px, .42fr) minmax(0, 1fr); gap: 34px; align-items: start; padding-top: 15px; border-top: 1px solid var(--line-strong); margin-bottom: 25px; }
    .section-head h2 { margin: 0; font-size: clamp(1.45rem, 2.7vw, 2rem); font-weight: 680; letter-spacing: -.02em; }
    .section-head p { margin: 2px 0 0; max-width: 700px; color: var(--muted); }
    .stats { display: grid; grid-template-columns: repeat(6, 1fr); border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); background: var(--surface); }
    .stat { padding: 17px 14px; border-right: 1px solid var(--line); }
    .stat:last-child { border-right: 0; }
    .stat strong { display: block; color: var(--accent-dark); font-size: 1.55rem; font-weight: 620; font-variant-numeric: tabular-nums; }
    .stat span { color: var(--muted); font-size: .7rem; text-transform: uppercase; letter-spacing: .055em; }
    .scope-grid { margin-top: 25px; display: grid; grid-template-columns: 1fr 1fr; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
    .scope-card { padding: 24px 28px 24px 0; }
    .scope-card + .scope-card { border-left: 1px solid var(--line); padding-left: 28px; }
    .scope-card h3 { margin: 0 0 11px; font-size: 1.03rem; font-weight: 700; }
    .scope-card p, .scope-card ul { color: var(--muted); margin-bottom: 0; }
    .scope-card li + li { margin-top: 7px; }
    .dependency { display: grid; grid-template-columns: 1fr .8fr 1fr; gap: 0; align-items: stretch; border: 1px solid var(--line); background: var(--surface); }
    .dependency-column { display: grid; }
    .dep-node { padding: 13px 17px; border-bottom: 1px solid var(--line); }
    .dep-node:last-child { border-bottom: 0; }
    .dep-node strong { display: block; }
    .dep-node span { color: var(--muted); font-size: .82rem; }
    .dep-core { padding: 25px 21px; display: flex; flex-direction: column; justify-content: center; border-inline: 1px solid var(--line); background: var(--soft); }
    .dep-core strong { display: block; font-size: 1.18rem; }
    .dep-core span { color: var(--muted); }
    .vao-section { background: var(--soft); border-bottom: 1px solid var(--line); padding: 27px 30px 30px; }
    .vao-section .section-head { margin-bottom: 22px; }
    .vao-section .eyebrow { margin-bottom: 7px; }
    .vao-bridge { display: grid; grid-template-columns: 1fr auto 1.15fr auto 1fr; gap: 14px; align-items: stretch; }
    .vao-bridge-node { padding: 16px 0; border-top: 2px solid var(--line-strong); }
    .vao-bridge-node strong { display: block; font-size: 1rem; }
    .vao-bridge-node span { display: block; margin-top: 6px; color: var(--muted); font-size: .86rem; }
    .vao-bridge-node.vao-focus { border-color: var(--accent); }
    .vao-arrow { display: grid; place-items: center; color: var(--accent); }
    .vao-links { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 21px; }
    .vao-boundary { margin: 19px 0 0; color: var(--muted); border-top: 1px solid var(--line); padding-top: 14px; }
    .module-grid { border-top: 1px solid var(--line-strong); }
    .module-record { display: grid; grid-template-columns: 135px minmax(250px, .9fr) minmax(310px, 1.1fr); gap: 28px; padding: 22px 0; border-bottom: 1px solid var(--line); }
    .module-topline { display: flex; flex-direction: column; gap: 4px; color: var(--accent); font-size: .7rem; text-transform: uppercase; letter-spacing: .075em; }
    .module-summary h3 { margin: 0 0 7px; font-size: 1.03rem; }
    .module-summary p { color: var(--muted); margin: 0; }
    .module-details dl { margin: 0 0 10px; }
    .module-details dl div + div { margin-top: 8px; }
    .module-details dt { font-size: .68rem; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; }
    .module-details dd { margin: 2px 0 0; font-size: .82rem; }
    .module-details > a { font-size: .84rem; font-weight: 650; }
    .term-tools { display: grid; grid-template-columns: minmax(220px, 1fr) auto; gap: 12px; margin-bottom: 18px; }
    .term-tools input { width: 100%; border: 1px solid var(--line-strong); background: var(--surface); color: var(--ink); padding: 10px 11px; font: inherit; }
    .term-filters { display: flex; flex-wrap: wrap; gap: 7px; }
    .term-filter { border: 1px solid var(--line); background: transparent; color: var(--ink); padding: 7px 9px; font: .78rem/1.3 inherit; cursor: pointer; }
    .term-filter[aria-pressed="true"] { background: var(--accent-dark); border-color: var(--accent-dark); color: white; }
    .term-count { color: var(--muted); margin: 0 0 12px; }
    .term-list { border-top: 1px solid var(--line-strong); }
    .term { border-bottom: 1px solid var(--line); background: var(--surface); }
    .term summary { display: grid; grid-template-columns: minmax(210px, .7fr) minmax(0, 1.3fr) auto; gap: 22px; align-items: baseline; padding: 13px 15px; cursor: pointer; list-style: none; }
    .term summary::-webkit-details-marker { display: none; }
    .term summary::after { content: "+"; color: var(--accent); font-weight: 700; }
    .term[open] summary::after { content: "−"; }
    .term h3 { margin: 0; font: 650 .87rem/1.4 "SFMono-Regular", Consolas, monospace; color: var(--accent-dark); }
    .term-label { color: #334045; }
    .term-kind { color: var(--muted); font-size: .68rem; text-transform: uppercase; letter-spacing: .055em; }
    .term-body { display: grid; grid-template-columns: minmax(210px, .7fr) minmax(0, 1.3fr); gap: 22px; padding: 0 46px 16px 15px; }
    .term p { margin: 0; color: var(--muted); }
    .term-meta { margin-top: 8px; font-size: .82rem; color: var(--muted); }
    .term-iri { display: block; color: var(--muted); font-size: .72rem; }
    .empty { border: 1px dashed var(--line); padding: 28px; text-align: center; color: var(--muted); }
    .validation-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    .coverage-note { margin-bottom: 20px; padding: 16px 18px; background: var(--note-bg); border-left: 3px solid #a87827; color: #60451b; }
    .coverage-note strong { display: block; margin-bottom: 5px; }
    .checklist { margin: 0; padding: 0; list-style: none; background: var(--surface); border-top: 1px solid var(--line-strong); }
    .checklist li { display: grid; grid-template-columns: 23px 1fr; gap: 10px; padding: 13px 16px; border-bottom: 1px solid var(--line); }
    .checklist li:last-child { border-bottom: 0; }
    .checklist .done::before { content: "✓"; color: var(--accent); font-weight: 800; }
    .checklist .pending::before { content: "○"; color: #9a6c20; font-weight: 800; }
    .downloads { padding: 20px 22px; background: var(--soft); border-top: 1px solid var(--line-strong); }
    .downloads h3 { margin-top: 0; font-size: 1rem; }
    .downloads a { display: block; padding: 10px 0; border-bottom: 1px solid var(--line); }
    .citation { padding: 22px 25px; background: var(--surface); border-top: 1px solid var(--line-strong); border-bottom: 1px solid var(--line); }
    .citation h3 { margin-top: 0; font-size: 1rem; }
    .citation p { color: var(--muted); }
    footer { border-top: 1px solid var(--line-strong); }
    .footer-inner { padding: 29px 0 36px; display: flex; justify-content: space-between; gap: 30px; color: var(--muted); font-size: .82rem; }
    .footer-inner strong { color: var(--ink); }
    @media (max-width: 900px) {
      .hero { grid-template-columns: 1fr; }
      .stats { grid-template-columns: repeat(3, 1fr); }
      .stat:nth-child(3) { border-right: 0; }
      .stat:nth-child(-n+3) { border-bottom: 1px solid var(--line); }
      .dependency { grid-template-columns: 1fr; }
      .dep-core { border: 0; border-block: 1px solid var(--line); }
      .vao-bridge { grid-template-columns: 1fr; }
      .vao-arrow { transform: rotate(90deg); }
      .module-record { grid-template-columns: 110px minmax(0, 1fr); }
      .module-details { grid-column: 2; }
      .term-tools { grid-template-columns: 1fr; }
    }
    @media (max-width: 680px) {
      .head-inner, main, .footer-inner { width: min(100% - 28px, 1140px); }
      .nav { align-items: flex-start; padding: 13px 0; flex-direction: column; }
      .nav-links { gap: 12px 16px; }
      .hero { padding: 38px 0 40px; gap: 38px; }
      .hero-meta div { grid-template-columns: 6.6rem minmax(0, 1fr); }
      .section-head { grid-template-columns: 1fr; gap: 8px; }
      .footer-inner { align-items: flex-start; flex-direction: column; }
      .scope-grid, .validation-grid { grid-template-columns: 1fr; }
      .scope-card, .scope-card + .scope-card { padding: 20px 0; border-left: 0; }
      .scope-card + .scope-card { border-top: 1px solid var(--line); }
      .stats { grid-template-columns: repeat(2, 1fr); }
      .stat:nth-child(2n) { border-right: 0; }
      .stat:nth-child(3) { border-right: 1px solid var(--line); }
      .stat:nth-child(-n+4) { border-bottom: 1px solid var(--line); }
      .module-record { grid-template-columns: 1fr; gap: 11px; }
      .module-topline { flex-direction: row; }
      .module-details { grid-column: auto; }
      .term summary, .term-body { grid-template-columns: 1fr; gap: 6px; }
      .term summary { position: relative; padding-right: 38px; }
      .term summary::after { position: absolute; right: 15px; top: 14px; }
      .term-body { padding-right: 15px; }
    }
    @media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
  </style>
</head>
<body>
  <div class="preview-bar">0.1.0 release-candidate preview · not yet published or deployed</div>
  <header class="site-head">
    <div class="head-inner">
      <nav class="nav" aria-label="Primary navigation">
        <a class="brand" href="#top"><strong>MODAVIS</strong><small>Ontology Network</small></a>
        <div class="nav-links"><a href="#overview">Overview</a><a href="#modules">Modules</a><a href="#vao">VAO</a><a href="#terms">Terms</a><a href="#validation">Validation</a><a href="#citation">Citation</a></div>
      </nav>
      <div class="hero" id="top">
        <div>
          <p class="eyebrow">Ontology specification · version __VERSION__</p>
          <h1>MODAVIS Ontology Network</h1>
          <p class="lede">A modular semantic standard for physical, digitized, and virtual musical instruments: their identity, changing states, components, evidence, scholarly assertions, audio regions, and processing provenance. Pipe organs are represented through a dedicated specialization of the instrument-neutral model.</p>
          <div class="namespace"><span>Namespace</span><code>https://w3id.org/modavis/</code></div>
        </div>
        <aside class="hero-meta" aria-label="Publication metadata">
          <dl>
            <div><dt>Version</dt><dd>__VERSION__</dd></div>
            <div><dt>Status</dt><dd>0.1.0 release candidate · not published</dd></div>
            <div><dt>Creator</dt><dd><a href="__ORCID__">__CREATOR__</a></dd></div>
            <div><dt>License</dt><dd>CC BY 4.0</dd></div>
            <div><dt>Immutable version IRI</dt><dd><code>https://w3id.org/modavis/ontology/0.1.0</code></dd></div>
          </dl>
        </aside>
      </div>
    </div>
  </header>

  <main>
    <section id="overview">
      <div class="section-head"><h2>Network overview</h2><p>The publication separates durable domain semantics from database internals and application-specific exchange mechanics. Public terms keep stable, unversioned IRIs; immutable release artifacts receive version IRIs.</p></div>
      <div class="stats">
        <div class="stat"><strong>__MODULE_COUNT__</strong><span>modules</span></div>
        <div class="stat"><strong>__CLASS_COUNT__</strong><span>classes</span></div>
        <div class="stat"><strong>__OBJECT_PROPERTY_COUNT__</strong><span>object properties</span></div>
        <div class="stat"><strong>__DATATYPE_PROPERTY_COUNT__</strong><span>datatype properties</span></div>
        <div class="stat"><strong>__CONCEPT_COUNT__</strong><span>SKOS concepts</span></div>
        <div class="stat"><strong>__SHAPE_COUNT__</strong><span>SHACL shapes</span></div>
      </div>
      <div class="scope-grid">
        <article class="scope-card"><h3>In scope</h3><ul><li>Stable identity and multilingual naming</li><li>Instrument-neutral components and contextual functional roles</li><li>States, configurations, events, evidence, assertions, and provenance</li><li>Digital surrogates, fixed audio regions, and virtual-instrument identity</li><li>Contextual heritage recognition and checksum-fixed knowledge revisions</li><li>Pipe-organ specialization without making it the universal model</li></ul></article>
        <article class="scope-card"><h3>Deliberately separate</h3><ul><li>Operational database tables and workflow state</li><li>VAO ZIP paths, archive rules, and application profiles</li><li>Authentication, authorization, cache, and deployment behavior</li><li>Unreviewed external alignments and mutable vocabulary snapshots</li></ul></article>
      </div>
    </section>

    <section id="dependencies">
      <div class="section-head"><h2>Module architecture</h2><p>Core supplies common identity and temporal foundations. Domain modules reuse it without importing the VAO container vocabulary.</p></div>
      <div class="dependency">
        <div class="dependency-column"><div class="dep-node"><strong>Instrument</strong><span>generic instruments, components, roles</span></div><div class="dep-node"><strong>Evidence</strong><span>snapshots, fragments, selectors, fixity</span></div><div class="dep-node"><strong>Media & audio</strong><span>surrogates, assets, signals, regions, playback</span></div><div class="dep-node"><strong>Events</strong><span>domain history and participation</span></div></div>
        <div class="dep-core"><strong>MODAVIS Core</strong><span>identity · agents · places · time</span></div>
        <div class="dependency-column"><div class="dep-node"><strong>Organ</strong><span>optional instrument specialization</span></div><div class="dep-node"><strong>Virtual instrument</strong><span>playable identity, products, versions, packages, sources</span></div><div class="dep-node"><strong>Assertions</strong><span>claims, conflicts, editorial decisions</span></div><div class="dep-node"><strong>Provenance</strong><span>PROV-O-compatible processing lineage</span></div></div>
      </div>
    </section>

    <section id="modules">
      <div class="section-head"><h2>Candidate modules</h2><p>Each module has a stable ontology IRI, immutable 0.1.0 version IRI, human-readable term page, and generated Turtle, JSON-LD, and RDF/XML distributions. Preview links point to the checked source Turtle.</p></div>
      <div class="module-grid">__MODULE_CARDS__</div>
    </section>

    <section id="vao" class="vao-section">
      <div class="section-head"><div><p class="eyebrow">Related exchange standard</p><h2>Virtual Acoustic Object · VAO 0.4.0</h2></div><p>VAO is a downstream container and application profile, not an ontology module. Its final co-release binding uses MODAVIS 0.1.0 terms directly and adds an exact VAO-owned mapping.</p></div>
      <div class="vao-bridge" aria-label="Relationship between MODAVIS, VAO, and implementations">
        <div class="vao-bridge-node"><strong>MODAVIS Ontologies</strong><span>Instruments, components, states, configurations, evidence, assertions, events, provenance, and governed concepts.</span></div>
        <div class="vao-arrow" aria-hidden="true">→</div>
        <div class="vao-bridge-node vao-focus"><strong>VAO · .vao</strong><span>One ZIP64 object containing the semantic graph, audio, 3D models, animations, interaction data, paradata, analyses, rights, and fixity.</span></div>
        <div class="vao-arrow" aria-hidden="true">→</div>
        <div class="vao-bridge-node"><strong>OrgRec & VAOM</strong><span>OrgRec uses VAO as its primary exchange format. VAOM is the instrument-neutral manager, validator, and authoring environment.</span></div>
      </div>
      <div class="vao-links"><a href="../docs/VAO_INTEROPERABILITY.md">Co-release interoperability contract</a><a href="../examples/valid/virtual-pipe-organ.ttl">Virtual pipe-organ example</a></div>
      <p class="vao-boundary"><strong>Dependency direction:</strong> VAO 0.4.0 binds to the immutable MODAVIS 0.1.0 network and owns the conservative mapping graph. MODAVIS does not import VAO; the two validation regimes remain separate.</p>
    </section>

    <section id="terms">
      <div class="section-head"><h2>Term reference</h2><p>This preview is generated from the checked-in OWL and SKOS graphs. Search by label, compact name, IRI, definition, or module.</p></div>
      <div class="term-tools">
        <label><span class="sr-only">Search ontology terms</span><input id="term-search" type="search" placeholder="Search __TERM_TOTAL__ ontology terms…" autocomplete="off"></label>
        <div class="term-filters" aria-label="Filter terms by type">
          <button class="term-filter" type="button" data-kind="all" aria-pressed="true">All</button>
          <button class="term-filter" type="button" data-kind="Class" aria-pressed="false">Classes</button>
          <button class="term-filter" type="button" data-kind="Object property" aria-pressed="false">Object properties</button>
          <button class="term-filter" type="button" data-kind="Datatype property" aria-pressed="false">Datatype properties</button>
          <button class="term-filter" type="button" data-kind="Concept scheme" aria-pressed="false">Concept schemes</button>
          <button class="term-filter" type="button" data-kind="Concept" aria-pressed="false">Concepts</button>
        </div>
      </div>
      <p class="term-count" id="term-count" aria-live="polite"></p>
      <div class="term-list" id="term-list"></div>
    </section>

    <section id="validation">
      <div class="section-head"><h2>Release evidence</h2><p>Technical preparation and publication authorization are intentionally reported separately. Passing tests does not imply that the ontology has been released.</p></div>
      <div class="coverage-note"><strong>Preview completeness boundary</strong>This page contains the complete inventory of named OWL classes, object properties, datatype properties, SKOS concept schemes, and SKOS concepts from every candidate module, plus principal named relationships. The candidate builder adds per-module pages, alternate serializations, versioned SHACL profiles, examples, context, DCAT catalog, manifest, and checksums. Human review, deployment, and W3ID registration remain external gates.</div>
      <div class="validation-grid">
        <ul class="checklist">
          <li class="done">Turtle syntax, SHACL fixtures, reasoning, SKOS quality, and competency tests pass</li>
          <li class="done">Deterministic release-candidate site, archive, catalog, manifest, and checksum builder</li>
          <li class="done">Creator, publisher, ORCID, licenses, governance, citation, security, and concrete W3ID rules</li>
          <li class="done">VAO interoperability boundary, virtual pipe-organ example, and legacy MDVS compatibility shape</li>
          <li class="done">Accountable domain, ontology-engineering, and implementation reviews recorded</li>
          <li class="pending">Release authorization, deployment, clean tag, and W3ID registration</li>
        </ul>
        <aside class="downloads"><h3>Candidate source artifacts</h3><a href="../ontology/modavis-network.ttl">Ontology network · Turtle</a><a href="../vocab/modavis-vocab.ttl">Controlled vocabularies · Turtle</a><a href="../shapes/modavis-publication.shacl.ttl">Publication profile · SHACL</a><a href="../docs/RELEASE_PROCESS.md">Release process</a><a href="../docs/INTERPRETATION_GUIDE.md">Interpretation guide</a><a href="../config/w3id-routes.json">W3ID routes</a><a href="../CITATION.cff">Citation metadata</a></aside>
      </div>
    </section>

    <section id="citation">
      <div class="section-head"><h2>Citation and responsibility</h2><p>Final citation text will name the immutable ontology release and its public distribution location. Affiliations describe the creator’s research context and do not imply institutional publication or endorsement.</p></div>
      <div class="citation"><h3>Release-candidate citation</h3><p><strong>__CREATOR__.</strong> <em>MODAVIS Ontology Network</em>. Version __VERSION__. Unpublished release candidate. ORCID: <a href="__ORCID__">__ORCID__</a>.</p><p>Affiliations: __AFFILIATIONS__</p></div>
    </section>
  </main>

  <footer><div class="footer-inner"><div><strong>MODAVIS Ontology Network</strong><br>Release-candidate preview generated from the ontology source graph.</div><div>The namespace and license are defined; publication, deployment, and endorsement are not asserted by this preview.</div></div></footer>
  <script id="term-data" type="application/json">__TERM_JSON__</script>
  <script id="module-data" type="application/json">__MODULE_JSON__</script>
  <script>
    (() => {
      const terms = JSON.parse(document.getElementById('term-data').textContent);
      const list = document.getElementById('term-list');
      const count = document.getElementById('term-count');
      const search = document.getElementById('term-search');
      const filters = [...document.querySelectorAll('.term-filter')];
      let activeKind = 'all';

      function termElement(term) {
        const article = document.createElement('details');
        article.className = 'term';
        article.id = 'term-' + term.qname.replace(/[^A-Za-z0-9_-]/g, '-');
        const summary = document.createElement('summary');
        const identity = document.createElement('div');
        const name = document.createElement('h3');
        name.textContent = term.qname;
        const kind = document.createElement('div');
        kind.className = 'term-kind';
        kind.textContent = term.kind + ' · ' + term.module + (term.status ? ' · ' + term.status : '');
        identity.append(name, kind);
        const summaryLabel = document.createElement('span');
        summaryLabel.className = 'term-label';
        summaryLabel.textContent = term.label;
        summary.append(identity, summaryLabel);
        const body = document.createElement('div');
        body.className = 'term-body';
        const iri = document.createElement('code');
        iri.className = 'term-iri';
        iri.textContent = term.iri;
        const description = document.createElement('div');
        const label = document.createElement('p');
        label.textContent = term.definition || 'No definition supplied.';
        description.append(label);
        const details = [];
        if (term.domain.length) details.push('Domain: ' + term.domain.join(', '));
        if (term.range.length) details.push('Range: ' + term.range.join(', '));
        if (term.scheme.length) details.push('Scheme: ' + term.scheme.join(', '));
        if (term.relationships.length) details.push(...term.relationships);
        if (details.length) {
          const meta = document.createElement('div');
          meta.className = 'term-meta';
          meta.textContent = details.join(' · ');
          description.append(meta);
        }
        body.append(iri, description);
        article.append(summary, body);
        return article;
      }

      function openHashTarget() {
        if (!location.hash) return;
        const target = document.getElementById(location.hash.slice(1));
        if (target?.tagName === 'DETAILS') target.open = true;
      }

      function renderTerms() {
        const query = search.value.trim().toLocaleLowerCase();
        const visible = terms.filter((term) => {
          const kindMatches = activeKind === 'all' || term.kind === activeKind;
          const haystack = [term.qname, term.iri, term.label, term.definition, term.module, term.status, ...term.domain, ...term.range, ...term.scheme, ...term.relationships].join(' ').toLocaleLowerCase();
          return kindMatches && (!query || haystack.includes(query));
        });
        list.replaceChildren(...visible.map(termElement));
        count.textContent = `${visible.length} matching terms`;
        if (!visible.length) {
          const empty = document.createElement('div');
          empty.className = 'empty';
          empty.textContent = 'No ontology terms match this search.';
          list.append(empty);
        }
      }

      search.addEventListener('input', renderTerms);
      filters.forEach((button) => button.addEventListener('click', () => {
        activeKind = button.dataset.kind;
        filters.forEach((candidate) => candidate.setAttribute('aria-pressed', String(candidate === button)));
        renderTerms();
      }));
      renderTerms();
      openHashTarget();
      addEventListener('hashchange', openHashTarget);
    })();
  </script>
</body>
</html>
'''
    replacements = {
        "__VERSION__": escape(version),
        "__ORCID__": escape(creator["orcid"]),
        "__CREATOR__": escape(creator["name"]),
        "__AFFILIATIONS__": escape(affiliations),
        "__MODULE_COUNT__": str(stats["modules"]),
        "__CLASS_COUNT__": str(stats["classes"]),
        "__OBJECT_PROPERTY_COUNT__": str(stats["objectProperties"]),
        "__DATATYPE_PROPERTY_COUNT__": str(stats["datatypeProperties"]),
        "__CONCEPT_COUNT__": str(stats["concepts"]),
        "__SHAPE_COUNT__": str(stats["shapes"]),
        "__TERM_TOTAL__": str(len(terms)),
        "__MODULE_CARDS__": cards,
        "__TERM_JSON__": term_json,
        "__MODULE_JSON__": module_json,
    }
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    return template


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the MODAVIS release-candidate preview")
    parser.add_argument("--check", action="store_true", help="fail if the checked-in preview is stale")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    generated = build_html()
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != generated:
            print(f"Publication preview is stale: {output}", file=sys.stderr)
            return 1
        print(f"Publication preview is current: {output}")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generated, encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
