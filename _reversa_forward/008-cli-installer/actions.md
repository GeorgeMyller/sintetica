# Actions: cli-installer (instalador `npx sintetica install`)

> Identificador: `008-cli-installer`
> Data: `2026-10-12`
> Roadmap: `_reversa_forward/008-cli-installer/roadmap.md`
> Fontes auxiliares: `data-delta.md`, `interfaces/installer-cli.md`, `requirements.md` (17 cenários Gherkin).

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 28 |
| Paralelizáveis (`[//]`) | 23 |
| Maior cadeia de dependência | 7 (T001 → T014 → T016 → T018 → T019 → T025 → T026) |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Criar `installer/` com `package.json` (`name: sintetica`, versão igual à do `pyproject.toml`, `type: module`, `bin`, `engines.node >= 18`, `files`, scripts `typecheck`, `test`, `coverage`, `build:runtime` e `prepack`, dependências só de desenvolvimento `typescript`, `c8`, `@types/node`) e `tsconfig.json` (`allowJs`, `checkJs`, `strict`, `noEmit`) (D-01, D-18) | - | `[//]` | `installer/package.json` | 🟢 | `[X]` |
| T002 | Criar `sintetica.command.cli_command()`: lê `SINTETICA_CMD` e devolve `uv run sintetica` sem ela (D-13) | - | `[//]` | `src/sintetica/command.py` | 🟡 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Criar os auxiliares de teste do instalador: projeto temporário, executáveis falsos (`uv`, `python3`) no início do `PATH`, sistema de arquivos com falha na n-ésima escrita, execução do instalador com a saída capturada e SHA-256 dos arquivos (D-19) | T001 | `[//]` | `installer/test/helpers.js` | 🟡 | `[X]` |
| T004 | Escrever testes de argumentos, versão do Node (16 recusado com a versão encontrada e a mínima) e detecção dos 5 harnesses pelos marcadores (D-02 a D-04) | T003 | `[//]` | `installer/test/detect.test.js` | 🟢 | `[X]` |
| T005 | Escrever testes do plano de arquivos: as 6 ações (`criar`, `igual`, `substituir`, `perguntar`, `preservar`, `recuperar`), arquivo do manifest editado tratado como do usuário (D-05) | T003 | `[//]` | `installer/test/plan.test.js` | 🟢 | `[X]` |
| T006 | Escrever testes da escrita atômica e do diário de desfazer: criado apagado, substituído restaurado, `.bak` revertido (D-07) | T003 | `[//]` | `installer/test/files.test.js` | 🟢 | `[X]` |
| T007 | Escrever testes do runtime: `uv` e Python ≥ 3.10 pelos executáveis falsos, comando de instalação por sistema, conteúdo do lançador `sh` e `.cmd`, wheel encontrado ou ausente (D-10 a D-12) | T003 | `[//]` | `installer/test/runtime.test.js` | 🟡 | `[X]` |
| T008 | Escrever os testes de ponta a ponta dos cenários Gherkin do instalador: instalação limpa, sem harness, manifest, arquivo do usuário com resposta não, `--yes` com política do usuário, runtime ausente, 2ª execução, versão nova, falha no meio, somente leitura, `policy.json` corrompido, `$HOME`, sem terminal interativo | T003 | `[//]` | `installer/test/install.test.js` | 🟡 | `[X]` |
| T009 | Escrever testes Python de `cli_command()` e das mensagens: sem `SINTETICA_CMD`, saída idêntica; com o lançador, a retomada do lote cita `.sintetica/bin/sintetica` (RF-16) | T002 | `[//]` | `tests/test_command.py` | 🟡 | `[X]` |
| T010 | Escrever testes Python das skills e da política: todo comando citado em `installer/skills/*/SKILL.md` existe no parser da CLI; a política padrão do instalador é lida pelo runtime sem erro; versão do `package.json` igual à do `pyproject.toml` (D-12, D-15, RN-04) | T001 | `[//]` | `tests/test_skills_commands.py` | 🟢 | `[X]` |
| T011 | Escrever o teste de integração do lançador com o wheel real (`.sintetica/bin/sintetica --help` e `start` num projeto temporário), pulado quando `uv` não estiver disponível | T001 | `[//]` | `tests/test_launcher.py` | 🟡 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T012 | Implementar `checkNode(versão)` com sintaxe aceita pelo Node 16 e a leitura dos argumentos `install [--yes] [--dir]` com a ajuda (D-02, D-03) | T001 | `[//]` | `installer/src/args.js` | 🟡 | `[X]` |
| T013 | Implementar a detecção dos harnesses pelos marcadores da Q51, em ordem fixa (D-04) | T001 | `[//]` | `installer/src/detect.js` | 🟢 | `[X]` |
| T014 | Implementar SHA-256, escrita atômica com modo de arquivo, sistema de arquivos injetável e o diário de desfazer (D-07) | T001 | `[//]` | `installer/src/files.js` | 🟢 | `[X]` |
| T015 | Implementar a verificação de `uv` e Python por `spawnSync` sem shell, o comando de instalação do `uv` por sistema, o conteúdo do lançador `sh` e `.cmd` e a busca do wheel (D-10 a D-12) | T001 | `[//]` | `installer/src/runtime.js` | 🟢 | `[X]` |
| T016 | Implementar o plano: arquivos desejados (10 skills, lançadores, wheel, política padrão) e a ação de cada um pelo manifest e pelo SHA-256 (D-05) | T014, T015 | - | `installer/src/plan.js` | 🟢 | `[X]` |
| T017 | Implementar as confirmações: `readline`, `--yes` (exceto `policy.json`), sem terminal interativo = não com aviso, confirmação fora de projeto (D-06, D-16) | T001 | `[//]` | `installer/src/prompt.js` | 🟡 | `[X]` |
| T018 | Implementar a orquestração: versão do Node, diretório, detecção, plano, confirmações, aplicação com desfazer, `state.json` e `install-manifest.json` gravados só se mudarem, resumo com `✓`, `!` e `✗` e códigos 0 e 1 (D-08, D-09, D-17) | T012, T013, T016, T017 | - | `installer/src/install.js` | 🟢 | `[X]` |
| T019 | Implementar `bin/sintetica.js`: checa o Node antes de importar o resto e chama a instalação | T018 | - | `installer/bin/sintetica.js` | 🟡 | `[X]` |
| T020 | Escrever as skills `sintetica-start`, `sintetica-schema` e `sintetica-sample` a partir de `docs/intent-interview.md`, `docs/schema-builder.md` e `docs/sample-preview.md`, com o lançador, o protocolo `request`/`submit` e os códigos de saída (D-14) | T001 | `[//]` | `installer/skills/` | 🟡 | `[X]` |
| T021 | Escrever as skills `sintetica-generate` e `sintetica-eval` a partir de `docs/batch-generator.md` e `docs/quality-evaluator.md`, com autorização de custo, background, retomada e veredito (D-14) | T001 | `[//]` | `installer/skills/` | 🟡 | `[X]` |
| T022 | Trocar `uv run sintetica` por `cli_command()` em `cli.py`, `providers/harness/provider.py` e `schema/service.py` (D-13) | T002 | `[//]` | `src/sintetica/cli.py` | 🟡 | `[X]` |
| T023 | Trocar `uv run sintetica` por `cli_command()` em `intent/service.py`, `intent/model.py` e `intent/summary.py` (D-13) | T002 | `[//]` | `src/sintetica/intent/service.py` | 🟡 | `[X]` |
| T024 | Trocar `uv run sintetica` por `cli_command()` em `sample/service.py`, `batch/service.py` e `quality/service.py` (D-13) | T002 | `[//]` | `src/sintetica/batch/service.py` | 🟡 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T025 | Gerar o wheel com `npm run build:runtime` e conferir que o instalador o copia para `.sintetica/runtime/` e que o lançador o usa (D-12) | T019, T020, T021 | - | `installer/package.json` | 🟡 | `[X]` |
| T026 | Completar os testes até `tsc --checkJs --strict` sem erros e cobertura ≥ 80% pelo `c8` em `installer/`, com os 17 cenários Gherkin cobertos, os 516 testes anteriores passando e `mypy --strict` e `ruff` sem erros (critério de pronto) | T025, T022, T023, T024, T004, T005, T006, T007, T008, T009, T010, T011 | - | `installer/test/` | 🟡 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T027 | Escrever a documentação curta do instalador: `npx sintetica install`, `--yes`, `--dir`, arquivos criados, lançador, reinstalação, runtime ausente e desenvolvimento do pacote | T019 | `[//]` | `docs/cli-installer.md` | 🟡 | `[X]` |
| T028 | Acrescentar aos `docs/*.md` das features 004 a 007 a nota de que, no projeto do usuário, os comandos rodam pelo lançador `.sintetica/bin/sintetica` | T024 | `[//]` | `docs/` | 🟢 | `[X]` |

## Notas de execução

<!--
Reservado para /reversa-coding registrar avisos ou observações que surgiram durante a execução.
Não use isso para corrigir ações, edits manuais ficam fora desse arquivo, vão direto no código.
-->

- As T022 a T024 e a T028 alteram arquivos das features 002 a 007: 40 mensagens com `uv run sintetica` em 9 arquivos de `src/sintetica/` passam a usar `cli_command()`, e os 5 `docs/*.md` ganham a nota do lançador. Sem `SINTETICA_CMD`, a saída é idêntica; os 516 testes anteriores passam sem mudança.
- 2026-10-12, T013: os testes da T004 acharam um defeito. Uma pasta `.claude` vazia quebrava a detecção com `ENOENT`. Correção: pasta vazia conta como marcador.
- 2026-10-12, T018: os testes da T008 acharam outro defeito. Depois da 1ª instalação, uma pasta `.claude` que o usuário tinha vazia passa a ter só as skills do sintetica e deixava de ser detectada; a 2ª execução mudava o `state.json` (quebra da idempotência). Correção: a detecção considera os harnesses do `state.json` anterior.
- 2026-10-12, T010: o teste de versão lê o `pyproject.toml` por expressão regular, sem `tomllib`, porque o projeto aceita Python 3.10.
- 2026-10-12, T001: os aliases `npm` e `uv` do shell desta máquina apontam para um comando ausente; a execução usou os binários diretos (`~/.volta/bin/npm`, `~/.local/bin/uv`). O `npm install` das ferramentas de desenvolvimento usou a rede (88 pacotes).
- 2026-10-12, T025: o `npm run build:runtime` gerou `installer/runtime/sintetica-0.1.0-py3-none-any.whl` (87 arquivos, só o pacote `sintetica`). O arquivo é artefato de build e fica no repositório até a publicação. Teste manual: instalação num projeto temporário e `.sintetica/bin/sintetica start Pedidos` pelo `uvx`, com a mensagem citando o lançador.
- 2026-10-12, T026: 532 testes Python passam (516 anteriores + 16 novos: 2 em `tests/test_command.py`, 13 em `tests/test_skills_commands.py`, 1 em `tests/test_launcher.py`); 37 testes Node passam; cobertura do instalador em 99,6% de linhas pelo `c8`; `tsc --checkJs --strict`, `mypy --strict` e `ruff` sem erros. Os 17 cenários Gherkin têm teste correspondente. O ramo Windows (`.cmd`) só tem teste de conteúdo.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-12 | Versão inicial gerada por `/reversa-to-do` | reversa |
