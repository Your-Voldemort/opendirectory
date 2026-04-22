"""Build a grounded product brief from GitHub repo context.

This is a deterministic Stage A transformer: it extracts factual signals from
repo metadata and README text, then assembles a concise launch brief that the
asset generator can safely use.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any


def _clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _strip_markdown(text: str | None) -> str:
    cleaned = text or ""
    cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\[\]", r"\1", cleaned)
    cleaned = re.sub(r"[`*_>#]", "", cleaned)
    return _clean(cleaned)


def _first_sentence(text: str) -> str:
    cleaned = _strip_markdown(text)
    if not cleaned:
        return ""
    match = re.search(r"^(.+?[.!?])(\s|$)", cleaned)
    return match.group(1).strip() if match else cleaned


def _readme_paragraphs(readme_text: str) -> list[str]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", readme_text or "")]
    return [block for block in blocks if block]


def _readme_bullets(readme_text: str) -> list[str]:
    bullets = []
    for line in (readme_text or "").splitlines():
        if re.match(r"^\s*[-*+]\s+", line):
            bullets.append(_strip_markdown(re.sub(r"^\s*[-*+]\s+", "", line)))
    return bullets


def _infer_audience(repo_context: dict[str, Any], readme_text: str) -> tuple[str, str]:
    text = f"{repo_context.get('description') or ''}\n{readme_text}".lower()
    candidates = [
        ("developers", ["developer", "developers", "devs", "engineers", "coding"]),
        ("teams", ["team", "teams", "workspace", "collaboration"]),
        ("authors and maintainers", ["maintainer", "maintainers", "author", "open source"]),
        ("data/infra users", ["api", "cli", "server", "deploy", "infra", "pipeline"]),
        ("end users", ["app", "users", "personal", "workflow"]),
    ]
    for label, keywords in candidates:
        if any(keyword in text for keyword in keywords):
            return label, "medium"
    return "unknown", "low"


def _infer_problem(repo_context: dict[str, Any], readme_text: str) -> tuple[str, str]:
    description = _strip_markdown(repo_context.get("description"))
    if description:
        return description, "medium"

    paras = _readme_paragraphs(readme_text)
    if paras:
        return _first_sentence(paras[0]), "low"

    return "Unknown from available repo metadata.", "low"


def _infer_value_prop(problem: str, key_features: list[str]) -> str:
    if key_features:
        first = key_features[0]
        return f"Solves {problem.lower()} with {first.lower()}."
    return f"Grounds launch copy in the repository's own README and metadata around {problem.lower()}."


def _extract_key_features(readme_text: str, repo_context: dict[str, Any]) -> list[str]:
    bullets = _readme_bullets(readme_text)
    features: list[str] = []
    for bullet in bullets:
        if len(features) >= 5:
            break
        if len(bullet) < 3:
            continue
        features.append(bullet)

    if not features:
        description = _strip_markdown(repo_context.get("description"))
        if description:
            features.append(description)

    return features[:5]


def _build_links(repo_context: dict[str, Any]) -> dict[str, str | None]:
    return {
        "repo": repo_context.get("repo_url"),
        "homepage": repo_context.get("homepage") or None,
        "readme_source": repo_context.get("fetched_from", {}).get("readme_api"),
    }


def build_product_brief(repo_context: dict[str, Any]) -> dict[str, Any]:
    """Convert fetched repo context into a grounded launch brief."""

    readme_text = repo_context.get("readme_text") or ""
    repo_name = repo_context.get("full_name") or repo_context.get("name") or "unknown-repo"

    problem, problem_confidence = _infer_problem(repo_context, readme_text)
    audience, audience_confidence = _infer_audience(repo_context, readme_text)
    key_features = _extract_key_features(readme_text, repo_context)
    value_prop = _infer_value_prop(problem, key_features)

    summary = _clean(repo_context.get("description"))
    if not summary:
        summary = _first_sentence(readme_text) or f"Open-source project in {repo_context.get('language') or 'unknown language'}."

    assumptions: list[str] = []
    if repo_context.get("readme_error"):
        assumptions.append(f"README issue: {repo_context['readme_error']}")
    if audience == "unknown":
        assumptions.append("Audience inferred from repo metadata only.")
    if not key_features:
        assumptions.append("No strong feature bullets extracted from README.")

    confidence = "high"
    if repo_context.get("confidence") == "low" or audience_confidence == "low" or problem_confidence == "low":
        confidence = "low"
    elif assumptions:
        confidence = "medium"

    proof_points = []
    if repo_context.get("stars") is not None:
        proof_points.append(f"{repo_context['stars']} GitHub stars")
    if repo_context.get("forks") is not None:
        proof_points.append(f"{repo_context['forks']} forks")
    if repo_context.get("topics"):
        proof_points.append("topics: " + ", ".join(repo_context.get("topics", [])[:5]))
    if repo_context.get("language"):
        proof_points.append(f"primary language: {repo_context['language']}")
    if repo_context.get("license"):
        proof_points.append(f"license: {repo_context['license']}")

    return {
        "repo_name": repo_name,
        "one_line_summary": summary,
        "audience": audience,
        "problem_solved": problem,
        "value_proposition": value_prop,
        "key_proof_points": proof_points,
        "key_features": key_features,
        "links": _build_links(repo_context),
        "confidence": confidence,
        "assumptions": assumptions,
        "source_confidence": {
            "problem": problem_confidence,
            "audience": audience_confidence,
            "repo_context": repo_context.get("confidence", "low"),
        },
    }


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python build_product_brief.py <repo-context-json>")

    with open(sys.argv[1], "r", encoding="utf-8") as handle:
        repo_context = json.load(handle)

    brief = build_product_brief(repo_context)
    print(json.dumps(brief, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
