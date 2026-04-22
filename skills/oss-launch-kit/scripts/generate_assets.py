"""Generate launch assets from a product brief.

This module renders a stable Markdown launch kit grounded in repo facts.
It includes Show HN, Product Hunt, Reddit variants, Twitter/X, and a first-week
community plan, while preserving explicit low-confidence warnings.
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


def _shorten(text: str, limit: int) -> str:
    text = _clean(text)
    if len(text) <= limit:
        return text
    truncated = text[:limit].rstrip()
    if " " in truncated:
        truncated = truncated[: truncated.rfind(" ")].rstrip()
    return truncated + "..."


def _repo_slug(brief: dict[str, Any]) -> str:
    return _clean(brief.get("repo_name") or "unknown-repo")


def _title_case(text: str) -> str:
    words = text.split()
    return " ".join(word if len(word) <= 3 else word[:1].upper() + word[1:] for word in words)


def _strip_trailing_period(text: str) -> str:
    return text[:-1] if text.endswith(".") else text


def _canonical_summary(brief: dict[str, Any]) -> str:
    summary = _strip_markdown(brief.get("one_line_summary"))
    if summary:
        return _strip_trailing_period(summary)

    problem = _strip_markdown(brief.get("problem_solved"))
    if problem:
        return _strip_trailing_period(problem)

    return "an open-source project"


def _choose_show_hn_title(brief: dict[str, Any]) -> str:
    repo_name = _repo_slug(brief)
    summary = _canonical_summary(brief)
    audience = _strip_markdown(brief.get("audience"))

    candidates = []
    if summary and audience and audience != "unknown":
        candidates.append(f"Show HN: {repo_name} - {summary} for {audience}")
    if summary:
        candidates.append(f"Show HN: {repo_name} - {summary}")
    candidates.append(f"Show HN: {repo_name}")

    for candidate in candidates:
        if len(candidate) <= 72:
            return candidate
    return candidates[-1]


def _should_write_body(brief: dict[str, Any]) -> bool:
    confidence = _clean(brief.get("confidence"))
    proof_points = brief.get("key_proof_points") or []
    features = brief.get("key_features") or []

    if confidence == "low":
        return False
    if len(proof_points) < 2:
        return False
    if not features:
        return False
    return True


def _intro_line(brief: dict[str, Any]) -> str:
    repo_name = _repo_slug(brief)
    summary = _canonical_summary(brief)
    audience = _strip_markdown(brief.get("audience"))
    if audience and audience != "unknown":
        return _shorten(f"I built {repo_name} because I wanted a clearer way to serve {audience} who need {summary.lower()}.", 220)
    return _shorten(f"I built {repo_name} because I wanted a clearer way to package {summary.lower()} as a launchable OSS project.", 220)


def _core_explanation(brief: dict[str, Any]) -> str:
    features = [_strip_markdown(feature) for feature in (brief.get("key_features") or [])[:3]]
    proof_points = brief.get("key_proof_points") or []
    lines: list[str] = []
    if features:
        lines.append("The launch kit focuses on " + ", ".join(features) + ".")
    if proof_points:
        lines.append("I grounded the copy in repo signals like " + "; ".join(proof_points[:3]) + ".")
    if not lines:
        lines.append("I kept the draft anchored to the repo README and GitHub metadata.")
    return " ".join(lines)


def _feedback_ask(brief: dict[str, Any]) -> str:
    assumptions = brief.get("assumptions") or []
    if assumptions:
        return _shorten(
            "If the README is too thin or the audience is off, I’d especially appreciate feedback on the framing and where the launch copy feels too broad.",
            220,
        )
    return _shorten(
        "Happy to hear whether the framing feels accurate and what launch angle you’d expect from a repo like this.",
        220,
    )


def _low_confidence_note(brief: dict[str, Any]) -> str:
    confidence = _clean(brief.get("confidence"))
    assumptions = brief.get("assumptions") or []
    if confidence == "low" or assumptions:
        notes = [f"Confidence: {confidence or 'unknown'}"]
        if assumptions:
            notes.append("Assumptions: " + "; ".join(assumptions[:3]).rstrip("."))
        return "\n".join(f"- {note}" for note in notes)
    return "- Confidence: high"


def _is_low_confidence(brief: dict[str, Any]) -> bool:
    return _clean(brief.get("confidence")) == "low" or bool(brief.get("assumptions"))


def _low_confidence_edit_note() -> str:
    return "Edit before posting: this repo context is sparse, so tighten the copy after reviewing the README and repo signals."


def _normalize_phrase(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", _clean(text).lower()).strip()


def _phrase_overlap(a: str, b: str) -> bool:
    a_words = {word for word in _normalize_phrase(a).split() if len(word) > 2}
    b_words = {word for word in _normalize_phrase(b).split() if len(word) > 2}
    if not a_words or not b_words:
        return False
    return len(a_words & b_words) >= 3


def _is_marketing_heavy(text: str) -> bool:
    normalized = _normalize_phrase(text)
    signals = [
        "worlds best",
        "ultimate",
        "powerful",
        "all in one",
        "beautiful",
        "magical",
        "supercharge",
        "next generation",
        "revolutionary",
        "seamless",
        "unlock",
        "delight",
        "built for teams",
        "move faster",
    ]
    return any(signal in normalized for signal in signals)


def _ph_repo_category(brief: dict[str, Any]) -> str:
    text = " ".join(
        part
        for part in [
            _strip_markdown(brief.get("problem_solved")),
            _strip_markdown(brief.get("one_line_summary")),
            _strip_markdown(brief.get("value_proposition")),
        ]
        if part
    ).lower()
    if any(term in text for term in ["framework", "sdk"]):
        return "framework"
    if any(term in text for term in ["library", "package", "module"]):
        return "library"
    if any(term in text for term in ["cli", "tool", "automation", "workflow", "build", "deploy"]):
        return "tool"
    if any(term in text for term in ["design", "css", "ui", "frontend"]):
        return "UI toolkit"
    return "open-source project"


def _render_low_confidence_note(brief: dict[str, Any]) -> str:
    note = _low_confidence_note(brief)
    if _is_low_confidence(brief):
        note += "\n" + _low_confidence_edit_note()
    return note


def _is_open_source(brief: dict[str, Any]) -> bool:
    links = brief.get("links") or {}
    return bool(_clean(links.get("repo")))


def _tagline_candidates(brief: dict[str, Any]) -> list[str]:
    summary = _canonical_summary(brief)
    audience = _strip_markdown(brief.get("audience"))
    problem = _strip_markdown(brief.get("problem_solved"))
    features = [_strip_markdown(feature) for feature in (brief.get("key_features") or [])[:3]]
    repo_name = _repo_slug(brief)
    value_prop = _strip_markdown(brief.get("value_proposition"))
    focus = features[0] if features else summary

    candidates = []
    if audience and audience != "unknown":
        candidates.append(f"Launch copy for {audience} built from repo facts")
    if problem:
        candidates.append(f"Turns {problem.lower()} into launch-ready copy")
    if value_prop:
        candidates.append(_shorten(value_prop, 60))
    if focus:
        candidates.append(_shorten(f"Built for repos about {focus.lower()}", 60))
    candidates.extend(
        [
            f"Launch assets grounded in README and metadata",
            f"Turns GitHub repos into launch copy",
            f"Helps OSS maintainers write launch-ready posts",
        ]
    )
    if repo_name:
        candidates.append(f"Launch copy for {repo_name}")
    return [candidate for candidate in candidates if candidate]


def _pick_tagline(brief: dict[str, Any]) -> str:
    candidates = []
    for candidate in _tagline_candidates(brief):
        candidate = _strip_markdown(candidate)
        if not candidate:
            continue
        if candidate.lower().startswith(_repo_slug(brief).lower()):
            continue
        if candidate.endswith(".") or candidate.endswith("?"):
            candidate = candidate[:-1]
        if len(candidate) <= 60:
            candidates.append(candidate)
    if candidates:
        return candidates[0]
    fallback = _strip_markdown(brief.get("value_proposition")) or "Launch copy grounded in repo facts"
    return _shorten(fallback, 60)


def _ph_description(brief: dict[str, Any]) -> str:
    summary = _canonical_summary(brief)
    audience = _strip_markdown(brief.get("audience"))
    features = [_strip_markdown(feature) for feature in (brief.get("key_features") or [])[:2]]
    problem = _strip_markdown(brief.get("problem_solved"))
    value_prop = _strip_markdown(brief.get("value_proposition"))
    edit_note = _low_confidence_edit_note() if _is_low_confidence(brief) else ""
    open_source_phrase = "Open source and self-hostable." if brief.get("links", {}).get("repo") else ""

    parts = []
    audience_label = audience if audience != 'unknown' else 'OSS maintainers'
    if problem and value_prop:
        parts.append(_shorten(f"For {audience_label}, it frames {problem.lower()} around {value_prop.lower()}.", 180))
    elif problem:
        parts.append(_shorten(f"For {audience_label}, it turns {problem.lower()} into launch copy.", 180))
    elif audience and audience != 'unknown':
        parts.append(_shorten(f"Built for {audience_label} who need launch copy grounded in repo facts.", 180))
    else:
        parts.append("Built for OSS maintainers who want launch copy grounded in repo facts.")

    if features and not _is_low_confidence(brief):
        parts.append("Uses signals like " + ", ".join(features) + ".")
    elif features:
        parts.append("Grounded in repo signals, not invented claims.")
    if open_source_phrase:
        parts.append(open_source_phrase)
    if edit_note:
        parts.append(edit_note)

    description = " ".join(part for part in parts if part)
    return _shorten(description, 320 if _is_low_confidence(brief) else 500)


def _maker_comment(brief: dict[str, Any]) -> str:
    repo_name = _repo_slug(brief)
    summary = _canonical_summary(brief)
    audience = _strip_markdown(brief.get("audience"))
    features = [_strip_markdown(feature) for feature in (brief.get("key_features") or [])[:3]]
    proof_points = brief.get("key_proof_points") or []
    assumptions = brief.get("assumptions") or []
    links = brief.get("links") or {}

    paragraphs = [
        _shorten(
            f"I built {repo_name} because I kept seeing open-source projects with good code but weak launch copy. The repo had enough signal to explain itself, but not enough structure to turn that signal into something launch-ready.",
            420,
        ),
        _shorten(
            f"This version starts from a GitHub repo URL, pulls the README and repository metadata, and then drafts channel-specific launch assets. For Product Hunt, that means a short tagline, a concise description, and a maker comment that stays tied to the repo rather than turning into generic marketing.",
            420,
        ),
        _shorten(
            f"I’m aiming this at {audience if audience != 'unknown' else 'OSS maintainers'} who want a practical launch package without making up traction or polishing the repo into something it is not. The current focus is {summary.lower()}, with the copy grounded in {', '.join(features) if features else 'README content and metadata' }.",
            420,
        ),
        _shorten(
            f"What it does not do yet: it does not post anywhere, it does not scrape private sources, and it does not invent proof points. If the README is thin, the output will say so instead of filling gaps with fluff.",
            420,
        ),
        _shorten(
            f"I’d love feedback on whether the framing feels honest and whether the launch copy stays useful when the repo is strong versus when the README is sparse. {('Repo: ' + links.get('repo')) if links.get('repo') else ''}",
            420,
        ),
    ]

    if proof_points:
        paragraphs.insert(
            2,
            _shorten(
                "I grounded the draft in repo signals like " + "; ".join(proof_points[:3]) + ".",
                420,
            ),
        )

    if assumptions:
        paragraphs.append("Low-confidence areas: " + "; ".join(assumptions[:3]) + ".")

    return "\n\n".join(paragraphs)


def _reddit_subreddit_candidates(brief: dict[str, Any]) -> list[tuple[str, str]]:
    audience = _strip_markdown(brief.get("audience")).lower()
    summary = _canonical_summary(brief).lower()
    language = _clean(brief.get("language") or "").lower()
    topics = {str(topic).lower() for topic in (brief.get("links") or {}).get("topics", [])}
    title = _repo_slug(brief).lower()
    candidates: list[tuple[str, str]] = []
    low_conf = _is_low_confidence(brief)

    def add(subreddit: str, context: str) -> None:
        if subreddit and subreddit.lower() not in {item[0].lower() for item in candidates}:
            candidates.append((subreddit, context))

    if low_conf:
        return [
            ("r/opensource", "open-source launch context"),
            ("r/SideProject", "general maker context"),
            ("r/programming", "developer audience"),
            ("r/devtools", "developer tools audience"),
            ("r/commandline", "command-line users"),
        ]

    if any(term in summary for term in ["cli", "tool", "automation", "build", "deploy", "developer"]):
        add("r/devtools", "developer tools audience")
    if any(term in summary for term in ["open source", "oss", "github", "repo"]):
        add("r/opensource", "open-source launch context")
    if any(term in audience for term in ["developer", "engineer", "team"]):
        add("r/programming", "developer audience")
    if any(term in summary for term in ["side project", "indie", "personal"]):
        add("r/SideProject", "maker / indie launch context")
    if any(term in topics for term in ["python", "go", "rust", "javascript", "typescript"]):
        for topic in ["python", "go", "rust", "javascript", "typescript"]:
            if topic in topics:
                add(f"r/{topic.capitalize()}", f"language-specific community for {topic}")
                break

    if "cli" in title or "terminal" in summary:
        add("r/commandline", "command-line users")
    if any(term in summary for term in ["self-host", "server", "infra", "pipeline", "ci"]):
        add("r/devops", "devops / infrastructure audience")

    fallback_pool = [
        ("r/SideProject", "general maker context"),
        ("r/opensource", "open-source launch context"),
        ("r/programming", "developer audience"),
        ("r/devtools", "developer tools audience"),
        ("r/commandline", "command-line users"),
    ]
    for subreddit, context in fallback_pool:
        add(subreddit, context)

    seen: set[str] = set()
    deduped: list[tuple[str, str]] = []
    for subreddit, context in candidates:
        key = subreddit.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append((subreddit, context))
        if len(deduped) == 5:
            break
    return deduped


def _reddit_body_for_context(brief: dict[str, Any], subreddit: str, context: str) -> str:
    repo_name = _repo_slug(brief)
    summary = _canonical_summary(brief)
    audience = _strip_markdown(brief.get("audience"))
    features = [_strip_markdown(feature) for feature in (brief.get("key_features") or [])[:3]]
    proof_points = brief.get("key_proof_points") or []
    low_conf = _is_low_confidence(brief)
    lead_feature = features[0] if features else summary
    secondary = features[1] if len(features) > 1 else "README details"

    opener = f"I built {repo_name}"
    if audience and audience != "unknown":
        opener += f" for {audience}"
    opener += f" because {summary.lower()}"

    if low_conf:
        lines = [
            f"I built {repo_name} and wanted to see if the repo story reads clearly from the README alone.",
            f"Posting this in {context} for feedback, with no extra claims attached.",
        ]
        if features:
            lines.append(f"The only concrete signal I’m leaning on is {lead_feature}.")
        lines.append("I built this myself and will only post where the subreddit rules allow self-promo.")
        lines.append(_low_confidence_edit_note())
        return "\n\n".join(lines)

    if subreddit.lower() == "r/devtools":
        lines = [
            f"{opener} and I wanted a cleaner way to turn repo facts into launch copy.",
            f"This angle fits {context}; I’m sharing it for feedback on the workflow, not as a promo blast.",
            f"The main angle here is {lead_feature}, with {secondary} as supporting context.",
        ]
    elif subreddit.lower() == "r/opensource":
        lines = [
            f"{opener} and I think the interesting part is the launch workflow, not the code itself.",
            f"I’m posting in {context} because it’s an OSS launch question first and a product post second.",
            f"The repo signals I leaned on were {', '.join(features) if features else 'README text and metadata'}.",
        ]
    elif subreddit.lower() == "r/programming":
        lines = [
            f"{opener}, and the challenge was keeping the launch copy specific without turning it into jargon.",
            f"For {context}, I’d mainly want feedback on whether the problem/solution framing is actually useful to builders.",
            f"The repo cues I used were {lead_feature} and {secondary}.",
        ]
    elif subreddit.lower() == "r/SideProject":
        lines = [
            f"{opener} as a side project I wanted to package more clearly.",
            f"I’m sharing this in {context} to compare launch framing, not to spam the thread.",
            f"The most concrete cues were {lead_feature} and {secondary}.",
        ]
    else:
        lines = [
            opener + ".",
            f"This is a fit for {context}; I’m sharing it here to get feedback, not to spam the subreddit.",
            f"It focuses on {', '.join(features) if features else 'the repo metadata and README'}.",
        ]

    if proof_points:
        lines.append("Grounded in repo facts like " + "; ".join(proof_points[:2]) + ".")
    lines.append("I built this myself and will only post where the subreddit rules allow self-promo.")
    if subreddit.lower() == "r/opensource":
        lines.append(f"Curious whether this framing would land with {context}.")
    elif subreddit.lower() == "r/SideProject":
        lines.append(f"Happy to hear if the angle feels too broad or too narrow for {context}.")
    elif subreddit.lower() in {"r/programming", "r/devtools"}:
        lines.append(f"Would this problem/solution framing feel useful to builders in {context}?")
    else:
        lines.append(f"If this fits the community, I’d appreciate feedback on the launch angle and any missing context.")
    return "\n\n".join(lines)


def generate_reddit_posts(brief: dict[str, Any]) -> list[dict[str, str]]:
    posts = []
    for subreddit, context in _reddit_subreddit_candidates(brief):
        posts.append(
            {
                "subreddit": subreddit,
                "context": context,
                "body": _reddit_body_for_context(brief, subreddit, context),
            }
        )
    return posts


def _twitter_thread_tweets(brief: dict[str, Any]) -> list[str]:
    repo_name = _repo_slug(brief)
    summary = _canonical_summary(brief)
    audience = _strip_markdown(brief.get("audience"))
    features = [_strip_markdown(feature) for feature in (brief.get("key_features") or [])[:3]]
    proof_points = brief.get("key_proof_points") or []
    repo_link = _clean((brief.get("links") or {}).get("repo"))
    low_conf = _is_low_confidence(brief)
    lead_feature = features[0] if features else summary
    secondary = features[1] if len(features) > 1 else "README and metadata"

    if low_conf:
        return [
            f"{repo_name} is still a draftable idea, but the repo context is too thin to write a confident launch thread.",
            "The safe move is to keep the copy short and avoid claims the README doesn’t support.",
            f"This version stays tied to README + GitHub metadata and tells you to edit before posting. Repo: {repo_link or 'add the repo link'}.",
        ]

    return [
        f"The launch story for {repo_name} should start with {summary.lower()}, not the implementation details.",
        f"The hard part isn’t the code; it’s explaining why {lead_feature.lower()} matters to the right audience.",
        f"This kit turns the repo’s own signals into a tighter launch story without inventing traction.",
        f"It reads the README + GitHub metadata, then drafts Show HN, Product Hunt, Reddit, and X posts that stay close to the repo. The supporting detail I’d foreground is {secondary.lower()}." + (" Evidence comes from " + "; ".join(proof_points[:2]) + "." if proof_points else ""),
        f"Feedback welcome on the repo angle: {repo_link or 'add the repo link before posting'}",
    ]


def generate_twitter_thread(brief: dict[str, Any]) -> list[dict[str, str]]:
    tweets = _twitter_thread_tweets(brief)
    return [{"tweet": tweet, "label": f"Tweet {index + 1}"} for index, tweet in enumerate(tweets)]


def _week_plan_items(brief: dict[str, Any]) -> list[tuple[str, str]]:
    repo_name = _repo_slug(brief)
    audience = _strip_markdown(brief.get("audience"))
    summary = _canonical_summary(brief)
    repo_link = _clean((brief.get("links") or {}).get("repo"))
    low_conf = _is_low_confidence(brief)

    items = [
        ("Day 0", f"Prep the launch copy, verify links, and trim anything that sounds generic for {repo_name} before posting."),
        ("Launch day", f"Post the Show HN draft, Product Hunt draft, 5 Reddit variants, and the X thread. Keep replies factual and point people to {repo_link or 'the repo'}."),
        ("Day 1-2", f"Respond to feedback, update the README if commenters point out missing context, and tighten the launch framing around {summary.lower()} for {audience if audience != 'unknown' else 'the intended audience'}."),
        ("Day 3-7", "Publish a short follow-up post or changelog note, answer questions in communities where you posted, and reuse useful feedback to improve docs, examples, or onboarding."),
    ]
    if low_conf:
        items.append(("Note", _low_confidence_edit_note()))
    return items


def generate_first_week_plan(brief: dict[str, Any]) -> list[dict[str, str]]:
    return [{"day": day, "plan": plan} for day, plan in _week_plan_items(brief)]


def generate_product_hunt(brief: dict[str, Any]) -> dict[str, str]:
    """Generate Product Hunt assets from a grounded brief."""

    repo_name = _repo_slug(brief)
    audience = _strip_markdown(brief.get("audience"))
    summary = _strip_markdown(brief.get("one_line_summary")) or _canonical_summary(brief)
    problem = _strip_markdown(brief.get("problem_solved"))
    value_prop = _strip_markdown(brief.get("value_proposition"))
    low_confidence = _is_low_confidence(brief)
    marketing_heavy = _is_marketing_heavy(summary) or _is_marketing_heavy(problem) or _is_marketing_heavy(value_prop)
    category = _ph_repo_category(brief)

    if low_confidence:
        return {
            "tagline": f"Draft: {repo_name}",
            "description": "Draft only. Not enough repo signal for a polished Product Hunt description. Edit after reviewing the README and metadata.",
            "maker_comment": "Draft only. This needs manual editing before posting.",
        }

    if audience and audience != "unknown":
        audience_phrase = audience
    else:
        audience_phrase = "OSS builders"

    if marketing_heavy:
        audience_phrase = category

    if marketing_heavy:
        tagline = f"{repo_name}: {category} for {audience_phrase}"
        description = _shorten(
            f"Built for {audience_phrase}. This draft keeps the pitch factual and avoids repeating the README’s slogans.",
            220,
        )
    else:
        tagline = f"{repo_name}: {category} for {audience_phrase}"
        description_parts = [f"Built for {audience_phrase}."]
        if problem and not _phrase_overlap(problem, summary):
            description_parts.append(f"Focuses on the repo’s core function instead of reusing README language.")
        elif summary and not _phrase_overlap(summary, problem or summary):
            description_parts.append("Keeps the pitch factual and plain.")
        else:
            description_parts.append("Keeps the pitch grounded in repo facts.")
        description = _shorten(" ".join(description_parts), 220)

    maker_comment = "Draft only. Edit before posting."
    return {
        "tagline": tagline,
        "description": description,
        "maker_comment": maker_comment,
    }


def _body_from_brief(brief: dict[str, Any]) -> str:
    intro = _intro_line(brief)
    core = _core_explanation(brief)
    ask = _feedback_ask(brief)
    confidence = _low_confidence_note(brief)

    return "\n\n".join(
        [
            intro,
            core,
            ask,
            confidence,
        ]
    )


def generate_show_hn(brief: dict[str, Any]) -> dict[str, str]:
    """Generate Show HN title and optional body from a grounded brief."""

    title = _choose_show_hn_title(brief)
    body = _body_from_brief(brief) if _should_write_body(brief) else ""
    return {
        "title": title,
        "body": body,
    }


def render_show_hn_markdown(brief: dict[str, Any]) -> str:
    """Render a stable Markdown Show HN draft."""

    show_hn = generate_show_hn(brief)
    title = show_hn["title"]
    body = show_hn["body"]

    sections = [
        "# Show HN Draft",
        "",
        "## Title",
        title,
        "",
        "## Short Intro",
        _intro_line(brief) if body else "Low-confidence repo context. Title-only draft recommended.",
        "",
        "## Core Explanation",
        _core_explanation(brief) if body else "Not enough README signal to write a reliable body.",
        "",
        "## Feedback Ask",
        _feedback_ask(brief) if body else "Please review the repo framing and README quality before posting.",
        "",
        "## Notes",
        _low_confidence_note(brief),
    ]
    return "\n".join(sections).rstrip() + "\n"


def render_product_hunt_markdown(brief: dict[str, Any]) -> str:
    """Render a stable Markdown Product Hunt draft."""

    ph = generate_product_hunt(brief)
    sections = [
        "# Product Hunt Draft",
        "",
        "## Tagline",
        ph["tagline"],
        "",
        "## Description",
        ph["description"],
        "",
        "## Maker Comment",
        ph["maker_comment"],
        "",
        "## Notes",
        _low_confidence_note(brief),
    ]
    return "\n".join(sections).rstrip() + "\n"


def generate_assets(brief: dict[str, Any]) -> dict[str, Any]:
    """Generate the first supported channel assets for oss-launch-kit."""

    return {
        "show_hn": generate_show_hn(brief),
        "product_hunt": generate_product_hunt(brief),
        "reddit": generate_reddit_posts(brief),
        "twitter_x": generate_twitter_thread(brief),
        "first_week_plan": generate_first_week_plan(brief),
        "markdown": render_show_hn_markdown(brief) + "\n" + render_product_hunt_markdown(brief),
    }


def render_reddit_markdown(brief: dict[str, Any]) -> str:
    posts = generate_reddit_posts(brief)
    sections = ["# Reddit Drafts", ""]
    for index, post in enumerate(posts, start=1):
        sections.extend(
            [
                f"## Variant {index}",
                f"Subreddit: {post['subreddit']} ({post['context']})",
                "",
                post["body"],
                "",
            ]
        )
    sections.extend(["## Notes", _render_low_confidence_note(brief)])
    return "\n".join(sections).rstrip() + "\n"


def render_twitter_markdown(brief: dict[str, Any]) -> str:
    tweets = generate_twitter_thread(brief)
    sections = ["# Twitter/X Thread", ""]
    for tweet in tweets:
        sections.extend([f"## {tweet['label']}", tweet["tweet"], ""])
    sections.extend(["## Notes", _render_low_confidence_note(brief)])
    return "\n".join(sections).rstrip() + "\n"


def render_first_week_plan_markdown(brief: dict[str, Any]) -> str:
    items = generate_first_week_plan(brief)
    sections = ["# First-Week Launch Plan", ""]
    for item in items:
        sections.extend([f"## {item['day']}", item["plan"], ""])
    sections.extend(["## Notes", _render_low_confidence_note(brief)])
    return "\n".join(sections).rstrip() + "\n"


def render_full_launch_kit_markdown(brief: dict[str, Any]) -> str:
    repo_name = _repo_slug(brief)
    summary = _canonical_summary(brief)
    audience = _strip_markdown(brief.get("audience"))
    header_lines = [
        "# Launch Kit",
        "",
        "## Repo Summary",
        repo_name,
        "",
        "## Audience",
        audience if audience and audience != "unknown" else "Unknown from available repo context",
        "",
        "## Description",
        summary,
        "",
    ]
    sections = [
        "\n".join(header_lines).rstrip(),
        render_show_hn_markdown(brief).rstrip(),
        render_product_hunt_markdown(brief).rstrip(),
        render_reddit_markdown(brief).rstrip(),
        render_twitter_markdown(brief).rstrip(),
        render_first_week_plan_markdown(brief).rstrip(),
        "# Assumptions / Low-Confidence Notes",
        _render_low_confidence_note(brief),
    ]
    return "\n\n".join(sections).rstrip() + "\n"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python generate_assets.py <product-brief-json>")

    with open(sys.argv[1], "r", encoding="utf-8") as handle:
        brief = json.load(handle)

    print(generate_assets(brief)["markdown"])


if __name__ == "__main__":
    main()
