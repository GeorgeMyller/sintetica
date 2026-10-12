import crypto from 'node:crypto';
import nodeFs from 'node:fs';
import path from 'node:path';

/**
 * Subconjunto do `node:fs` usado na escrita. Os testes trocam por uma versão que falha.
 * @typedef {{
 *   existsSync: (p: string) => boolean,
 *   readFileSync: (p: string) => Buffer,
 *   writeFileSync: (p: string, data: Buffer | string, opts?: { mode?: number }) => void,
 *   renameSync: (from: string, to: string) => void,
 *   unlinkSync: (p: string) => void,
 *   mkdirSync: (p: string) => void,
 *   rmdirSync: (p: string) => void,
 *   chmodSync: (p: string, mode: number) => void,
 * }} FsApi
 */

/** @type {FsApi} */
export const realFs = {
  existsSync: (p) => nodeFs.existsSync(p),
  readFileSync: (p) => nodeFs.readFileSync(p),
  writeFileSync: (p, data, opts) => nodeFs.writeFileSync(p, data, opts),
  renameSync: (from, to) => nodeFs.renameSync(from, to),
  unlinkSync: (p) => nodeFs.unlinkSync(p),
  mkdirSync: (p) => nodeFs.mkdirSync(p),
  rmdirSync: (p) => nodeFs.rmdirSync(p),
  chmodSync: (p, mode) => nodeFs.chmodSync(p, mode),
};

/**
 * @param {Buffer | string} data
 * @returns {string} SHA-256 em hexadecimal
 */
export function sha256(data) {
  return crypto.createHash('sha256').update(data).digest('hex');
}

/**
 * @typedef {{ type: 'created', path: string }
 *   | { type: 'replaced', path: string, before: Buffer }
 *   | { type: 'renamed', from: string, to: string }
 *   | { type: 'dir', path: string }} Entry
 */

let counter = 0;

/**
 * Escrita atômica com diário de desfazer (D-07): se algo falhar, `rollback` deixa o projeto
 * como estava antes desta execução.
 */
export class Journal {
  /** @param {FsApi} [fs] */
  constructor(fs = realFs) {
    this.fs = fs;
    /** @type {Entry[]} */
    this.entries = [];
  }

  /** @param {string} dir */
  ensureDir(dir) {
    if (this.fs.existsSync(dir)) return;
    this.ensureDir(path.dirname(dir));
    this.fs.mkdirSync(dir);
    this.entries.push({ type: 'dir', path: dir });
  }

  /**
   * @param {string} file caminho absoluto
   * @param {Buffer | string} data
   * @param {number} [mode]
   */
  write(file, data, mode = 0o644) {
    this.ensureDir(path.dirname(file));
    const before = this.fs.existsSync(file) ? this.fs.readFileSync(file) : null;
    counter += 1;
    const tmp = `${file}.tmp-${process.pid}-${counter}`;
    try {
      this.fs.writeFileSync(tmp, data, { mode });
      this.fs.chmodSync(tmp, mode);
      this.fs.renameSync(tmp, file);
    } catch (err) {
      if (this.fs.existsSync(tmp)) this.fs.unlinkSync(tmp);
      throw err;
    }
    this.entries.push(before ? { type: 'replaced', path: file, before } : { type: 'created', path: file });
  }

  /**
   * @param {string} from
   * @param {string} to
   */
  rename(from, to) {
    this.fs.renameSync(from, to);
    this.entries.push({ type: 'renamed', from, to });
  }

  /** Desfaz tudo, do último passo ao primeiro. Erros no desfazer são ignorados. */
  rollback() {
    for (const entry of [...this.entries].reverse()) {
      try {
        if (entry.type === 'created') this.fs.unlinkSync(entry.path);
        else if (entry.type === 'replaced') this.fs.writeFileSync(entry.path, entry.before);
        else if (entry.type === 'renamed') this.fs.renameSync(entry.to, entry.from);
        else this.fs.rmdirSync(entry.path);
      } catch {
        // segue desfazendo o restante
      }
    }
    this.entries = [];
  }
}
