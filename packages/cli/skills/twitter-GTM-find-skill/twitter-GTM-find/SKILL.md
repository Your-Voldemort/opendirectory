---
name: twitter-GTM-find-Skill
description: End-to-end pipeline for scraping Twitter for GTM/DevRel tech startup jobs using Apify, and validating them against an Ideal Customer Profile (ICP) using Gemini's native Google Search Grounding. Use this skill when OpenClaw needs to find developer-first, funded startups actively hiring for GTM, DevRel, or Growth roles.
---

# Twitter GTM Find Skill

This skill provides an automated pipeline to scrape Twitter for Developer-First startups hiring GTM/DevRel roles, followed by an automatic web-search verification step to validate them against our Ideal Customer Profile (ICP).

## Using the Pipeline

You can run the full pipeline using the executable Node.js project bundled in `scripts/`. 

```bash
cd scripts
npm install
npx ts-node src/index.ts
```

**Requirements:**
A `.env` file must be present at the workspace root with:
- `APIFY_API_TOKEN` (Apify account access)
- `GEMINI_API_KEY` (Gemini 3 Flash Preview with Search Grounding)
- `MAX_POSTS=20` (Optional limit)

## Outputs

The script handles two primary JSON files:
1. `radar-jobs.json`: The initial raw batch of tech jobs identified by the scraper.
2. `openclaw-icp-jobs.json`: The **final validated file** OpenClaw should ingest, containing only companies that passed the strict web-search evaluation.

## References

For deeper context on how the evaluation works or modifying the pipeline, read these files as needed:

- **ICP Checklist**: See [references/icp-checklist.md](references/icp-checklist.md) for the exact strict evaluation criteria (Developer-first + $100K minimum funding).
- **Gemini Search Grounding**: The pipeline (`scripts/src/icp-filter.ts`) natively uses Google Search Grounding via the `@google/generative-ai` SDK (`gemini-3-flash-preview` / `gemini-flash-latest`) to look up live funding and product data.
