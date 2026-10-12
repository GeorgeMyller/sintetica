import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

import { sha256 } from '../src/files.js';
import { SKILLS, SKILL_ROOTS } from '../src/plan.js';
import { fakeEnv, fakePackage, failingFs, read, runInstall, snapshot, tempProject } from './helpers.js';

const BIN = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', 'bin', 'sintetica.js');
const POLICY_DEFAULT = {
  telemetry: false,
  pii_premask: true,
  cost_ceiling_usd: 5.0,
  provider_priority: ['harness', 'ollama', 'external'],
  pii_custom_patterns: [],
};

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

test('instalação limpa com Claude Code e Cursor', async () => {
  const root = tempProject(['.claude', '.cursor']);
  const { code, text } = await runInstall(root, { packageDir: fakePackage() });
  assert.equal(code, 0, text);
  assert.match(text, /✓ Harnesses detectados: Claude Code, Cursor/);
  for (const dir of SKILL_ROOTS) {
    for (const skill of SKILLS) assert.ok(fs.existsSync(path.join(root, dir, skill, 'SKILL.md')));
  }
  const state = JSON.parse(read(root, '.sintetica/state.json'));
  assert.deepEqual(state, { version: '0.1.0', harnesses: ['claude-code', 'cursor'], runtime_ready: true });
  assert.deepEqual(JSON.parse(read(root, '.sintetica/policy.json')), POLICY_DEFAULT);
  assert.equal(fs.statSync(path.join(root, '.sintetica', 'bin', 'sintetica')).mode & 0o111, 0o111);
  assert.ok(fs.existsSync(path.join(root, '.sintetica', 'runtime', 'sintetica-0.1.0-py3-none-any.whl')));
  assert.match(text, new RegExp(`Instalado em ${root.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`));
  assert.match(text, /Próximo passo: no seu harness, rode \/sintetica-start/);
});

test('manifest com cada arquivo criado e o SHA-256 correto', async () => {
  const root = tempProject();
  assert.equal((await runInstall(root, { packageDir: fakePackage() })).code, 0);
  const manifest = JSON.parse(read(root, '.sintetica/install-manifest.json'));
  assert.equal(manifest.sintetica_version, '0.1.0');
  assert.match(manifest.installed_at, /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/);
  const created = [...snapshot(root).keys()].filter((p) => p !== '.sintetica/install-manifest.json');
  assert.deepEqual(manifest.files.map((/** @type {{path: string}} */ f) => f.path), created.sort());
  for (const entry of manifest.files) {
    assert.equal(entry.sha256, sha256(fs.readFileSync(path.join(root, ...entry.path.split('/')))));
  }
  assert.equal(manifest.files.length, 15); // 10 skills, 2 lançadores, wheel, política, estado
});

test('nenhum harness detectado', async () => {
  const root = tempProject();
  const { code, text } = await runInstall(root, { packageDir: fakePackage() });
  assert.equal(code, 0);
  assert.match(text, /! Nenhum harness detectado/);
  assert.deepEqual(JSON.parse(read(root, '.sintetica/state.json')).harnesses, []);
});

test('arquivo do usuário com o mesmo nome e resposta não', async () => {
  const root = tempProject(['.claude']);
  put(root, '.claude/skills/sintetica-start/SKILL.md', 'minha skill');
  /** @type {string[]} */
  const asked = [];
  const { code, text } = await runInstall(root, {
    packageDir: fakePackage(),
    ask: async (q) => {
      asked.push(q);
      return false;
    },
  });
  assert.equal(code, 0);
  assert.equal(asked.length, 1);
  assert.equal(read(root, '.claude/skills/sintetica-start/SKILL.md'), 'minha skill');
  assert.ok(!fs.existsSync(path.join(root, '.agents', 'skills', 'sintetica-start')));
  assert.match(text, /! Arquivo do usuário mantido: .*sintetica-start.*skill sintetica-start pulado/);
  assert.match(text, /✓ Skills: 4 em/);
  const manifest = JSON.parse(read(root, '.sintetica/install-manifest.json'));
  assert.ok(!manifest.files.some((/** @type {{path: string}} */ f) => f.path.includes('sintetica-start')));
});

test('resposta sim substitui o arquivo do usuário', async () => {
  const root = tempProject();
  put(root, '.agents/skills/sintetica-eval/SKILL.md', 'minha');
  const { code } = await runInstall(root, { packageDir: fakePackage(), ask: async () => true });
  assert.equal(code, 0);
  assert.notEqual(read(root, '.agents/skills/sintetica-eval/SKILL.md'), 'minha');
});

test('sem terminal interativo, a resposta é não e a saída sugere --yes', async () => {
  const root = tempProject();
  put(root, '.sintetica/bin/sintetica', 'meu lançador');
  const { code, text } = await runInstall(root, { packageDir: fakePackage() });
  assert.equal(code, 0);
  assert.equal(read(root, '.sintetica/bin/sintetica'), 'meu lançador');
  assert.match(text, /arquivo pulado/);
  assert.match(text, /rode de novo com --yes/);
});

test('--yes substitui arquivos do usuário, mas preserva a política editada', async () => {
  const root = tempProject();
  put(root, '.claude/skills/sintetica-start/SKILL.md', 'minha skill');
  put(root, '.sintetica/policy.json', '{"cost_ceiling_usd": 20}');
  const { code, text } = await runInstall(root, { packageDir: fakePackage(), yes: true });
  assert.equal(code, 0, text);
  assert.notEqual(read(root, '.claude/skills/sintetica-start/SKILL.md'), 'minha skill');
  assert.equal(read(root, '.sintetica/policy.json'), '{"cost_ceiling_usd": 20}');
});

test('runtime Python ausente: código 0, runtime_ready false e o comando de instalação', async () => {
  const root = tempProject();
  const { code, text } = await runInstall(root, {
    packageDir: fakePackage(),
    env: fakeEnv({ uv: false }),
    platform: 'linux',
  });
  assert.equal(code, 0);
  assert.equal(JSON.parse(read(root, '.sintetica/state.json')).runtime_ready, false);
  assert.match(text, /! uv não encontrado\. Instale o uv com: curl -LsSf/);
  const old = await runInstall(tempProject(), {
    packageDir: fakePackage(),
    env: fakeEnv({ python: '3.9.0' }),
  });
  assert.match(old.text, /! Python 3\.10 ou superior não encontrado/);
});

test('sem wheel empacotado, só o lançador, com aviso', async () => {
  const root = tempProject();
  const { code, text } = await runInstall(root, { packageDir: fakePackage({ wheel: false }) });
  assert.equal(code, 0);
  assert.match(text, /! Runtime: .* sem wheel empacotado/);
  assert.ok(!fs.existsSync(path.join(root, '.sintetica', 'runtime')));
});

test('segunda execução sem mudanças não altera nenhum arquivo', async () => {
  const root = tempProject(['.claude']);
  const pkg = fakePackage();
  assert.equal((await runInstall(root, { packageDir: pkg })).code, 0);
  const before = snapshot(root);
  await new Promise((resolve) => setTimeout(resolve, 20));
  assert.equal((await runInstall(root, { packageDir: pkg })).code, 0);
  assert.deepEqual(snapshot(root), before);
});

test('reinstalação com versão nova substitui só os arquivos do manifest', async () => {
  const root = tempProject();
  assert.equal((await runInstall(root, { packageDir: fakePackage({ version: '0.1.0' }) })).code, 0);
  put(root, '.sintetica/policy.json', '{"cost_ceiling_usd": 7}');
  put(root, '.agents/skills/meu-extra/SKILL.md', 'do usuário');
  const { code } = await runInstall(root, {
    packageDir: fakePackage({ version: '0.2.0' }),
    now: () => new Date('2026-10-13T10:00:00.123Z'),
  });
  assert.equal(code, 0);
  const manifest = JSON.parse(read(root, '.sintetica/install-manifest.json'));
  assert.equal(manifest.sintetica_version, '0.2.0');
  assert.equal(manifest.installed_at, '2026-10-13T10:00:00Z');
  assert.match(read(root, '.sintetica/bin/sintetica'), /sintetica-0\.2\.0-py3-none-any\.whl/);
  assert.ok(fs.existsSync(path.join(root, '.sintetica', 'runtime', 'sintetica-0.2.0-py3-none-any.whl')));
  assert.equal(read(root, '.sintetica/policy.json'), '{"cost_ceiling_usd": 7}');
  assert.equal(read(root, '.agents/skills/meu-extra/SKILL.md'), 'do usuário');
  assert.equal(JSON.parse(read(root, '.sintetica/state.json')).version, '0.2.0');
});

test('skill instalada e editada depois é tratada como do usuário', async () => {
  const root = tempProject();
  const pkg = fakePackage();
  assert.equal((await runInstall(root, { packageDir: pkg })).code, 0);
  put(root, '.claude/skills/sintetica-sample/SKILL.md', 'editada');
  const { text } = await runInstall(root, { packageDir: fakePackage({ version: '0.3.0' }) });
  assert.equal(read(root, '.claude/skills/sintetica-sample/SKILL.md'), 'editada');
  assert.match(text, /skill sintetica-sample pulado/);
});

test('falha no meio da cópia desfaz tudo desta execução', async () => {
  const root = tempProject(['.claude']);
  const { code, text } = await runInstall(root, { packageDir: fakePackage(), fs: failingFs(3) });
  assert.equal(code, 1);
  assert.match(text, /✗ falha ao gravar .*ENOSPC/);
  assert.deepEqual([...snapshot(root).keys()], []);
  assert.deepEqual(fs.readdirSync(root), ['.claude']);
});

test('falha na reinstalação restaura os arquivos anteriores', async () => {
  const root = tempProject();
  assert.equal((await runInstall(root, { packageDir: fakePackage() })).code, 0);
  const before = snapshot(root);
  const { code } = await runInstall(root, {
    packageDir: fakePackage({ version: '0.4.0' }),
    fs: failingFs(5),
  });
  assert.equal(code, 1);
  const after = snapshot(root);
  assert.deepEqual([...after.keys()].sort(), [...before.keys()].sort());
  for (const [p, info] of before) assert.equal(after.get(p)?.sha, info.sha, p);
});

test('sem permissão de escrita: código 1 e o caminho', { skip: process.getuid?.() === 0 }, async () => {
  const root = tempProject();
  fs.chmodSync(root, 0o555);
  try {
    const { code, text } = await runInstall(root, { packageDir: fakePackage() });
    assert.equal(code, 1);
    assert.match(text, /✗ falha ao gravar .*EACCES/);
    assert.deepEqual(fs.readdirSync(root), []);
  } finally {
    fs.chmodSync(root, 0o755);
  }
});

test('policy.json corrompido vira .bak e a política padrão é gravada', async () => {
  const root = tempProject();
  put(root, '.sintetica/policy.json', '{ corrompido');
  const { code, text } = await runInstall(root, { packageDir: fakePackage() });
  assert.equal(code, 0);
  assert.equal(read(root, '.sintetica/policy.json.bak'), '{ corrompido');
  assert.deepEqual(JSON.parse(read(root, '.sintetica/policy.json')), POLICY_DEFAULT);
  assert.match(text, /! \.sintetica\/policy\.json inválido/);
});

test('fora de projeto: sem confirmação nada é criado; com --yes instala', async () => {
  const home = tempProject();
  const refused = await runInstall(home, { packageDir: fakePackage(), home });
  assert.equal(refused.code, 1);
  assert.match(refused.text, /instalação cancelada/);
  assert.deepEqual(fs.readdirSync(home), []);
  const accepted = await runInstall(home, { packageDir: fakePackage(), home, yes: true });
  assert.equal(accepted.code, 0);
});

test('pasta inexistente, Node antigo e manifest ilegível', async () => {
  const missing = await runInstall(path.join(os.tmpdir(), 'nao-existe-sintetica'), {
    packageDir: fakePackage(),
  });
  assert.equal(missing.code, 1);
  const old = await runInstall(tempProject(), { packageDir: fakePackage(), nodeVersion: '16.20.2' });
  assert.equal(old.code, 1);
  assert.match(old.text, /✗ Node\.js 16\.20\.2 encontrado; o sintetica exige 18\.0\.0/);
  const root = tempProject();
  put(root, '.sintetica/install-manifest.json', '{');
  const broken = await runInstall(root, { packageDir: fakePackage() });
  assert.equal(broken.code, 0);
  assert.match(broken.text, /install-manifest\.json ilegível/);
});

test('bin: ajuda sem comando e instalação pela linha de comando', () => {
  const help = spawnSync(process.execPath, [BIN], { encoding: 'utf8' });
  assert.equal(help.status, 1);
  assert.match(help.stderr, /Uso: npx sintetica install/);
  const root = tempProject(['.gemini']);
  const run = spawnSync(process.execPath, [BIN, 'install', '--dir', root], {
    encoding: 'utf8',
    env: fakeEnv(),
    input: '',
  });
  assert.equal(run.status, 0, run.stderr);
  assert.match(run.stdout, /Gemini CLI/);
});
