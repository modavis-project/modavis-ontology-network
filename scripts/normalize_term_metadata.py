#!/usr/bin/env python3
"""Add declaration ownership and lifecycle status to public MODAVIS terms.

The rewrite is deliberately textual so the curated Turtle layout and comments
remain intact. It is idempotent and fails closed when a declared public term
cannot be matched to one top-level Turtle subject block.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from rdflib import Graph, OWL, RDF, SKOS, URIRef


MODAVIS_ROOT = "https://w3id.org/modavis/"
VS_NAMESPACE = "http://www.w3.org/2003/06/sw-vocab-status/ns#"
PUBLIC_TYPES = {
    OWL.Class,
    OWL.ObjectProperty,
    OWL.DatatypeProperty,
    SKOS.ConceptScheme,
    SKOS.Concept,
}


def prefix_map(text: str) -> dict[str, str]:
    return dict(re.findall(r"@prefix\s+([A-Za-z][\w-]*):\s*<([^>]+)>\s*\.", text))


def expand_subject(token: str, prefixes: dict[str, str]) -> URIRef | None:
    if token.startswith("<") and token.endswith(">"):
        return URIRef(token[1:-1])
    if ":" in token:
        prefix, local_name = token.split(":", 1)
        if prefix in prefixes:
            return URIRef(prefixes[prefix] + local_name)
    return None


def add_vs_prefix(text: str) -> str:
    declaration = f"@prefix vs: <{VS_NAMESPACE}> .\n"
    if declaration in text:
        return text
    lines = text.splitlines(keepends=True)
    last_prefix = max(index for index, line in enumerate(lines) if line.startswith("@prefix "))
    lines.insert(last_prefix + 1, declaration)
    return "".join(lines)


def normalize(path: Path) -> None:
    graph = Graph().parse(path, format="turtle")
    ontology_iris = list(graph.subjects(RDF.type, OWL.Ontology))
    if len(ontology_iris) != 1:
        raise ValueError(f"Expected one ontology declaration in {path}, found {ontology_iris}")
    owner = ontology_iris[0]
    terms = {
        term
        for public_type in PUBLIC_TYPES
        for term in graph.subjects(RDF.type, public_type)
        if isinstance(term, URIRef) and str(term).startswith(MODAVIS_ROOT)
    }
    if not terms:
        return

    text = add_vs_prefix(path.read_text(encoding="utf-8"))
    prefixes = prefix_map(text)
    lines = text.splitlines(keepends=True)
    subject_lines: dict[URIRef, int] = {}
    top_level_lines: list[int] = []

    for index, line in enumerate(lines):
        if not line.strip() or line[0].isspace() or line.startswith(("@prefix ", "#")):
            continue
        top_level_lines.append(index)
        token = line.split(maxsplit=1)[0]
        subject = expand_subject(token, prefixes)
        if subject in terms:
            if subject in subject_lines:
                raise ValueError(f"Multiple top-level declaration blocks for {subject} in {path}")
            subject_lines[subject] = index

    missing = terms - set(subject_lines)
    if missing:
        raise ValueError(f"Could not locate public term blocks in {path}: {sorted(map(str, missing))}")

    for term, start in sorted(subject_lines.items(), key=lambda item: item[1], reverse=True):
        last = next(
            (
                index for index in range(start, len(lines))
                if lines[index].rstrip().endswith(".")
            ),
            None,
        )
        if last is None:
            raise ValueError(f"Declaration block for {term} does not end in a Turtle period")
        block = "".join(lines[start:last + 1])
        if "rdfs:isDefinedBy" in block or "vs:term_status" in block:
            if not ("rdfs:isDefinedBy" in block and "vs:term_status" in block):
                raise ValueError(f"Partial lifecycle metadata for {term} in {path}")
            continue
        stripped = lines[last].rstrip("\n")
        period = stripped.rfind(".")
        lines[last] = stripped[:period].rstrip() + " ;\n"
        lines[last + 1:last + 1] = [
            f"  rdfs:isDefinedBy <{owner}> ;\n",
            '  vs:term_status "testing" .\n',
        ]

    path.write_text("".join(lines), encoding="utf-8")
    verified = Graph().parse(path, format="turtle")
    for term in terms:
        if (term, URIRef("http://www.w3.org/2000/01/rdf-schema#isDefinedBy"), owner) not in verified:
            raise ValueError(f"Missing declaration owner after rewrite: {term}")
        if (term, URIRef(VS_NAMESPACE + "term_status"), None) not in verified:
            raise ValueError(f"Missing lifecycle status after rewrite: {term}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    paths = args.paths or [
        *sorted(Path("ontology").glob("modavis-*.ttl")),
        *sorted(Path("vocab").glob("*.ttl")),
    ]
    for path in paths:
        normalize(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
