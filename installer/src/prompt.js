import os from 'node:os';
import path from 'node:path';
import readline from 'node:readline';

/** @typedef {(question: string) => Promise<boolean>} Ask */

/**
 * Confirmações (D-06): `--yes` responde sim; sem terminal interativo, responde não.
 * @param {{ yes: boolean, interactive: boolean, input?: NodeJS.ReadableStream,
 *   output?: NodeJS.WritableStream, answer?: (q: string) => Promise<string> }} opts
 * @returns {Ask}
 */
export function makeAsker(opts) {
  return async (question) => {
    if (opts.yes) return true;
    if (!opts.interactive && !opts.answer) return false;
    const reply = opts.answer
      ? await opts.answer(question)
      : await new Promise((resolve) => {
          const rl = readline.createInterface({
            input: opts.input ?? process.stdin,
            output: opts.output ?? process.stdout,
          });
          rl.question(`? ${question} (sim/não) `, (text) => {
            rl.close();
            resolve(text);
          });
        });
    return /^\s*(s|sim|y|yes)\s*$/i.test(reply);
  };
}

/**
 * Fora de projeto (D-16): a pasta pessoal ou a raiz do sistema.
 * @param {string} dir
 * @param {string} [home]
 * @returns {boolean}
 */
export function outOfProject(dir, home = os.homedir()) {
  const resolved = path.resolve(dir);
  return resolved === path.resolve(home) || resolved === path.parse(resolved).root;
}
