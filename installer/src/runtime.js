import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

export const MIN_PYTHON = [3, 10];
export const LAUNCHER = '.sintetica/bin/sintetica';
export const LAUNCHER_CMD = '.sintetica/bin/sintetica.cmd';
export const RUNTIME_DIR = '.sintetica/runtime';

/**
 * @typedef {(cmd: string, args: string[], opts: { encoding: 'utf8', env: NodeJS.ProcessEnv, shell: false })
 *   => { status: number | null, stdout: string | null, error?: Error }} Spawn
 * @typedef {{ uv: string | null, python: boolean, ready: boolean }} RuntimeCheck
 */

/** @type {Spawn} */
const defaultSpawn = (cmd, args, opts) => {
  const result = spawnSync(cmd, args, opts);
  return { status: result.status, stdout: result.stdout, error: result.error };
};

/**
 * @param {Spawn} spawn
 * @param {NodeJS.ProcessEnv} env
 * @param {string} cmd
 * @param {string[]} args
 * @returns {string | null} saída do comando, ou null se ele falhou ou não existe
 */
function run(spawn, env, cmd, args) {
  const result = spawn(cmd, args, { encoding: 'utf8', env, shell: false });
  if (result.error || result.status !== 0) return null;
  return result.stdout ?? '';
}

/**
 * @param {string} text saída de `python --version`
 * @returns {boolean}
 */
export function pythonOk(text) {
  const match = /Python (\d+)\.(\d+)/.exec(text);
  if (!match) return false;
  const major = Number(match[1]);
  const minor = Number(match[2]);
  return major > MIN_PYTHON[0] || (major === MIN_PYTHON[0] && minor >= MIN_PYTHON[1]);
}

/**
 * `uv` no PATH e Python ≥ 3.10 (D-10). Nada é instalado, só verificado.
 * @param {{ spawn?: Spawn, env?: NodeJS.ProcessEnv }} [opts]
 * @returns {RuntimeCheck}
 */
export function checkRuntime(opts = {}) {
  const spawn = opts.spawn ?? defaultSpawn;
  const env = opts.env ?? process.env;
  const uvOut = run(spawn, env, 'uv', ['--version']);
  const uv = uvOut === null ? null : uvOut.trim();
  let python = false;
  if (uv !== null) {
    python = run(spawn, env, 'uv', ['python', 'find', '>=3.10']) !== null;
  } else {
    for (const exe of ['python3', 'python']) {
      const out = run(spawn, env, exe, ['--version']);
      if (out !== null && pythonOk(out)) {
        python = true;
        break;
      }
    }
  }
  return { uv, python, ready: uv !== null && python };
}

/**
 * Comando recomendado para instalar o `uv` (só exibido, nunca executado).
 * @param {NodeJS.Platform} platform
 * @returns {string}
 */
export function uvInstallHint(platform) {
  if (platform === 'win32') {
    return 'powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"';
  }
  return 'curl -LsSf https://astral.sh/uv/install.sh | sh';
}

/**
 * @param {string} version
 * @returns {string} nome do wheel desta versão
 */
export function wheelName(version) {
  return `sintetica-${version}-py3-none-any.whl`;
}

/**
 * @param {string} packageDir pasta do pacote npm
 * @param {string} version
 * @returns {string | null} caminho do wheel empacotado, ou null (cópia de desenvolvimento)
 */
export function findWheel(packageDir, version) {
  const file = path.join(packageDir, 'runtime', wheelName(version));
  return fs.existsSync(file) ? file : null;
}

/**
 * Lançador POSIX (D-11): `uvx --from <wheel>`; sem o wheel, `uv run sintetica`.
 * @param {string} version
 * @returns {string}
 */
export function launcherSh(version) {
  return [
    '#!/bin/sh',
    '# Lançador do runtime do sintetica, criado por `npx sintetica install`.',
    'ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)',
    `SINTETICA_CMD="${LAUNCHER}"`,
    'export SINTETICA_CMD',
    `WHEEL="$ROOT/${RUNTIME_DIR}/${wheelName(version)}"`,
    'if [ -f "$WHEEL" ]; then',
    '  exec uvx --from "$WHEEL" sintetica "$@"',
    'fi',
    'exec uv run sintetica "$@"',
    '',
  ].join('\n');
}

/**
 * Lançador do Windows, em ASCII para não depender da página de código do terminal.
 * @param {string} version
 * @returns {string}
 */
export function launcherCmd(version) {
  return [
    '@echo off',
    'rem Lancador do runtime do sintetica, criado por npx sintetica install.',
    'setlocal',
    'set "ROOT=%~dp0..\\.."',
    'set "SINTETICA_CMD=.sintetica\\bin\\sintetica.cmd"',
    `set "WHEEL=%ROOT%\\.sintetica\\runtime\\${wheelName(version)}"`,
    'if exist "%WHEEL%" (',
    '  uvx --from "%WHEEL%" sintetica %*',
    ') else (',
    '  uv run sintetica %*',
    ')',
    'exit /b %ERRORLEVEL%',
    '',
  ].join('\r\n');
}
