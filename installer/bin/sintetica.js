#!/usr/bin/env node
// Ponto de entrada de `npx sintetica`. A checagem de versão vem antes de importar o restante
// do instalador, para o Node antigo mostrar a mensagem certa (D-02).
import { HELP, checkNode, parseArgs } from '../src/args.js';

const problem = checkNode(process.versions.node);
if (problem) {
  console.error('✗ ' + problem);
  process.exit(1);
}

const parsed = parseArgs(process.argv.slice(2), process.cwd());
if ('error' in parsed) {
  console.error('✗ ' + parsed.error);
  console.error(HELP);
  process.exit(1);
}

import('../src/install.js')
  .then(function (mod) {
    return mod.install({
      dir: parsed.dir,
      yes: parsed.yes,
      out: function (line) {
        console.log(line);
      },
    });
  })
  .then(function (code) {
    process.exitCode = code;
  });
