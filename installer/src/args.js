// Este módulo é importado antes da checagem de versão do Node (D-02): só sintaxe que o
// Node 16 entende, para a mensagem de versão mínima aparecer em vez de um erro de sintaxe.

export const MIN_NODE = '18.0.0';

export const HELP = [
  'Uso: npx sintetica install [--yes] [--dir <caminho>]',
  '',
  '  install       instala as skills do sintetica no projeto',
  '  --yes         responde sim às confirmações (nunca substitui .sintetica/policy.json)',
  '  --dir <dir>   pasta do projeto (padrão: a pasta atual)',
].join('\n');

/**
 * @param {string} version versão do Node, como em `process.versions.node`
 * @returns {string | null} mensagem de erro, ou null se a versão atende ao mínimo
 */
export function checkNode(version) {
  const found = String(version).replace(/^v/, '').split('.').map(Number);
  const min = MIN_NODE.split('.').map(Number);
  for (let i = 0; i < 3; i += 1) {
    const a = found[i] || 0;
    const b = min[i] || 0;
    if (a > b) return null;
    if (a < b) {
      return 'Node.js ' + String(version).replace(/^v/, '') + ' encontrado; o sintetica exige ' +
        MIN_NODE + ' ou superior.';
    }
  }
  return null;
}

/**
 * @typedef {{ command: 'install', yes: boolean, dir: string }} Parsed
 * @typedef {{ error: string }} ParseError
 */

/**
 * @param {string[]} argv argumentos depois de `sintetica`
 * @param {string} cwd pasta atual
 * @returns {Parsed | ParseError}
 */
export function parseArgs(argv, cwd) {
  if (argv[0] !== 'install') {
    return { error: argv.length ? 'comando desconhecido: ' + argv[0] : 'informe o comando install' };
  }
  let yes = false;
  let dir = cwd;
  for (let i = 1; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--yes' || arg === '-y') {
      yes = true;
    } else if (arg === '--dir') {
      const value = argv[i + 1];
      if (!value) return { error: '--dir exige um caminho' };
      dir = value;
      i += 1;
    } else {
      return { error: 'opção desconhecida: ' + arg };
    }
  }
  return { command: 'install', yes: yes, dir: dir };
}
