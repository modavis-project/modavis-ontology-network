#!/usr/bin/env python3
"""Validate a MODAVIS release candidate without performing publication."""

from __future__ import annotations

import argparse
from datetime import date, datetime
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ROOT = "https://w3id.org/modavis/"
EXPECTED_ORCID = "https://orcid.org/0000-0002-7904-3892"
CANDIDATE_VERSION = "0.1.0-rc.7"


def check(root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    blockers: list[str] = []
    required = [
        "AUTHORS.md", "CITATION.cff", "GOVERNANCE.md", "CONTRIBUTING.md",
        "SECURITY.md", "CHANGELOG.md", "VERSION", "LICENSE", "LICENSE-CODE",
        "REUSE.toml", "LICENSES/Apache-2.0.txt", "LICENSES/CC-BY-4.0.txt",
        "requirements-dev.in", "requirements-dev.txt",
        "config/release-metadata.json", "config/competency-questions.json",
        "config/external-dependencies.json",
        "config/w3id-routes.json", "w3id/README.md", "w3id/.htaccess",
        "context/modavis-context.jsonld",
        "docs/RELEASE_PROCESS.md", "docs/INTERPRETATION_GUIDE.md",
        "docs/VAO_INTEROPERABILITY.md",
        "docs/EVALUATION_AND_RELEASE_READINESS.md", "docs/MDVS_V1_COMPATIBILITY.md",
        "docs/COMPETENCY_QUESTIONS.md",
        "scripts/build_release_candidate.py", "scripts/build_publication_preview.py",
        "scripts/check_w3id.py", "scripts/normalize_shacl_constraints.py",
        "scripts/normalize_term_metadata.py",
        "publication-preview/index.html",
    ]
    for relative in required:
        if not (root / relative).is_file():
            errors.append(f"missing preparation artifact: {relative}")

    try:
        metadata = json.loads((root / "config/release-metadata.json").read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"invalid release metadata: {exc}"], blockers

    if metadata.get("identifierRoot") != EXPECTED_ROOT:
        errors.append("unexpected common identifier root")
    if metadata.get("targetVersion") != "0.1.0":
        errors.append("unexpected target semantic version")
    if metadata.get("creator", {}).get("orcid") != EXPECTED_ORCID:
        errors.append("creator ORCID drift")
    if metadata.get("status") not in {"private-development", "release-candidate", "public-development-release", "released"}:
        errors.append("unrecognized preparation status")

    no_publish = metadata.get("noPublish") is not False
    authorization = metadata.get("releaseAuthorization", {})
    if no_publish:
        blockers.append("release authority has not removed the no-publish guard")
        if metadata.get("status") == "released":
            errors.append("release metadata cannot claim released status while the no-publish guard is active")
        if authorization.get("status") == "authorized":
            errors.append("release authorization cannot be active while the no-publish guard remains set")
    else:
        if authorization.get("status") != "authorized" or not authorization.get("authorizedBy") or not authorization.get("authorizedAt"):
            blockers.append("release authorization record is incomplete")
        else:
            try:
                authorized_at = datetime.fromisoformat(str(authorization["authorizedAt"]).replace("Z", "+00:00"))
                if authorized_at.tzinfo is None:
                    raise ValueError("timezone missing")
            except (TypeError, ValueError):
                blockers.append("release authorization timestamp must be an ISO 8601 date-time with timezone")
        try:
            date.fromisoformat(metadata.get("publicationDate", ""))
        except (TypeError, ValueError):
            blockers.append("publication date is not assigned")
        if metadata.get("status") != "released":
            blockers.append("release metadata status is not released")
    for key, label in (
        ("publisher", "publisher"),
        ("publicRepository", "public repository"),
        ("publicationHost", "publication host"),
        ("securityContact", "security contact"),
    ):
        if not metadata.get(key):
            blockers.append(f"{label} is not approved")
    if not metadata.get("maintainerContacts"):
        blockers.append("durable maintainer contact is not approved")
    licenses = metadata.get("licenses", {})
    for key in ("semanticArtifactsAndDocumentation", "code"):
        record = licenses.get(key, {})
        if not record.get("approved") or not record.get("spdx") or not record.get("iri"):
            blockers.append(f"license approval pending or incomplete: {key}")
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    expected_review_candidate = version if no_publish else CANDIDATE_VERSION
    reviews = metadata.get("requiredReviews", {})
    stale_review_labels: list[str] = []
    for key in ("domain", "ontologyEngineering", "implementation"):
        people = reviews.get(key)
        if not people:
            blockers.append(f"reviewer not assigned: {key}")
            continue
        if not isinstance(people, list):
            blockers.append(f"review records must be a list: {key}")
            continue
        for index, review in enumerate(people):
            label = f"{key}[{index}]"
            if not isinstance(review, dict):
                blockers.append(f"review record is not structured: {label}")
                continue
            if not review.get("name"):
                blockers.append(f"reviewer name missing: {label}")
            try:
                date.fromisoformat(str(review.get("reviewedAt", "")))
            except ValueError:
                blockers.append(f"review date missing or invalid: {label}")
            if review.get("reviewedCandidate") != expected_review_candidate:
                stale_review_labels.append(label)
            if review.get("outcome") not in {"approved", "approved-with-resolved-findings"}:
                blockers.append(f"review outcome is not approved: {label}")
            if review.get("findingsResolved") is not True:
                blockers.append(f"review findings are not recorded as resolved: {label}")
            if not isinstance(review.get("independentOfLeadEditor"), bool):
                blockers.append(f"review independence declaration missing: {label}")
    if stale_review_labels:
        blockers.append(
            f"recorded reviews do not cover semantic candidate {expected_review_candidate}: "
            + ", ".join(stale_review_labels)
        )
    semantic_reviews = [
        review
        for role in ("domain", "ontologyEngineering")
        for review in reviews.get(role, [])
        if isinstance(review, dict)
    ]
    independent_semantic_review = any(
        review.get("independentOfLeadEditor") is True for review in semantic_reviews
    )
    if semantic_reviews and not independent_semantic_review:
        policy = metadata.get("reviewPolicy", {})
        if policy.get("independentReviewRequiredForInitialRelease") is True:
            blockers.append("no independent domain or ontology-engineering review is recorded")
        if policy.get("independentReviewRecommended") is not True:
            blockers.append("non-independent review policy does not retain an independent-review recommendation")
        if policy.get("selfReviewLimitationDisclosed") is not True or not policy.get("rationale"):
            blockers.append("self-review limitation is not disclosed by release policy")
        for role in ("domain", "ontologyEngineering", "implementation"):
            for index, review in enumerate(reviews.get(role, [])):
                if (
                    isinstance(review, dict)
                    and review.get("independentOfLeadEditor") is False
                    and not review.get("independenceLimitation")
                ):
                    blockers.append(f"self-review independence limitation missing: {role}[{index}]")
    dependency = metadata.get("dependencies", {}).get("modavisRelease13VocabularySnapshot", {})
    if dependency.get("status") not in {"ready", "not-publicly-versioned"}:
        errors.append("MODAVIS Release 1.3 vocabulary dependency has not been resolved honestly")
    if dependency.get("status") == "not-publicly-versioned" and not dependency.get("decisionRationale"):
        errors.append("Release 1.3 no-public-artifact decision lacks a rationale")

    expected_version = CANDIDATE_VERSION if no_publish else "0.1.0"
    if version != expected_version:
        errors.append(f"expected VERSION {expected_version} for the current publication guard, found {version}")
    citation = (root / "CITATION.cff").read_text(encoding="utf-8")
    if f'version: "{expected_version}"' not in citation:
        errors.append(f"CITATION.cff version does not match {expected_version}")
    if not no_publish:
        publication_date = metadata.get("publicationDate")
        if f'date-released: "{publication_date}"' not in citation:
            errors.append("CITATION.cff does not record the authorized publication date")
        if "release candidate" in citation.lower() or CANDIDATE_VERSION in citation:
            errors.append("CITATION.cff still contains release-candidate claims")
        readme = (root / "README.md").read_text(encoding="utf-8")
        if CANDIDATE_VERSION in readme or "has not been published" in readme.lower():
            errors.append("README.md still describes the ontology as an unpublished release candidate")
        current_status_files = (
            "CONTRIBUTING.md", "DESIGN.md", "GOVERNANCE.md",
            "docs/EVALUATION_AND_RELEASE_READINESS.md",
            "docs/RELEASE_PROCESS.md",
        )
        for relative in current_status_files:
            text = (root / relative).read_text(encoding="utf-8")
            if CANDIDATE_VERSION in text:
                errors.append(f"{relative} still names the pre-release candidate as current state")
        issued_token = f'dcterms:issued "{publication_date}"^^xsd:date'
        semantic_files = [
            *root.glob("ontology/*.ttl"), *root.glob("vocab/*.ttl"),
        ]
        for path in semantic_files:
            if issued_token not in path.read_text(encoding="utf-8"):
                errors.append(f"publication date is not reflected in {path.relative_to(root)}")
        for relative in ("w3id/.htaccess", "w3id/README.md"):
            text = (root / relative).read_text(encoding="utf-8").lower()
            if "release-candidate" in text or "nopublish=true" in text:
                errors.append(f"{relative} still contains pre-authorization wording")

    route_data = json.loads((root / "config/w3id-routes.json").read_text(encoding="utf-8"))
    if route_data.get("root") != EXPECTED_ROOT:
        errors.append("W3ID route root drift")
    destination = route_data.get("destinationBase")
    if not isinstance(destination, str) or not destination.startswith("https://"):
        errors.append("publication destination must be a concrete HTTPS base")
    route_paths = {record.get("path") for record in route_data.get("routes", []) if isinstance(record, dict)}
    expected_routes = {
        "ontology/{version}",
        "ontology/{module}/{version}",
        "vocab/{scheme}/{concept}",
        "vao/0.4.0",
        "vao/0.4.0/schema/{artifact}",
        "vao/0.4.0/context.jsonld",
        "vao/0.4.0/vocabulary",
        "vao/0.4.0/modavis-mapping",
        "vao/profile/{profile}/0.4.0",
        "vao/vocab/{path}",
    }
    if not expected_routes.issubset(route_paths):
        errors.append("W3ID registry does not cover every prepared MODAVIS/VAO identifier family")
    if route_data.get("requirements", {}).get("unknownTermResponse") != 404:
        errors.append("W3ID registry must explicitly return 404 for unknown vocabulary terms")

    rules = (root / "w3id/.htaccess").read_text(encoding="utf-8")
    if "__PUBLICATION_BASE__" in rules or "example.com" in rules:
        errors.append("concrete W3ID rules contain a placeholder destination")
    if destination and destination not in rules:
        errors.append("W3ID rules do not use the configured publication destination")
    for token in ("0\\.1\\.0", "text/turtle", "application/ld\\+json", "application/rdf\\+xml", "R=303"):
        if token not in rules:
            errors.append(f"W3ID rules are missing required token: {token}")

    lock = (root / "requirements-dev.txt").read_text(encoding="utf-8")
    if "--hash=sha256:" not in lock or "# This file was autogenerated by uv" not in lock:
        errors.append("development dependencies are not transitively hash-locked")
    for workflow in root.glob(".github/workflows/*.yml"):
        workflow_text = workflow.read_text(encoding="utf-8")
        if "pip install" in workflow_text and "--require-hashes -r requirements-dev.txt" not in workflow_text:
            errors.append(f"{workflow.relative_to(root)} installs dependencies without the hash lock")

    return errors, blockers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--publication-ready", action="store_true")
    args = parser.parse_args()
    errors, blockers = check(args.root.resolve())
    result = {
        "preparation": "PASS" if not errors else "FAIL",
        "publicationReady": not errors and not blockers,
        "errors": errors,
        "blockers": blockers,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if errors or (args.publication_ready and blockers) else 0


if __name__ == "__main__":
    raise SystemExit(main())
