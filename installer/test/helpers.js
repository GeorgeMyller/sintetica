import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { realFs, sha256 } from '../src/files.js';
import { install } from '../src/install.js';

/**
 * Projeto temporário com os marcadores pedidos (`AGENTS.md` vira arquivo; o resto, pasta).
 * @param {string[]} [markers]
 * @returns {string}
 */
export function tempProject(markers = []) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'sintetica-inst-'));
  for (const marker of markers) {
    const target = path.join(dir, marker);
    if (marker.endsWith('.md')) fs.writeFileSync(target, '# agentes\n');
    else fs.mkdirSync(target, { recursive: true });
  }
  return dir;
}

/**
 * Pasta com executáveis falsos de `uv` e `python3`, para usar como PATH (D-19).
 * @param {{ uv?: boolean, python?: string | null }} [opts] `python`: versão, ou null para ausente
 * @returns {NodeJS.ProcessEnv}
 */
export function fakeEnv(opts = {}) {
  const uv = opts.uv ?? true;
  const python = opts.python === undefined ? '3.12.1' : opts.python;
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'sintetica-bin-'));
  const pythonOk = python !== null && /^3\.(1\d|[2-9]\d)/.test(python);
  if (uv) {
    const find = pythonOk ? 'echo /usr/bin/python3; exit 0' : 'exit 2';
    fs.writeFileSync(
      path.join(dir, 'uv'),
      `#!/bin/sh\nif [ "$1" = "--version" ]; then echo "uv 0.6.16"; exit 0; fi\n${find}\n`,
      { mode: 0o755 },
    );
  }
  if (python !== null) {
    fs.writeFileSync(path.join(dir, 'python3'), `#!/bin/sh\necho "Python ${python}"\n`, {
      mode: 0o755,
    });
  }
  return { ...process.env, PATH: dir };
}

/**
 * Roda o instalador no processo, com a saída capturada.
 * @param {string} dir
 * @param {Partial<import('../src/install.js').InstallOptions>} [opts]
 * @returns {Promise<{ code: number, lines: string[], text: string }>}
 */
export async function runInstall(dir, opts = {}) {
  /** @type {string[]} */
  const lines = [];
  const code = await install({
    dir,
    out: (line) => lines.push(line),
    env: fakeEnv(),
    interactive: false,
    home: path.join(os.tmpdir(), 'casa-que-nao-existe'),
    ...opts,
  });
  return { code, lines, text: lines.join('\n') };
}

/**
 * Sistema de arquivos que falha na n-ésima escrita (ENOSPC).
 * @param {number} n
 * @returns {import('../src/files.js').FsApi}
 */
export function failingFs(n) {
  let calls = 0;
  return {
    ...realFs,
    writeFileSync: (p, data, o) => {
      calls += 1;
      if (calls === n) {
        const err = /** @type {NodeJS.ErrnoException} */ (new Error('sem espaço'));
        err.code = 'ENOSPC';
        err.path = p;
        throw err;
      }
      realFs.writeFileSync(p, data, o);
    },
  };
}

/**
 * Todos os arquivos da pasta, com SHA-256 e data de modificação.
 * @param {string} root
 * @returns {Map<string, { sha: string, mtime: number }>}
 */
export function snapshot(root) {
  /** @type {Map<string, { sha: string, mtime: number }>} */
  const files = new Map();
  /** @param {string} dir */
  const walk = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else {
        const rel = path.relative(root, full).split(path.sep).join('/');
        files.set(rel, { sha: sha256(fs.readFileSync(full)), mtime: fs.statSync(full).mtimeMs });
      }
    }
  };
  walk(root);
  return files;
}

/**
 * @param {string} root
 * @param {string} rel
 * @returns {string}
 */
export function read(root, rel) {
  return fs.readFileSync(path.join(root, ...rel.split('/')), 'utf8');
}

/**
 * Cópia do pacote npm numa pasta temporária, com wheel falso opcional e versão trocável.
 * @param {{ wheel?: boolean, version?: string }} [opts]
 * @returns {string}
 */
export function fakePackage(opts = {}) {
  const src = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'sintetica-pkg-'));
  fs.cpSync(path.join(src, 'skills'), path.join(dir, 'skills'), { recursive: true });
  fs.cpSync(path.join(src, 'templates'), path.join(dir, 'templates'), { recursive: true });
  const pkg = JSON.parse(fs.readFileSync(path.join(src, 'package.json'), 'utf8'));
  const version = opts.version ?? pkg.version;
  fs.writeFileSync(path.join(dir, 'package.json'), JSON.stringify({ ...pkg, version }));
  if (opts.wheel ?? true) {
    fs.mkdirSync(path.join(dir, 'runtime'));
    fs.writeFileSync(
      path.join(dir, 'runtime', `sintetica-${version}-py3-none-any.whl`),
      `wheel falso ${version}`,
    );
  }
  return dir;
}
