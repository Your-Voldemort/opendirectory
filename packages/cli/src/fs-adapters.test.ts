import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as fs from 'node:fs/promises';
import * as path from 'node:path';
import * as os from 'node:os';
import { resolvePath, safeWriteFile, safeAppendFile } from './fs-adapters';

describe('fs-adapters', () => {
  let tempDir: string;

  beforeEach(async () => {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'fs-adapters-test-'));
  });

  afterEach(async () => {
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  describe('resolvePath', () => {
    it('should resolve ~ to home directory', () => {
      const home = os.homedir();
      expect(resolvePath('~/foo/bar')).toBe(path.join(home, 'foo/bar'));
      expect(resolvePath('~')).toBe(home);
    });

    it('should resolve absolute paths', () => {
      const absPath = path.resolve('/foo/bar');
      expect(resolvePath('/foo/bar')).toBe(absPath);
    });

    it('should resolve relative paths', () => {
      const relPath = path.resolve('foo/bar');
      expect(resolvePath('foo/bar')).toBe(relPath);
    });
  });

  describe('safeWriteFile', () => {
    it('should create directory and write file', async () => {
      const filePath = path.join(tempDir, 'nested', 'dir', 'test.txt');
      await safeWriteFile(filePath, 'hello world');
      
      const content = await fs.readFile(filePath, 'utf-8');
      expect(content).toBe('hello world');
    });

    it('should overwrite existing file', async () => {
      const filePath = path.join(tempDir, 'test.txt');
      await safeWriteFile(filePath, 'hello world');
      await safeWriteFile(filePath, 'new content');
      
      const content = await fs.readFile(filePath, 'utf-8');
      expect(content).toBe('new content');
    });
  });

  describe('safeAppendFile', () => {
    it('should create file if it does not exist', async () => {
      const filePath = path.join(tempDir, 'nested', 'test.txt');
      await safeAppendFile(filePath, 'hello world');
      
      const content = await fs.readFile(filePath, 'utf-8');
      expect(content).toBe('hello world');
    });

    it('should append to existing file', async () => {
      const filePath = path.join(tempDir, 'test.txt');
      await safeWriteFile(filePath, 'line 1\n');
      await safeAppendFile(filePath, 'line 2');
      
      const content = await fs.readFile(filePath, 'utf-8');
      expect(content).toBe('line 1\nline 2');
    });

    it('should add newline if existing file does not end with one', async () => {
      const filePath = path.join(tempDir, 'test.txt');
      await safeWriteFile(filePath, 'line 1');
      await safeAppendFile(filePath, 'line 2');
      
      const content = await fs.readFile(filePath, 'utf-8');
      expect(content).toBe('line 1\nline 2');
    });

    it('should not append if content already exists', async () => {
      const filePath = path.join(tempDir, 'test.txt');
      await safeWriteFile(filePath, 'existing content\nmore stuff');
      await safeAppendFile(filePath, 'existing content');
      
      const content = await fs.readFile(filePath, 'utf-8');
      expect(content).toBe('existing content\nmore stuff');
    });
  });
});
