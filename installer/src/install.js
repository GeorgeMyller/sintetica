import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { checkNode } from './args.js';
import { detectHarnesses } from './detect.js';
import { Journal, realFs, sha256 } from './files.js';
import { MANIFEST, POLICY, SKILL_ROOTS, STATE, decide, desiredFiles } from './plan.js';
import { makeAsker, outOfProject } from './prompt.js';
import { LAUNCHER, checkRuntime, uvInstallHint } from './runtime.js';

/** Pasta do pacote npm (onde ficam `skills/`, `templates/` e `runtime/`). */
export const PACKAGE_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

/**
 * @typedef {import('./plan.js').Desired} Desired
 * @typedef {import('./plan.js').Action} Action
 * @typedef {import('./prompt.js').Ask} Ask
 * @typedef {import('./runtime.js').Spawn} Spawn
 * @typedef {import('./files.js').FsApi} FsApi
 * @typedef {{
 *   dir: string,
 *   yes?: boolean,
 *   out: (line: string) => void,
 *   ask?: Ask,
 *   interactive?: boolean,
 *   fs?: FsApi,
 *   spawn?: Spawn,
 *   env?: NodeJS.ProcessEnv,
 *   nodeVersion?: string,
 *   home?: string,
 *   platform?: NodeJS.Platform,
 *   packageDir?: string,
 *   now?: () => Date,
 * }} InstallOptions
 * @typedef {{ sintetica_version: string, installed_at: string,
 *   files: { path: string, sha256: string }[] }} Manifest
 */

/**
 * @param {string} dir
 * @returns {string}
 */
function readVersion(dir) {
  const pkg = JSON.parse(fs.readFileSync(path.join(dir, 'package.json'), 'utf8'));
  return String(pkg.version);
}

/**
 * @param {string} root
 * @param {(line: string) => void} out
 * @returns {Manifest | null}
 */
function readManifest(root, out) {
  const file = path.join(root, ...MANIFEST.split('/'));
  if (!fs.existsSync(file)) return null;
  try {
    const data = JSON.parse(fs.readFileSync(file, 'utf8'));
    if (data && Array.isArray(data.files)) return /** @type {Manifest} */ (data);
  } catch {
    // tratado abaixo
  }
  out(`! ${MANIFEST} ilegível: todos os arquivos existentes serão tratados como do usuário`);
  return null;
}

/**
 * @param {string} root
 * @returns {string[]} harnesses gravados na instalação anterior
 */
function previousHarnesses(root) {
  try {
    const state = JSON.parse(fs.readFileSync(abs(root, STATE), 'utf8'));
    return Array.isArray(state.harnesses) ? state.harnesses.map(String) : [];
  } catch {
    return [];
  }
}

/**
 * @param {string} root
 * @param {string} rel
 * @returns {string}
 */
function abs(root, rel) {
  return path.join(root, ...rel.split('/'));
}

/**
 * @param {unknown} err
 * @returns {string}
 */
function describe(err) {
  const e = /** @type {NodeJS.ErrnoException} */ (err);
  const where = e && e.path ? `${e.path}: ` : '';
  return `${where}${e && e.code ? e.code : String(err)}`;
}

/**
 * `npx sintetica install` (interfaces/installer-cli.md). Devolve o código de saída.
 * @param {InstallOptions} opts
 * @returns {Promise<number>}
 */
export async function install(opts) {
  const out = opts.out;
  const packageDir = opts.packageDir ?? PACKAGE_DIR;
  const nodeVersion = opts.nodeVersion ?? process.versions.node;
  const problem = checkNode(nodeVersion);
  if (problem) {
    out(`✗ ${problem}`);
    return 1;
  }
  out(`✓ Node.js ${nodeVersion}`);

  const root = path.resolve(opts.dir);
  const ask =
    opts.ask ??
    makeAsker({ yes: Boolean(opts.yes), interactive: opts.interactive ?? Boolean(process.stdin.isTTY) });
  if (!fs.existsSync(root) || !fs.statSync(root).isDirectory()) {
    out(`✗ pasta do projeto inexistente: ${root}`);
    return 1;
  }
  if (outOfProject(root, opts.home)) {
    if (!(await ask(`${root} não parece a pasta de um projeto. Instalar mesmo assim?`))) {
      out('✗ instalação cancelada; rode o comando na raiz do seu projeto');
      return 1;
    }
  }

  const harnesses = detectHarnesses(root, previousHarnesses(root));
  if (harnesses.length) out(`✓ Harnesses detectados: ${harnesses.map((h) => h.label).join(', ')}`);
  else out(`! Nenhum harness detectado; as skills vão para ${SKILL_ROOTS.join(' e ')}`);

  const version = readVersion(packageDir);
  const previous = readManifest(root, out);
  const owned = new Map((previous?.files ?? []).map((f) => [f.path, f.sha256]));
  const { files, wheel } = desiredFiles(packageDir, version);

  /** @type {Map<string, Action>} */
  const actions = new Map(files.map((f) => [f.path, decide(f, root, owned)]));
  const skipped = await confirm(files, actions, ask, out, Boolean(opts.yes));

  const journal = new Journal(opts.fs ?? realFs);
  const runtime = checkRuntime({ spawn: opts.spawn, env: opts.env });
  try {
    /** @type {Map<string, string>} */
    const installed = new Map();
    for (const file of files) {
      const action = actions.get(file.path);
      const target = abs(root, file.path);
      if (skipped.has(file.path)) continue;
      if (action === 'criar' || action === 'substituir' || action === 'perguntar') {
        journal.write(target, file.content, file.mode);
      } else if (action === 'recuperar') {
        journal.rename(target, `${target}.bak`);
        journal.write(target, file.content, file.mode);
        out(`! ${POLICY} inválido: guardado em ${POLICY}.bak e trocado pela política padrão`);
      }
      installed.set(file.path, sha256(fs.readFileSync(target)));
    }
    const state = {
      version,
      harnesses: harnesses.map((h) => h.id),
      runtime_ready: runtime.ready,
    };
    writeIfChanged(journal, abs(root, STATE), `${JSON.stringify(state, null, 2)}\n`);
    installed.set(STATE, sha256(fs.readFileSync(abs(root, STATE))));
    writeManifest(journal, root, version, installed, previous, opts.now);
  } catch (err) {
    journal.rollback();
    out(`✗ falha ao gravar ${describe(err)}; nada desta execução foi mantido`);
    return 1;
  }

  const written = files.filter((f) => !skipped.has(f.path));
  const skills = new Set(written.filter((f) => f.kind === 'skill').map((f) => f.skill));
  out(`✓ Skills: ${skills.size} em ${SKILL_ROOTS.join('/ e ')}/`);
  if (wheel) out(`✓ Runtime: ${LAUNCHER} (wheel sintetica-${version})`);
  else out(`! Runtime: ${LAUNCHER} sem wheel empacotado; o lançador usará uv run sintetica`);
  if (!runtime.ready) {
    const missing = runtime.uv === null ? 'uv não encontrado' : 'Python 3.10 ou superior não encontrado';
    out(`! ${missing}. Instale o uv com: ${uvInstallHint(opts.platform ?? process.platform)}`);
  }
  out(`✓ Governança: ${POLICY}, ${STATE}, ${MANIFEST}`);
  out('');
  out(`Instalado em ${root}`);
  for (const dir of [...SKILL_ROOTS, '.sintetica']) out(`  ${abs(root, dir)}`);
  out('Próximo passo: no seu harness, rode /sintetica-start');
  return 0;
}

/**
 * Pergunta 1 vez por skill (as 2 cópias juntas) e 1 vez por arquivo fora das skills.
 * @param {Desired[]} files
 * @param {Map<string, Action>} actions
 * @param {Ask} ask
 * @param {(line: string) => void} out
 * @param {boolean} yes
 * @returns {Promise<Set<string>>} caminhos que não serão gravados
 */
async function confirm(files, actions, ask, out, yes) {
  /** @type {Set<string>} */
  const skipped = new Set();
  /** @type {Map<string, Desired[]>} */
  const groups = new Map();
  for (const file of files) {
    if (actions.get(file.path) !== 'perguntar') continue;
    const key = file.skill ?? file.path;
    groups.set(key, [...(groups.get(key) ?? []), file]);
  }
  let declined = false;
  for (const [key, group] of groups) {
    const paths = group.filter((f) => actions.get(f.path) === 'perguntar').map((f) => f.path);
    const label = paths.join(', ');
    if (await ask(`${label} já existe e não foi criado pelo sintetica. Substituir?`)) continue;
    declined = true;
    const same = files.filter((f) => (f.skill ?? f.path) === key);
    for (const f of same) skipped.add(f.path);
    out(`! Arquivo do usuário mantido: ${label} (${group[0].skill ? `skill ${key}` : 'arquivo'} pulado)`);
  }
  if (declined && !yes) out('! Para substituir sem perguntar, rode de novo com --yes');
  return skipped;
}

/**
 * @param {Journal} journal
 * @param {string} file
 * @param {string} text
 */
function writeIfChanged(journal, file, text) {
  if (fs.existsSync(file) && fs.readFileSync(file, 'utf8') === text) return;
  journal.write(file, text);
}

/**
 * Manifest gravado só se a lista mudar: assim uma 2ª execução igual não toca em nada (D-08).
 * @param {Journal} journal
 * @param {string} root
 * @param {string} version
 * @param {Map<string, string>} installed
 * @param {Manifest | null} previous
 * @param {(() => Date) | undefined} now
 */
function writeManifest(journal, root, version, installed, previous, now) {
  const entries = [...installed.entries()]
    .map(([p, hash]) => ({ path: p, sha256: hash }))
    .sort((a, b) => (a.path < b.path ? -1 : a.path > b.path ? 1 : 0));
  const same =
    previous !== null &&
    previous.sintetica_version === version &&
    JSON.stringify(previous.files) === JSON.stringify(entries);
  if (same) return;
  /** @type {Manifest} */
  const manifest = {
    sintetica_version: version,
    installed_at: (now ? now() : new Date()).toISOString().replace(/\.\d{3}Z$/, 'Z'),
    files: entries,
  };
  journal.write(abs(root, MANIFEST), `${JSON.stringify(manifest, null, 2)}\n`);
}
