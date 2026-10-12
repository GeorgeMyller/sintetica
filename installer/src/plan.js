import fs from 'node:fs';
import path from 'node:path';

import { sha256 } from './files.js';
import { LAUNCHER, LAUNCHER_CMD, RUNTIME_DIR, findWheel, launcherCmd, launcherSh, wheelName } from './runtime.js';

export const SKILLS = [
  'sintetica-start',
  'sintetica-schema',
  'sintetica-sample',
  'sintetica-generate',
  'sintetica-eval',
];
export const SKILL_ROOTS = ['.agents/skills', '.claude/skills'];
export const POLICY = '.sintetica/policy.json';
export const STATE = '.sintetica/state.json';
export const MANIFEST = '.sintetica/install-manifest.json';

/**
 * @typedef {'skill' | 'launcher' | 'wheel' | 'policy'} Kind
 * @typedef {{ path: string, content: Buffer, mode: number, kind: Kind, skill?: string }} Desired
 * @typedef {'criar' | 'igual' | 'substituir' | 'perguntar' | 'preservar' | 'recuperar'} Action
 */

/**
 * Arquivos que o instalador quer no projeto. Caminhos relativos com `/` (D-05).
 * @param {string} packageDir pasta do pacote npm
 * @param {string} version
 * @returns {{ files: Desired[], wheel: boolean }}
 */
export function desiredFiles(packageDir, version) {
  /** @type {Desired[]} */
  const files = [];
  for (const skill of SKILLS) {
    const content = fs.readFileSync(path.join(packageDir, 'skills', skill, 'SKILL.md'));
    for (const root of SKILL_ROOTS) {
      files.push({ path: `${root}/${skill}/SKILL.md`, content, mode: 0o644, kind: 'skill', skill });
    }
  }
  files.push({ path: LAUNCHER, content: Buffer.from(launcherSh(version)), mode: 0o755, kind: 'launcher' });
  files.push({ path: LAUNCHER_CMD, content: Buffer.from(launcherCmd(version)), mode: 0o644, kind: 'launcher' });
  const wheel = findWheel(packageDir, version);
  if (wheel) {
    files.push({
      path: `${RUNTIME_DIR}/${wheelName(version)}`,
      content: fs.readFileSync(wheel),
      mode: 0o644,
      kind: 'wheel',
    });
  }
  files.push({
    path: POLICY,
    content: fs.readFileSync(path.join(packageDir, 'templates', 'policy.json')),
    mode: 0o644,
    kind: 'policy',
  });
  return { files, wheel: wheel !== null };
}

/**
 * @param {Buffer} content
 * @returns {boolean} true se é um objeto JSON
 */
function isJsonObject(content) {
  try {
    const data = JSON.parse(content.toString('utf8'));
    return typeof data === 'object' && data !== null && !Array.isArray(data);
  } catch {
    return false;
  }
}

/**
 * Ação para 1 arquivo (D-05). `manifest` mapeia caminho relativo → SHA-256 instalado.
 * @param {Desired} file
 * @param {string} root
 * @param {Map<string, string>} manifest
 * @returns {Action}
 */
export function decide(file, root, manifest) {
  const target = path.join(root, ...file.path.split('/'));
  if (!fs.existsSync(target)) return 'criar';
  const current = fs.readFileSync(target);
  if (sha256(current) === sha256(file.content)) return 'igual';
  if (file.kind === 'policy') return isJsonObject(current) ? 'preservar' : 'recuperar';
  if (manifest.get(file.path) === sha256(current)) return 'substituir';
  return 'perguntar';
}
