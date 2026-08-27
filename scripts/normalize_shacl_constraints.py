#!/usr/bin/env python3
"""Give anonymous SHACL constraints stable, documented IRIs.

The source profiles remain modular, but every node, property, logical branch,
and SPARQL constraint that may appear in a validation report receives a stable
identifier. The transformation is idempotent: already named constraints keep
their identifiers.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import urldefrag

from rdflib import BNode, Graph, Literal, Namespace, RDF, RDFS, URIRef


SH = Namespace("http://www.w3.org/ns/shacl#")
SHAPE_RELATIONS = (SH.property, SH.sparql, SH["not"], SH.node, SH.qualifiedValueShape)
LOGICAL_RELATIONS = (SH["or"], SH.xone, SH["and"])


def local_name(value: URIRef) -> str:
    text = str(value)
    fragment = urldefrag(text)[1]
    return fragment or text.rstrip("/").rsplit("/", 1)[-1]


def humanize(value: str) -> str:
    value = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value)
    value = value.replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", value).strip().lower()


def safe_fragment(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-")
    return cleaned or "Constraint"


def compact_name(value) -> str:
    if isinstance(value, URIRef):
        return local_name(value)
    return str(value)


def generated_property_message(graph: Graph, shape: URIRef, path_label: str) -> Literal:
    requirements: list[str] = []
    minimum = graph.value(shape, SH.minCount)
    maximum = graph.value(shape, SH.maxCount)
    if minimum is not None and maximum is not None and minimum == maximum:
        requirements.append(f"exactly {minimum} value(s) are required")
    else:
        if minimum is not None:
            requirements.append(f"at least {minimum} value(s) are required")
        if maximum is not None:
            requirements.append(f"at most {maximum} value(s) are permitted")
    datatype = graph.value(shape, SH.datatype)
    if datatype is not None:
        requirements.append(f"values must use the {compact_name(datatype)} datatype")
    value_class = graph.value(shape, SH["class"])
    if value_class is not None:
        requirements.append(f"values must be instances of {compact_name(value_class)}")
    node_kind = graph.value(shape, SH.nodeKind)
    if node_kind is not None:
        requirements.append(f"values must have node kind {compact_name(node_kind)}")
    if graph.value(shape, SH["in"]) is not None:
        requirements.append("values must belong to the enumerated release set")
    if graph.value(shape, SH.hasValue) is not None:
        requirements.append(f"the value {compact_name(graph.value(shape, SH.hasValue))} is required")
    if graph.value(shape, SH.minLength) is not None:
        requirements.append(f"lexical length must be at least {graph.value(shape, SH.minLength)}")
    if graph.value(shape, SH.pattern) is not None:
        requirements.append("lexical form must match the declared pattern")
    for predicate, phrase in (
        (SH.minInclusive, "value must be at least"),
        (SH.maxInclusive, "value must be at most"),
        (SH.minExclusive, "value must be greater than"),
        (SH.maxExclusive, "value must be less than"),
    ):
        boundary = graph.value(shape, predicate)
        if boundary is not None:
            requirements.append(f"{phrase} {boundary}")
    if graph.value(shape, SH.lessThan) is not None:
        requirements.append(f"values must be less than {compact_name(graph.value(shape, SH.lessThan))}")
    if graph.value(shape, SH.lessThanOrEquals) is not None:
        requirements.append(
            f"values must be no greater than {compact_name(graph.value(shape, SH.lessThanOrEquals))}"
        )
    if graph.value(shape, SH.uniqueLang) is not None:
        requirements.append("at most one value is permitted per language")
    if graph.value(shape, SH["or"]) is not None:
        requirements.append("at least one named alternative shape must conform")
    if graph.value(shape, SH.xone) is not None:
        requirements.append("exactly one named alternative shape must conform")
    if not requirements:
        requirements.append("every constraint declared by this named property shape must be satisfied")
    message = f"{path_label[:1].upper() + path_label[1:]} constraint: " + "; ".join(requirements) + "."
    return Literal(message, lang="en")


def node_key(graph: Graph, node) -> tuple[str, ...]:
    path = graph.value(node, SH.path)
    message = graph.value(node, SH.message)
    select = graph.value(node, SH.select)
    values = sorted(
        f"{local_name(predicate) if isinstance(predicate, URIRef) else predicate}={obj}"
        for predicate, obj in graph.predicate_objects(node)
        if not isinstance(obj, BNode)
    )
    return (str(path or ""), str(message or ""), str(select or ""), *values)


def unique_iri(namespace: str, fragment: str, used: set[URIRef]) -> URIRef:
    base = safe_fragment(fragment)
    candidate = URIRef(namespace + base)
    number = 2
    while candidate in used:
        candidate = URIRef(f"{namespace}{base}-{number:02d}")
        number += 1
    used.add(candidate)
    return candidate


def profile_namespace(root: URIRef) -> str:
    text = str(root)
    if "#" not in text:
        raise ValueError(f"Named shape does not use a hash namespace: {root}")
    return text.rsplit("#", 1)[0] + "#"


def name_constraints(graph: Graph) -> tuple[set[URIRef], set[URIRef], set[URIRef]]:
    roots = sorted(
        {shape for shape in graph.subjects(RDF.type, SH.NodeShape) if isinstance(shape, URIRef)},
        key=str,
    )
    used = {node for node in set(graph.subjects()) | set(graph.objects()) if isinstance(node, URIRef)}
    replacements: dict[BNode, URIRef] = {}
    property_shapes: set[URIRef] = set()
    sparql_constraints: set[URIRef] = set()
    logical_shapes: set[URIRef] = set()

    for root in roots:
        namespace = profile_namespace(root)
        root_fragment = local_name(root)
        seen: set = set()
        counters = {"property": 0, "sparql": 0, "alternative": 0, "nested": 0}

        def assign(node, kind: str, hint: str) -> URIRef:
            if isinstance(node, URIRef):
                return node
            if node in replacements:
                return replacements[node]
            counters[kind] += 1
            suffix = f"{counters[kind]:02d}"
            iri = unique_iri(namespace, f"{root_fragment}-{hint}-{suffix}", used)
            replacements[node] = iri
            return iri

        def walk(shape) -> None:
            if shape in seen:
                return
            seen.add(shape)

            properties = sorted(set(graph.objects(shape, SH.property)), key=lambda node: node_key(graph, node))
            for prop in properties:
                path = graph.value(prop, SH.path)
                path_hint = local_name(path) if isinstance(path, URIRef) else "Path"
                named = assign(prop, "property", f"{safe_fragment(path_hint)}-PropertyShape")
                property_shapes.add(named)
                walk(prop)

            constraints = sorted(set(graph.objects(shape, SH.sparql)), key=lambda node: node_key(graph, node))
            for constraint in constraints:
                named = assign(constraint, "sparql", "SPARQLConstraint")
                sparql_constraints.add(named)
                walk(constraint)

            for relation in LOGICAL_RELATIONS:
                for head in graph.objects(shape, relation):
                    for option in graph.items(head):
                        if isinstance(option, BNode):
                            named = assign(
                                option,
                                "alternative",
                                f"{local_name(relation)}-Alternative-NodeShape",
                            )
                            logical_shapes.add(named)
                            walk(option)

            for relation in (SH["not"], SH.node, SH.qualifiedValueShape):
                for nested in graph.objects(shape, relation):
                    if isinstance(nested, BNode):
                        named = assign(
                            nested,
                            "nested",
                            f"{local_name(relation)}-NodeShape",
                        )
                        logical_shapes.add(named)
                        walk(nested)

        walk(root)

    for subject, predicate, obj in list(graph):
        new_subject = replacements.get(subject, subject)
        new_object = replacements.get(obj, obj)
        if new_subject != subject or new_object != obj:
            graph.remove((subject, predicate, obj))
            graph.add((new_subject, predicate, new_object))

    return property_shapes, sparql_constraints, logical_shapes


def document_constraints(
    graph: Graph,
    property_shapes: set[URIRef],
    sparql_constraints: set[URIRef],
    logical_shapes: set[URIRef],
) -> None:
    node_shapes = {shape for shape in graph.subjects(RDF.type, SH.NodeShape) if isinstance(shape, URIRef)}
    node_shapes.update(logical_shapes)

    for shape in node_shapes:
        graph.add((shape, RDF.type, SH.NodeShape))
        label = Literal(humanize(local_name(shape)), lang="en")
        graph.add((shape, RDFS.label, label))
        graph.add((shape, SH.name, label))
        graph.add((shape, SH.severity, SH.Violation))
        direct_parameters = {SH.nodeKind, SH.pattern, SH["or"], SH.xone, SH["not"], SH.node}
        if any((shape, predicate, None) in graph for predicate in direct_parameters):
            if not graph.value(shape, SH.message):
                graph.add((shape, SH.message, Literal(
                    "The focus node must satisfy the named logical, node-kind, or lexical constraint declared by this shape.",
                    lang="en",
                )))

    for shape in property_shapes:
        graph.add((shape, RDF.type, SH.PropertyShape))
        path = graph.value(shape, SH.path)
        path_label = humanize(local_name(path)) if isinstance(path, URIRef) else "property path"
        label = Literal(f"{path_label} property constraint", lang="en")
        graph.add((shape, RDFS.label, label))
        graph.add((shape, SH.name, label))
        graph.add((shape, SH.severity, SH.Violation))
        current_messages = list(graph.objects(shape, SH.message))
        generated_messages = [
            message for message in current_messages
            if str(message).startswith("Values of ") and "declared by this property shape" in str(message)
        ]
        if not current_messages or len(generated_messages) == len(current_messages):
            for message in generated_messages:
                graph.remove((shape, SH.message, message))
            graph.add((shape, SH.message, generated_property_message(graph, shape, path_label)))

    for constraint in sparql_constraints:
        label = Literal(humanize(local_name(constraint)), lang="en")
        graph.add((constraint, RDFS.label, label))
        graph.add((constraint, SH.name, label))
        graph.add((constraint, SH.severity, SH.Violation))


def normalize(path: Path) -> None:
    graph = Graph().parse(path, format="turtle")
    property_shapes, sparql_constraints, logical_shapes = name_constraints(graph)
    document_constraints(graph, property_shapes, sparql_constraints, logical_shapes)
    serialized = graph.serialize(format="turtle", encoding=None).rstrip() + "\n"
    path.write_text(serialized, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    paths = args.paths or sorted(Path("shapes").glob("*.ttl"))
    for path in paths:
        normalize(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
