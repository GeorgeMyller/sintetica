import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';

import { sha256 } from '../src/files.js';
import { POLICY, SKILLS, SKILL_ROOTS, decide, desiredFiles } from '../src/plan.js';
import { fakePackage, tempProject } from './helpers.js';

const skill = { path: '.claude/skills/sintetica-start/SKILL.md', content: Buffer.from('novo'), mode: 0o644, kind: /** @type {const} */ ('skill'), skill: 'sintetica-start' };
const policy = { path: POLICY, content: Buffer.from('{"a":1}'), mode: 0o644, kind: /** @type {const} */ ('policy') };

/**
 * @param {string} root
 * @param {string} rel
 * @param {string} text
 */
function put(root, rel, text) {
  const file = path.join(root, ...rel.split('/'));
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, text);
}

test('arquivos desejados: 10 skills, 2 lançadores, wheel e política', () => {
  const { files, wheel } = desiredFiles(fakePackage(), '0.1.0');
  assert.equal(wheel, true);
  assert.equal(files.filter((f) => f.kind === 'skill').length, SKILLS.length * SKILL_ROOTS.length);
  assert.deepEqual(
    files.filter((f) => f.kind !== 'skill').map((f) => f.path),
    [
      '.sintetica/bin/sintetica',
      '.sintetica/bin/sintetica.cmd',
      '.sintetica/runtime/sintetica-0.1.0-py3-none-any.whl',
      '.sintetica/policy.json',
    ],
  );
  assert.equal(files.find((f) => f.path === '.sintetica/bin/sintetica')?.mode, 0o755);
  assert.equal(desiredFiles(fakePackage({ wheel: false }), '0.1.0').wheel, false);
});

test('as 6 ações do plano', () => {
  const root = tempProject();
  const empty = new Map();
  assert.equal(decide(skill, root, empty), 'criar');
  put(root, skill.path, 'novo');
  assert.equal(decide(skill, root, empty), 'igual');
  put(root, skill.path, 'versão antiga instalada');
  assert.equal(decide(skill, root, new Map([[skill.path, sha256('versão antiga instalada')]])), 'substituir');
  assert.equal(decide(skill, root, empty), 'perguntar');
  // No manifest, mas editado depois da instalação: é do usuário.
  assert.equal(decide(skill, root, new Map([[skill.path, sha256('outro conteúdo')]])), 'perguntar');
  put(root, POLICY, '{"cost_ceiling_usd": 9}');
  assert.equal(decide(policy, root, new Map([[POLICY, sha256('x')]])), 'preservar');
  put(root, POLICY, '{ corrompido');
  assert.equal(decide(policy, root, empty), 'recuperar');
  put(root, POLICY, '[1, 2]');
  assert.equal(decide(policy, root, empty), 'recuperar');
});
