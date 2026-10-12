import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';

import { HELP, checkNode, parseArgs } from '../src/args.js';
import { detectHarnesses } from '../src/detect.js';
import { tempProject } from './helpers.js';

test('Node abaixo de 18 é recusado com a versão encontrada e a mínima', () => {
  const message = checkNode('16.20.2');
  assert.ok(message);
  assert.match(message, /16\.20\.2/);
  assert.match(message, /18\.0\.0/);
  assert.equal(checkNode('v17.9.9') !== null, true);
  assert.equal(checkNode('18.0.0'), null);
  assert.equal(checkNode('v22.16.0'), null);
  assert.equal(checkNode('18'), null);
});

test('argumentos de install', () => {
  assert.deepEqual(parseArgs(['install'], '/p'), { command: 'install', yes: false, dir: '/p' });
  assert.deepEqual(parseArgs(['install', '--yes', '--dir', '/q'], '/p'), {
    command: 'install',
    yes: true,
    dir: '/q',
  });
  assert.deepEqual(parseArgs(['install', '-y'], '/p'), { command: 'install', yes: true, dir: '/p' });
  assert.ok('error' in parseArgs([], '/p'));
  assert.ok('error' in parseArgs(['remove'], '/p'));
  assert.ok('error' in parseArgs(['install', '--dir'], '/p'));
  assert.ok('error' in parseArgs(['install', '--force'], '/p'));
  assert.match(HELP, /npx sintetica install/);
});

test('cada marcador detecta o seu harness, em ordem fixa', () => {
  const cases = [
    [['.claude'], ['claude-code']],
    [['.agents'], ['antigravity']],
    [['.agent'], ['antigravity']],
    [['.cursor'], ['cursor']],
    [['.gemini'], ['gemini-cli']],
    [['.codex'], ['codex']],
    [['AGENTS.md'], ['codex']],
    [['.cursor', '.claude'], ['claude-code', 'cursor']],
    [[], []],
  ];
  for (const [markers, expected] of cases) {
    assert.deepEqual(
      detectHarnesses(tempProject(markers)).map((h) => h.id),
      expected,
      markers.join(','),
    );
  }
});

test('pastas só com as skills do sintetica não contam como harness', () => {
  const root = tempProject();
  fs.mkdirSync(path.join(root, '.claude', 'skills', 'sintetica-start'), { recursive: true });
  fs.mkdirSync(path.join(root, '.agents', 'skills', 'sintetica-eval'), { recursive: true });
  assert.deepEqual(detectHarnesses(root), []);
  assert.deepEqual(detectHarnesses(root, ['claude-code']).map((h) => h.id), ['claude-code']);
  fs.writeFileSync(path.join(root, '.claude', 'settings.json'), '{}');
  fs.mkdirSync(path.join(root, '.agents', 'skills', 'outra'));
  assert.deepEqual(
    detectHarnesses(root).map((h) => h.id),
    ['claude-code', 'antigravity'],
  );
  const fileMarker = tempProject();
  fs.writeFileSync(path.join(fileMarker, '.claude'), 'arquivo');
  assert.deepEqual(detectHarnesses(fileMarker).map((h) => h.id), ['claude-code']);
  const skillsFile = tempProject(['.claude']);
  fs.writeFileSync(path.join(skillsFile, '.claude', 'skills'), 'arquivo');
  assert.deepEqual(detectHarnesses(skillsFile).map((h) => h.id), ['claude-code']);
});
