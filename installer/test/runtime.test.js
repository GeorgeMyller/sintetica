import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';

import {
  checkRuntime,
  findWheel,
  launcherCmd,
  launcherSh,
  pythonOk,
  uvInstallHint,
  wheelName,
} from '../src/runtime.js';
import { fakeEnv, tempProject } from './helpers.js';

test('versão do Python', () => {
  assert.equal(pythonOk('Python 3.10.0'), true);
  assert.equal(pythonOk('Python 3.12.1'), true);
  assert.equal(pythonOk('Python 4.0.0'), true);
  assert.equal(pythonOk('Python 3.9.18'), false);
  assert.equal(pythonOk('Python 2.7.18'), false);
  assert.equal(pythonOk('sem versão'), false);
});

test('uv e Python pelos executáveis do PATH', () => {
  assert.deepEqual(checkRuntime({ env: fakeEnv() }), { uv: 'uv 0.6.16', python: true, ready: true });
  assert.deepEqual(checkRuntime({ env: fakeEnv({ python: '3.9.1' }) }), {
    uv: 'uv 0.6.16',
    python: false,
    ready: false,
  });
  assert.deepEqual(checkRuntime({ env: fakeEnv({ uv: false }) }), {
    uv: null,
    python: true,
    ready: false,
  });
  assert.deepEqual(checkRuntime({ env: fakeEnv({ uv: false, python: '3.8.0' }) }), {
    uv: null,
    python: false,
    ready: false,
  });
  assert.deepEqual(checkRuntime({ env: fakeEnv({ uv: false, python: null }) }), {
    uv: null,
    python: false,
    ready: false,
  });
});

test('comando de instalação do uv por sistema', () => {
  assert.match(uvInstallHint('darwin'), /install\.sh \| sh/);
  assert.match(uvInstallHint('linux'), /install\.sh/);
  assert.match(uvInstallHint('win32'), /install\.ps1/);
});

test('lançadores sh e cmd', () => {
  const sh = launcherSh('0.1.0');
  assert.ok(sh.startsWith('#!/bin/sh\n'));
  assert.match(sh, /SINTETICA_CMD="\.sintetica\/bin\/sintetica"/);
  assert.match(sh, /exec uvx --from "\$WHEEL" sintetica "\$@"/);
  assert.match(sh, /exec uv run sintetica "\$@"/);
  assert.match(sh, /sintetica-0\.1\.0-py3-none-any\.whl/);
  const cmd = launcherCmd('0.1.0');
  assert.ok(cmd.includes('\r\n'));
  assert.ok(/^[\x00-\x7F]*$/.test(cmd), 'o .cmd precisa ser ASCII');
  assert.match(cmd, /uvx --from "%WHEEL%" sintetica %\*/);
  assert.match(cmd, /uv run sintetica %\*/);
});

test('wheel empacotado ou ausente', () => {
  const pkg = tempProject();
  assert.equal(findWheel(pkg, '0.1.0'), null);
  fs.mkdirSync(path.join(pkg, 'runtime'));
  fs.writeFileSync(path.join(pkg, 'runtime', wheelName('0.1.0')), 'zip');
  assert.equal(findWheel(pkg, '0.1.0'), path.join(pkg, 'runtime', 'sintetica-0.1.0-py3-none-any.whl'));
});
