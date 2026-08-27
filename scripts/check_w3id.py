#!/usr/bin/env python3
"""Check MODAVIS W3ID rules and optionally their generated target inventory."""

from __future__ import annotations

import argparse
import grp
import http.client
import json
import os
from pathlib import Path
import pwd
import shutil
import socket
import subprocess
import tempfile
import time

from rdflib import Graph, RDF, Namespace


ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "w3id" / ".htaccess"
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")


def apache_compiled_modules(binary: str) -> set[str]:
    """Return modules compiled into Apache rather than provided as DSOs."""
    result = subprocess.run(
        [binary, "-l"], text=True, capture_output=True, check=False
    )
    if result.returncode:
        return set()
    return {
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip().startswith("mod_") and line.strip().endswith(".c")
    }


def static_errors() -> list[str]:
    errors = []
    routes = json.loads((ROOT / "config" / "w3id-routes.json").read_text(encoding="utf-8"))
    text = RULES.read_text(encoding="utf-8")
    destination = routes.get("destinationBase")
    if not destination or destination not in text:
        errors.append("configured destination is absent from .htaccess")
    for forbidden in ("__PUBLICATION_BASE__", "example.com", "R=301"):
        if forbidden in text:
            errors.append(f"forbidden W3ID token: {forbidden}")
    for required in (
        "Options -MultiViews", "RewriteEngine On", "R=303", "R=404", "R=406",
        "text/html", "text/turtle", "application/ld\\+json", "application/rdf\\+xml",
        "ontology/0.1.0/ontology.ttl", "context/0.1.0/context.jsonld",
        "release/0.1.0/catalog.ttl",
    ):
        if required not in text:
            errors.append(f"missing W3ID rule requirement: {required}")
    if text.count("R=406") < 5:
        errors.append("every content-negotiated artifact family must reject unsupported explicit formats")
    vocabulary = Graph().parse(ROOT / "vocab" / "modavis-vocab.ttl", format="turtle")
    base = f"{routes['root']}vocab/"
    expected_terms = {
        str(term).removeprefix(base)
        for rdf_type in (SKOS.ConceptScheme, SKOS.Concept)
        for term in vocabulary.subjects(RDF.type, rdf_type)
        if str(term).startswith(base)
    }
    for term in expected_terms:
        if term not in text:
            errors.append(f"enumerated vocabulary term absent from W3ID rules: {term}")
    if routes.get("requirements", {}).get("unknownTermResponse") != 404:
        errors.append("route registry does not require 404 for unknown vocabulary terms")
    if "RewriteRule ^vao" in text:
        errors.append("separately governed VAO routes must not be deployed by the ontology candidate")
    return errors


def target_errors(site: Path) -> list[str]:
    errors = []
    modules = [path.stem.removeprefix("modavis-") for path in sorted((ROOT / "ontology").glob("modavis-*.ttl"))]
    expected = [
        "index.html", "ontology/0.1.0/index.html", "ontology/0.1.0/ontology.ttl",
        "ontology/0.1.0/ontology.jsonld", "ontology/0.1.0/ontology.rdf",
        "vocab/0.1.0/index.html", "vocab/0.1.0/vocab.ttl",
        "vocab/0.1.0/vocab.jsonld", "vocab/0.1.0/vocab.rdf",
        "context/0.1.0/context.jsonld",
        "release/0.1.0/index.html", "release/0.1.0/catalog.ttl",
        "release/0.1.0/catalog.jsonld", "release/0.1.0/catalog.rdf",
    ]
    for module in modules:
        if module == "network":
            continue
        expected.extend(
            f"ontology/{module}/0.1.0/{name}"
            for name in ("index.html", f"{module}.ttl", f"{module}.jsonld", f"{module}.rdf")
        )
    for profile in ("exchange", "publication"):
        expected.extend(
            f"shapes/{profile}/0.1.0/{name}"
            for name in ("index.html", "shapes.ttl", "shapes.jsonld", "shapes.rdf")
        )
    for relative in expected:
        if not (site / relative).is_file():
            errors.append(f"missing generated W3ID target: {relative}")
    return errors


def apache_syntax_error(require_apache: bool) -> str | None:
    binary = shutil.which("httpd") or shutil.which("apache2")
    module_candidates = [
        Path("/usr/libexec/apache2/mod_rewrite.so"),
        Path("/usr/lib/apache2/modules/mod_rewrite.so"),
        Path("/usr/lib64/httpd/modules/mod_rewrite.so"),
    ]
    module = next((path for path in module_candidates if path.is_file()), None)
    mpm_candidates = [
        ("mpm_event_module", Path("/usr/lib/apache2/modules/mod_mpm_event.so")),
        ("mpm_prefork_module", Path("/usr/libexec/apache2/mod_mpm_prefork.so")),
        ("mpm_prefork_module", Path("/usr/lib64/httpd/modules/mod_mpm_prefork.so")),
    ]
    mpm = next(((name, path) for name, path in mpm_candidates if path.is_file()), None)
    if not binary or not module or not mpm:
        return "Apache httpd with mod_rewrite is unavailable" if require_apache else None
    with tempfile.TemporaryDirectory(prefix="modavis-w3id-apache-") as temporary:
        runtime = Path(temporary)
        config = runtime / "httpd.conf"
        rules = RULES.read_text(encoding="utf-8")
        config.write_text(
            "\n".join([
                f'ServerRoot "{runtime}"',
                f'DefaultRuntimeDir "{runtime}"',
                f'PidFile "{runtime / "httpd.pid"}"',
                f'ErrorLog "{runtime / "error.log"}"',
                "Listen 127.0.0.1:8765",
                "ServerName localhost",
                f'LoadModule {mpm[0]} "{mpm[1]}"',
                f'LoadModule rewrite_module "{module}"',
                f'<Directory "{runtime}">',
                rules,
                "</Directory>",
                "",
            ]),
            encoding="utf-8",
        )
        result = subprocess.run(
            [binary, "-t", "-f", str(config)], text=True, capture_output=True, check=False
        )
        if result.returncode:
            return (result.stderr or result.stdout).strip()
    return None


def apache_behavior_errors(require_apache: bool) -> list[str]:
    binary = shutil.which("httpd") or shutil.which("apache2")
    module_roots = (
        Path("/usr/libexec/apache2"), Path("/usr/lib/apache2/modules"),
        Path("/usr/lib64/httpd/modules"),
    )

    def module_path(filename: str) -> Path | None:
        return next((root / filename for root in module_roots if (root / filename).is_file()), None)

    rewrite = module_path("mod_rewrite.so")
    authz = module_path("mod_authz_core.so")
    unixd = module_path("mod_unixd.so")
    unixd_compiled_in = (
        bool(binary) and "mod_unixd.c" in apache_compiled_modules(binary)
    )
    mpm_options = (
        ("mpm_prefork_module", module_path("mod_mpm_prefork.so")),
        ("mpm_event_module", module_path("mod_mpm_event.so")),
    )
    mpm = next(((name, path) for name, path in mpm_options if path), None)
    runtime_missing = (
        not binary
        or not rewrite
        or not authz
        or (not unixd and not unixd_compiled_in)
        or not mpm
    )
    if runtime_missing:
        message = "Apache runtime with rewrite, authorization, Unix, and MPM modules is unavailable"
        return [message] if require_apache else []

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]

    cases = (
        ("/ontology", "text/turtle", 303, "/ontology/0.1.0/ontology.ttl"),
        ("/ontology/core/0.1.0", "application/ld+json", 303, "/ontology/core/0.1.0/core.jsonld"),
        ("/ontology/heritage/0.1.0", "text/turtle", 303, "/ontology/heritage/0.1.0/heritage.ttl"),
        ("/vocab/compatibility-status/compatible", "text/html", 303, "/vocab/0.1.0/index.html#compatibility-status/compatible"),
        ("/vocab/heritage-recognition-status/recognized", "text/html", 303, "/vocab/0.1.0/index.html#heritage-recognition-status/recognized"),
        ("/context/0.1.0", "application/ld+json", 303, "/context/0.1.0/context.jsonld"),
        ("/shapes/exchange/0.1.0", "application/pdf", 406, None),
        ("/alignment/vao/0.2.2-to-modavis-0.1.0", "application/rdf+xml", 404, None),
        ("/release/0.1.0", "text/turtle", 303, "/release/0.1.0/catalog.ttl"),
        ("/ontology/9.9.9", "text/html", 404, None),
        ("/vocab/9.9.9", "text/html", 404, None),
        ("/vocab/not-a-scheme", "text/html", 404, None),
        ("/vocab/compatibility-status/not-a-concept", "text/html", 404, None),
        ("/vocab/event-type/compatible", "text/html", 404, None),
        ("/vao/0.2.2", "text/html", 404, None),
    )
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="modavis-w3id-smoke-") as temporary:
        runtime = Path(temporary)
        config = runtime / "httpd.conf"
        config.write_text(
            "\n".join([
                f'ServerRoot "{runtime}"',
                f'DefaultRuntimeDir "{runtime}"',
                f'PidFile "{runtime / "httpd.pid"}"',
                f'ErrorLog "{runtime / "error.log"}"',
                f'Listen 127.0.0.1:{port}',
                "ServerName localhost",
                f'LoadModule {mpm[0]} "{mpm[1]}"',
                *([f'LoadModule unixd_module "{unixd}"'] if unixd else []),
                f'LoadModule authz_core_module "{authz}"',
                f'LoadModule rewrite_module "{rewrite}"',
                f'User "{pwd.getpwuid(os.getuid()).pw_name}"',
                f'Group "{grp.getgrgid(os.getgid()).gr_name}"',
                "StartServers 1",
                "MinSpareServers 1",
                "MaxSpareServers 1",
                "ServerLimit 1",
                "MaxRequestWorkers 1",
                f'DocumentRoot "{runtime}"',
                f'<Directory "{runtime}">',
                "Require all granted",
                RULES.read_text(encoding="utf-8"),
                "</Directory>",
                "",
            ]),
            encoding="utf-8",
        )
        process = subprocess.Popen(
            [binary, "-f", str(config), "-DFOREGROUND"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            start_new_session=True,
        )
        try:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    errors.append("Apache redirect smoke server exited: " + (stderr or stdout).strip())
                    return errors
                try:
                    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
                    connection.request("GET", "/ontology", headers={"Accept": "text/html"})
                    connection.getresponse().read()
                    connection.close()
                    break
                except OSError:
                    time.sleep(0.05)
            else:
                errors.append("Apache redirect smoke server did not become ready")
                return errors

            for path, accept, expected_status, expected_location_suffix in cases:
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
                connection.request("GET", path, headers={"Accept": accept})
                response = connection.getresponse()
                response.read()
                location = response.getheader("Location")
                connection.close()
                if response.status != expected_status:
                    errors.append(f"{path} with Accept {accept}: expected {expected_status}, got {response.status}")
                if expected_location_suffix and (not location or not location.endswith(expected_location_suffix)):
                    errors.append(f"{path} with Accept {accept}: unexpected Location {location!r}")
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, help="generated site root whose redirect targets must exist")
    parser.add_argument("--require-apache", action="store_true")
    args = parser.parse_args()
    errors = static_errors()
    if args.site:
        errors.extend(target_errors(args.site.resolve()))
    syntax_error = apache_syntax_error(args.require_apache)
    if syntax_error:
        errors.append(f"Apache syntax check failed: {syntax_error}")
    errors.extend(apache_behavior_errors(args.require_apache))
    print(json.dumps({"w3id": "PASS" if not errors else "FAIL", "errors": errors}, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
