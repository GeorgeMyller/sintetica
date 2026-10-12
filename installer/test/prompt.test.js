import assert from 'node:assert/strict';
import path from 'node:path';
import { PassThrough } from 'node:stream';
import { test } from 'node:test';

import { makeAsker, outOfProject } from '../src/prompt.js';

test('respostas sim e não, --yes e sem terminal interativo', async () => {
  const answers = ['sim', 'não', ' S ', 'yes', ''];
  const ask = makeAsker({ yes: false, interactive: true, answer: async () => answers.shift() ?? '' });
  assert.deepEqual(
    [await ask('a'), await ask('b'), await ask('c'), await ask('d'), await ask('e')],
    [true, false, true, true, false],
  );
  assert.equal(await makeAsker({ yes: true, interactive: false })('x'), true);
  assert.equal(await makeAsker({ yes: false, interactive: false })('x'), false);
});

test('pergunta pelo readline do terminal', async () => {
  const input = new PassThrough();
  const output = new PassThrough();
  const ask = makeAsker({ yes: false, interactive: true, input, output });
  const pending = ask('Substituir?');
  input.write('sim\n');
  assert.equal(await pending, true);
});

test('fora de projeto: pasta pessoal e raiz do sistema', () => {
  assert.equal(outOfProject('/home/ana', '/home/ana'), true);
  assert.equal(outOfProject(path.parse(process.cwd()).root, '/home/ana'), true);
  assert.equal(outOfProject('/home/ana/projeto', '/home/ana'), false);
});
