import * as fs from 'node:fs/promises';
import * as path from 'node:path';
import * as os from 'node:os';

export function resolvePath(p: string): string {
  if (p.startsWith('~/') || p === '~') {
    return path.resolve(p.replace(/^~/, os.homedir()));
  }
  return path.resolve(p);
}

export async function safeWriteFile(filePath: string, content: string): Promise<void> {
  const resolvedPath = resolvePath(filePath);
  const dir = path.dirname(resolvedPath);
  await fs.mkdir(dir, { recursive: true });
  await fs.writeFile(resolvedPath, content, 'utf-8');
}

export async function safeAppendFile(filePath: string, content: string): Promise<void> {
  const resolvedPath = resolvePath(filePath);
  const dir = path.dirname(resolvedPath);
  await fs.mkdir(dir, { recursive: true });

  try {
    const existingContent = await fs.readFile(resolvedPath, 'utf-8');
    if (existingContent.includes(content)) {
      return;
    }
    
    const prefix = existingContent.length > 0 && !existingContent.endsWith('\n') ? '\n' : '';
    await fs.appendFile(resolvedPath, prefix + content, 'utf-8');
  } catch (error: any) {
    if (error.code === 'ENOENT') {
      await fs.writeFile(resolvedPath, content, 'utf-8');
    } else {
      throw error;
    }
  }
}

export async function updateHermesConfig(): Promise<void> {
  const configPath = resolvePath('~/.hermes/config.yaml');
  
  try {
    let content = await fs.readFile(configPath, 'utf-8');
    
    if (!content.includes('skills:')) {
      const prefix = content.length > 0 && !content.endsWith('\n') ? '\n' : '';
      content += prefix + 'skills:\n  external_dirs:\n    - "./.hermes/skills"\n';
    } else if (!content.includes('external_dirs:')) {
      content = content.replace(/(skills:\s*\n)/, '$1  external_dirs:\n    - "./.hermes/skills"\n');
    } else if (!content.includes('./.hermes/skills')) {
      content = content.replace(/(external_dirs:\s*\n)/, '$1    - "./.hermes/skills"\n');
    }
    
    await fs.writeFile(configPath, content, 'utf-8');
  } catch (error: any) {
    if (error.code === 'ENOENT') {
      const initialContent = `skills:\n  external_dirs:\n    - "./.hermes/skills"\n`;
      await safeWriteFile('~/.hermes/config.yaml', initialContent);
    } else {
      throw error;
    }
  }
}
