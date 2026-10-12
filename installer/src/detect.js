import fs from 'node:fs';
import path from 'node:path';

/** @typedef {{ id: string, label: string, markers: string[] }} Harness */

/** Marcadores da Q51, em ordem fixa. A detecção só informa o resumo e o `state.json`. */
/** @type {Harness[]} */
export const HARNESSES = [
  { id: 'claude-code', label: 'Claude Code', markers: ['.claude'] },
  { id: 'antigravity', label: 'Antigravity', markers: ['.agents', '.agent'] },
  { id: 'cursor', label: 'Cursor', markers: ['.cursor'] },
  { id: 'gemini-cli', label: 'Gemini CLI', markers: ['.gemini'] },
  { id: 'codex', label: 'Codex', markers: ['.codex', 'AGENTS.md'] },
];

/** Pastas que o próprio instalador cria; só contam como marcador se tiverem algo além disso. */
const OWN_ROOTS = new Set(['.claude', '.agents']);

/**
 * @param {string} dir pasta do marcador (`.claude` ou `.agents`)
 * @returns {boolean} true se a pasta só tem `skills/sintetica-*` criadas pelo instalador
 */
function onlyOurSkills(dir) {
  const entries = fs.readdirSync(dir);
  if (entries.length !== 1 || entries[0] !== 'skills') return false; // vazia também conta
  const skills = path.join(dir, 'skills');
  if (!fs.statSync(skills).isDirectory()) return false;
  const names = fs.readdirSync(skills);
  return names.length > 0 && names.every((name) => name.startsWith('sintetica-'));
}

/**
 * @param {string} root raiz do projeto
 * @param {string[]} [previous] harnesses do `state.json` anterior: uma pasta que o usuário
 *   tinha vazia passa a ter só as skills do sintetica e continua valendo como marcador
 * @returns {Harness[]} harnesses detectados, na ordem de HARNESSES
 */
export function detectHarnesses(root, previous = []) {
  return HARNESSES.filter((h) =>
    h.markers.some((marker) => {
      const target = path.join(root, marker);
      if (!fs.existsSync(target)) return false;
      if (OWN_ROOTS.has(marker) && fs.statSync(target).isDirectory() && onlyOurSkills(target)) {
        return previous.includes(h.id);
      }
      return true;
    }),
  );
}
