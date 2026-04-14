import fs from 'node:fs';
import path from 'node:path';
import matter from 'gray-matter';
import { z } from 'zod';

const skillsDir = path.join(process.cwd(), 'skills');

const frontmatterSchema = z.object({
  name: z.string(),
  description: z.string(),
  author: z.string(),
  version: z.string(),
});

const disallowedExtensions = ['.exe', '.dll', '.bat', '.zip', '.tar.gz'];
const dangerousPatterns = [
  /rm\s+-rf\s+\//,
  /curl.*\|.*bash/,
  /wget.*\|.*sh/,
  /(?<!\.)eval\(/,
  /(?<!\.)exec\(/,
];

function scanDirectory(dir: string, errors: string[]) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      scanDirectory(fullPath, errors);
    } else {
      const ext = path.extname(entry.name).toLowerCase();

      if (disallowedExtensions.includes(ext)) {
        errors.push(`Disallowed file extension found: ${fullPath}`);
        continue;
      }

      if (['.sh', '.py', '.js', '.ts'].includes(ext)) {
        const content = fs.readFileSync(fullPath, 'utf-8');
        for (const pattern of dangerousPatterns) {
          if (pattern.test(content)) {
            errors.push(`Dangerous pattern ${pattern.toString()} found in file: ${fullPath}`);
          }
        }
      }
    }
  }
}

function validateSkills() {
  if (!fs.existsSync(skillsDir)) {
    console.log('No skills directory found.');
    return;
  }

  const entries = fs.readdirSync(skillsDir, { withFileTypes: true });
  let hasErrors = false;

  for (const entry of entries) {
    if (entry.isDirectory()) {
      const skillPath = path.join(skillsDir, entry.name);
      const skillMdPath = path.join(skillPath, 'SKILL.md');
      const errors: string[] = [];

      if (!fs.existsSync(skillMdPath)) {
        errors.push(`Error: Skill '${entry.name}' is missing a SKILL.md file.`);
      } else {
        try {
          const fileContent = fs.readFileSync(skillMdPath, 'utf-8');
          const parsed = matter(fileContent);
          
          const result = frontmatterSchema.safeParse(parsed.data);
          if (!result.success) {
            errors.push(`Error: Skill '${entry.name}' has invalid frontmatter in SKILL.md: ${result.error.message}`);
          }
        } catch (err: any) {
          errors.push(`Error: Failed to parse SKILL.md for '${entry.name}': ${err.message}`);
        }
      }

      scanDirectory(skillPath, errors);

      if (errors.length > 0) {
        hasErrors = true;
        for (const error of errors) {
          console.error(error);
        }
      } else {
        console.log(`Skill '${entry.name}' is valid.`);
      }
    }
  }

  if (hasErrors) {
    console.error('\nValidation failed: One or more skills have errors.');
    process.exit(1);
  } else {
    console.log('\nAll skills are valid!');
  }
}

validateSkills();
