# Contributing to OpenDirectory

Thank you for your interest in contributing to OpenDirectory. This project aims to build a universal registry for AI Agent Skills. We welcome contributions in the form of new skills, bug fixes, and feature enhancements.

**Contributor Rewards:** We truly appreciate our open-source community. To say thank you, **top contributors will receive free exclusive OpenDirectory merchandise and t-shirts!** Whether you are submitting highly requested skills, and fixing core bugs, your efforts will be rewarded.

## Adding a New Skill

To add a new skill to the registry, follow these steps:

1. Create a new directory in the skills/ folder. The directory name should be the name of your skill (e.g., my-awesome-skill).
2. Create a SKILL.md file inside your new directory.
3. Add the required YAML frontmatter to the top of the SKILL.md file.

### Mandatory Skill Structure

Every skill must have a SKILL.md file with the following frontmatter structure:

```markdown
---
name: my-awesome-skill
description: A brief description of what the skill does.
author: your-username
version: 0.0.1
---

# My Awesome Skill

Detailed instructions for the AI agent on how to use this skill.
```

The frontmatter must include the name, description, author, and version fields. The name should match the directory name.

## Local Development and Testing

Before submitting a Pull Request, you must test your skill locally to ensure it functions correctly with the CLI.

### Prerequisites

- Node.js (v18 or higher)
- pnpm

### Setup

1. Clone the repository.
2. Install dependencies:
   ```bash
   pnpm install
   ```
3. Build the project:
   ```bash
   pnpm run build
   ```

### Testing Your Skill Locally

After building the project, you can run the local version of the CLI to verify your skill appears in the list and can be installed correctly.

1. Verify the skill is listed:
   ```bash
   node packages/cli/dist/index.js list
   ```

2. Test the installation process for a specific target (e.g., opencode):
   ```bash
   node packages/cli/dist/index.js install my-awesome-skill --target opencode
   ```

Verify that the files are placed in the expected directory (e.g., ./.opencode/skills/my-awesome-skill/).

## Pull Request Process

1. Ensure your skill follows the mandatory structure and passes local testing.
2. Submit a Pull Request with a clear description of your changes.
3. Automated Security Scan: All PRs are subject to an automated security scan. This scan checks for malicious content, including but not limited to:
   - Executable files (.exe, .bin, etc.)
   - Malicious shell scripts
   - Obfuscated code
4. Human Review: After passing the automated scan, your PR will be reviewed by a maintainer. We look for clarity in instructions, accuracy of descriptions, and overall quality.

## Code of Conduct

We expect all contributors to follow our Code of Conduct to ensure a welcoming and inclusive environment for everyone.
