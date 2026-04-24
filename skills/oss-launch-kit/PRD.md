# oss-launch-kit PRD

## Overview
`oss-launch-kit` is an advanced OpenDirectory skill that turns a public GitHub repo URL into a grounded launch package for open-source projects.

The v1 output is a single Markdown document containing:
- executive summary & launch readiness
- channel orchestration (where to launch & why)
- coordinated launch timeline
- Show HN draft (conditionally included)
- Product Hunt draft (conditionally included)
- 5 Reddit post variants (focus on feedback for weak repos)
- Twitter/X thread
- full confidence notes & assumptions

## Problem Statement
Open-source maintainers often know how to build and ship the product, but not how to package it for launch. The hardest part is not writing generic marketing copy; it is translating a repo’s real signal into channel-specific content that is honest, specific, and usable.

This skill solves that by taking one repo URL and generating launch assets that a maintainer can post or adapt with minimal editing.

### Why a repo URL is enough for v1
A GitHub repo already exposes the highest-signal inputs for launch copy:
- repository name and description
- README content
- topics and homepage
- primary language
- stars, forks, license
- optional release metadata

That is enough to infer what the project is, who it is for, what problem it solves, and what makes it worth announcing. V1 does not need deeper scraping or user-provided briefs.

### Why this is better scoped than the previous FAQ attempt
The closed `api-error-to-faq-builder` idea tried to infer support content from noisy inputs and broad product repos, which made hallucination and generic output more likely.

`oss-launch-kit` is narrower in three ways:
- input is a single public repo with structured metadata
- output is a bounded launch kit, not open-ended support material
- the skill can stay grounded in the repo’s own README and metadata

That makes the challenge more mergeable and easier to validate.

## Goals
- Analyze repo context to determine appropriate launch channels and project maturity.
- Generate grounded, channel-aware launch assets.
- Provide a coordinated, day-by-day launch strategy.
- Minimize hallucinations and unsupported claims.
- Produce output that is directly usable for OSS launches.
- Explicitly flag low-confidence areas when the README or metadata is sparse.

## Non-Goals
- No direct posting to Product Hunt, Reddit, HN, or X.
- No scraping of private sites.
- No invented traction, testimonials, users, or metrics.
- No attempt to infer hidden business strategy or audience beyond available evidence.

## User Input Contract
### Required CLI input
- `--repo-url <url>`: public GitHub repository URL.

### Optional CLI inputs
- `--output <path>`: write Markdown to a file instead of stdout.
  - default: `launch-kit.md`
- `--include-release-info`: fetch latest release metadata if available.
  - default: off
- `--max-reddit-variants <n>`: override the default 5 post variants.
  - default: `5`

### Environment variables
- `GITHUB_TOKEN`: optional, used to raise GitHub API rate limits.
- `OPENAI_API_KEY` or equivalent model credentials only if the implementation uses a hosted LLM.

### Validation rules
- Repo URL must resolve to a public GitHub repository.
- Invalid or private repos should fail with a clear message.
- If README is missing, the skill should continue with lowered confidence and flag the gap.

## Output Contract
The output must be a single Markdown document with stable headings.

### Required structure
1. `# Launch Strategy for <repo>`
2. `## Executive Summary & Launch Readiness`
3. `## Channel Orchestration (Where to launch & Why)`
4. `## Coordinated Launch Timeline`
5. `## Show HN Draft` (Conditional)
6. `## Product Hunt Draft` (Conditional)
7. `## Reddit Drafts`
8. `## Twitter/X Thread`
9. `## Full Confidence Notes & Assumptions`

### Content expectations
- Repo summary should cite only verified repo facts.
- Messaging brief should explain problem, solution, audience, and evidence.
- Show HN should be direct, technical, and not salesy.
- Product Hunt should include a tagline, description, and maker-comment style copy.
- Reddit should provide 5 variants with subreddit-fit notes.
- Twitter/X should be concise and evidence-based.
- Launch plan should be practical, day-based, and channel-aware.
- Low-confidence areas must explicitly list anything inferred rather than verified.

## Data Sources
### Essential
- repo name
- repo description
- README
- topics
- homepage
- primary language
- stars
- forks
- license

### Optional
- latest release metadata
- release notes
- repo archived/fork status
- README badges if easily parsed

### Priority order
1. README
2. repo description
3. topics and homepage
4. language, stars, forks, license
5. optional release info

## Success Criteria
- Launch assets feel specific to the repo, not generic.
- No fabricated claims.
- The user can use the drafts with light editing.
- Weak repos still produce honest output with confidence notes.
