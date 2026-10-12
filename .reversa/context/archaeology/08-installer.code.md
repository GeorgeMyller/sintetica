## Módulo `installer` (`installer/`, pacote npm `sintetica`)

🟢 **Propósito:** `npx sintetica install`. Confere o Node.js, detecta os harnesses, instala as 5 skills nos 2 destinos universais, o wheel do runtime Python e o lançador, e cria `.sintetica/` (política, estado e manifest). Nunca substitui arquivo do usuário sem confirmação; desfaz tudo se falhar; não usa a rede.

### Arquivos

| Arquivo | Papel |
|---------|-------|
| `bin/sintetica.js` | Ponto de entrada: confere a versão do Node antes de importar o resto |
| `src/args.js` | `checkNode`, `parseArgs`, `HELP`, `MIN_NODE` (sintaxe aceita pelo Node 16) |
| `src/detect.js` | `HARNESSES` (marcadores), `detectHarnesses` |
| `src/files.js` | `sha256`, `Journal` (escrita atômica e desfazer), `realFs` injetável |
| `src/runtime.js` | `checkRuntime`, `pythonOk`, `uvInstallHint`, `launcherSh`, `launcherCmd`, `findWheel`, `wheelName` |
| `src/plan.js` | `SKILLS`, `SKILL_ROOTS`, `desiredFiles`, `decide` (6 ações) |
| `src/prompt.js` | `makeAsker` (`readline`, `--yes`, sem terminal), `outOfProject` |
| `src/install.js` | `install`: orquestração, `state.json`, manifest, resumo |
| `skills/sintetica-*/SKILL.md` | As 5 skills, chamando `.sintetica/bin/sintetica` |
| `templates/policy.json` | Política padrão |
| `runtime/` | Wheel gerado por `npm run build:runtime` (`prepack`) |

### Funções principais

| Função | Assinatura | Retorno | Local |
|--------|-----------|---------|-------|
| `install` | `(opts: {dir, yes?, out, ask?, interactive?, fs?, spawn?, env?, nodeVersion?, home?, platform?, packageDir?, now?})` | código 0 ou 1 | `src/install.js:104` |
| `checkNode` | `(version)` | mensagem ou `null` | `src/args.js:18` |
| `parseArgs` | `(argv, cwd)` | `{command, yes, dir}` ou `{error}` | `src/args.js:43` |
| `detectHarnesses` | `(root, previous=[])` | harnesses na ordem fixa | `src/detect.js:38` |
| `desiredFiles` | `(packageDir, version)` | `{files, wheel}` | `src/plan.js:31` |
| `decide` | `(file, root, manifest)` | ação | `src/plan.js:80` |
| `checkRuntime` | `({spawn?, env?})` | `{uv, python, ready}` | `src/runtime.js:52` |
| `Journal.write` / `rename` / `rollback` | — | — | `src/files.js:73-110` |

### Algoritmos e regras

1. 🟢 **Versão do Node** (`bin/sintetica.js`, `args.js:18-34`): compara major.minor.patch com 18.0.0 antes de importar módulos modernos; abaixo, `✗` com a versão encontrada e a mínima, código 1.
2. 🟢 **Fora de projeto** (`prompt.js:39-43`, `install.js:123-128`): pasta pessoal ou raiz do sistema exigem confirmação (`--yes` confirma); recusa termina com 1 sem criar nada.
3. 🟢 **Detecção** (`detect.js`): Claude Code `.claude`; Antigravity `.agents` ou `.agent`; Cursor `.cursor`; Gemini CLI `.gemini`; Codex `.codex` ou `AGENTS.md`. `.claude` e `.agents` com só as skills do sintetica não contam, salvo se o `state.json` anterior já listava o harness. A detecção só informa o resumo e o `state.json` (Q51).
4. 🟢 **Plano de arquivos** (`plan.js`): 10 skills (5 × 2 destinos), lançador `sh` (modo 755) e `.cmd`, wheel (se empacotado) e política. Ação por arquivo: `criar` (ausente), `igual` (mesmo SHA-256), `substituir` (no manifest com o mesmo hash), `perguntar` (fora do manifest ou editado), `preservar` (`policy.json` válido), `recuperar` (`policy.json` inválido).
5. 🟢 **Confirmações** (`prompt.js:13-31`, `install.js:180-212`): 1 pergunta por skill (as 2 cópias juntas) e 1 por arquivo fora das skills; `--yes` responde sim; sem terminal interativo, não, com aviso sugerindo `--yes`; resposta não pula as 2 cópias.
6. 🟢 **Escrita com desfazer** (`files.js`): pastas criadas registradas; arquivo temporário no mesmo diretório, `chmod` e `rename`; o diário guarda criado, substituído (conteúdo anterior), renomeado (`.bak`) e pasta; `rollback` desfaz em ordem inversa e ignora erros pontuais. Qualquer erro na aplicação: desfaz e termina com 1, citando caminho e código (`ENOSPC`, `EACCES`).
7. 🟢 **Política** (`install.js:150-155`): `recuperar` renomeia para `policy.json.bak` e grava a padrão, com aviso; `--yes` nunca substitui a política existente.
8. 🟢 **Runtime** (`runtime.js:52-73`): `uv --version` por `spawnSync` sem shell; Python ≥ 3.10 por `uv python find ">=3.10"` (com `uv`) ou `python3`/`python --version`; sem eles, aviso com o comando de instalação do `uv` (só exibido) e `runtime_ready: false`.
9. 🟢 **Lançador** (`runtime.js:107-145`): define `SINTETICA_CMD` com o próprio caminho e roda `uvx --from <wheel> sintetica`; sem o wheel, `uv run sintetica`. O `.cmd` é ASCII com `\r\n`.
10. 🟢 **Idempotência** (`install.js:230-266`): `state.json` e manifest só são gravados se o conteúdo mudar; manifest ordenado, sem a si mesmo, com `installed_at` sem milissegundos.

### Tratamento de erros

🟢 Código 1 para Node antigo, comando inválido, pasta inexistente, cancelamento e falha de escrita; `install-manifest.json` ilegível vira aviso (arquivos existentes tratados como do usuário).

### Constantes

| Constante | Valor | Local |
|-----------|-------|-------|
| `MIN_NODE` | 18.0.0 | `args.js:4` |
| `MIN_PYTHON` | 3.10 | `runtime.js:5` |
| `LAUNCHER`, `LAUNCHER_CMD`, `RUNTIME_DIR` | `.sintetica/bin/sintetica`, `.cmd`, `.sintetica/runtime` | `runtime.js:6-8` |
| `SKILLS` | `sintetica-start`, `-schema`, `-sample`, `-generate`, `-eval` | `plan.js:7` |
| `SKILL_ROOTS` | `.agents/skills`, `.claude/skills` | `plan.js:14` |

### Integração com o runtime Python

🟢 `sintetica.command.cli_command()` (`src/sintetica/command.py`) lê `SINTETICA_CMD`; as mensagens do runtime citam o lançador quando ele é usado, e `uv run sintetica` sem ele.
