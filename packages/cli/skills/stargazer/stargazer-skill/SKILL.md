---
name: stargazer-deep-extractor
description: Advanced 5-tier OSINT scraper for extracting GitHub stargazer emails. Use this skill when a user wants to scrape, extract, or download stargazers from a GitHub repository.
---

# Stargazer Deep Extractor Skill

This skill provides a highly detailed, script-like workflow for an AI Agent to extract GitHub stargazers and their email addresses. It leverages the 5-tier Stargazer Deep Extractor toolkit (Profile API, PushEvents, GPG Keys, Patch Regex, and Global Search API) to maximize extraction yields while bypassing rate limits through multi-token rotation and asyncio semaphores.

## Tone and Formatting Constraints
- You must adopt a strictly professional, technical tone.
- Do not use emojis in your responses.
- Do not use em-dashes (use standard hyphens or colons instead).

## Workflow Execution Steps

### Step 1: Input Validation and Extraction
When a user requests a repository scrape, you must extract the exact GitHub owner and repository name.
- For a URL like `https://github.com/openai/codex`, the owner is `openai` and the repository is `codex`.
- If the user only provides `openai/codex`, split it by the slash.
- If the repository name is not provided, you must ask the user for it.

### Step 2: Interrogation and Environment Setup
If the user is running this for the first time, you must interrogate them to set up the `.env` file correctly. Ask the following questions in a point-wise format:
1. "What is the maximum number of stargazers you would like to scrape? By default, this will be the total star count of the repository."
2. "Please provide your GitHub Personal Access Tokens (PATs) as a comma-separated list."

### Step 3: Token Requirement Notice
You must remind the user about GitHub's strict rate limits and recommend the optimal number of tokens based on the repository's size. 
Provide the following advisory notice to the user:
- Less than 2,000 stars: 1 token is generally sufficient.
- 2,000 to 5,000 stars: 2 to 3 tokens are recommended.
- More than 20,000 stars: 4 or more tokens are strongly recommended.

**CRITICAL RULE**: Do not hard code this token math as a mandatory constraint. You must deliver this as a notice or recommendation. If the user decides not to follow the advice and wants to proceed with fewer tokens, you must allow them to do so and proceed with whatever they provide. Let the user use whatever they want.

### Step 4: Configuration Editing
After gathering the user's responses, you must configure the `.env` file in the execution directory (referencing `assets/.env.example` if needed).
Ensure the following variables are written to `.env`:
- `GITHUB_PATS`: Comma-separated list of the user's tokens.
- `TARGET_OWNER`: The parsed repository owner.
- `TARGET_REPO`: The parsed repository name.
- `MAX_USERS`: The user's defined limit (or the total star count).
- `MAX_CONCURRENT`: Set to 50 for optimal performance.

### Step 5: Sequence Execution
You must run the bundled scripts in the exact sequence below using the Bash tool. The JSONL checkpointing system ensures that if the process is interrupted, it can resume without losing data.

1. **Deep Extraction**: Run `python scripts/stargazer_deep_extractor.py`. This executes the 5-tier OSINT extraction. 
2. **Real-time Statistics**: Run `python scripts/count_emails.py`. This analyzes the generated JSONL file (`{TARGET_OWNER}_{TARGET_REPO}_detailed.jsonl`) to count the exact number of emails successfully found vs. null emails.
3. **CSV Conversion**: Run `python scripts/convert_to_csv.py`. This converts the final JSONL data into a structured CSV file with proper `utf-8-sig` encoding for Excel compatibility.

### Step 6: Final Transparency Report
After the sequence completes, you must be fully transparent with the user. Provide a final summary reporting:
- The total number of people fetched.
- The exact total of emails successfully extracted.
- The total number of null (hidden) emails.
- The absolute path to the final CSV deliverable.
