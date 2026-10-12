import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';

import { Journal, sha256 } from '../src/files.js';
import { failingFs, tempProject } from './helpers.js';

test('sha256 em hexadecimal', () => {
  assert.equal(sha256('abc'), 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');
});

test('escrita atômica cria pastas, arquivos e modo; o desfazer volta tudo', () => {
  const root = tempProject();
  fs.writeFileSync(path.join(root, 'antigo.txt'), 'antes');
  fs.writeFileSync(path.join(root, 'policy.json'), '{');
  const journal = new Journal();
  journal.write(path.join(root, 'a', 'b', 'novo.sh'), '#!/bin/sh\n', 0o755);
  journal.write(path.join(root, 'antigo.txt'), 'depois');
  journal.rename(path.join(root, 'policy.json'), path.join(root, 'policy.json.bak'));
  assert.equal(fs.statSync(path.join(root, 'a', 'b', 'novo.sh')).mode & 0o777, 0o755);
  assert.equal(fs.readFileSync(path.join(root, 'antigo.txt'), 'utf8'), 'depois');
  assert.deepEqual(fs.readdirSync(path.join(root, 'a', 'b')), ['novo.sh']);
  journal.rollback();
  assert.deepEqual(fs.readdirSync(root).sort(), ['antigo.txt', 'policy.json']);
  assert.equal(fs.readFileSync(path.join(root, 'antigo.txt'), 'utf8'), 'antes');
  assert.equal(journal.entries.length, 0);
});

test('falha na escrita não deixa arquivo temporário', () => {
  const root = tempProject();
  const journal = new Journal(failingFs(1));
  assert.throws(() => journal.write(path.join(root, 'x.txt'), 'dado'), /sem espaço/);
  assert.deepEqual(fs.readdirSync(root), []);
});

test('erro no desfazer não interrompe o restante', () => {
  const root = tempProject();
  const journal = new Journal();
  journal.write(path.join(root, 'um.txt'), '1');
  journal.write(path.join(root, 'dois.txt'), '2');
  fs.unlinkSync(path.join(root, 'dois.txt'));
  journal.rollback();
  assert.deepEqual(fs.readdirSync(root), []);
});
