# Legacy Impact: cli-installer

> Identificador: `008-cli-installer`
> Data: `2026-10-12`
> Feature greenfield, sem legado pré-existente. Âncora: prd.md + specs SDD.
> Política de edição no momento da execução: `allowLegacyEdits: true`, `allowedPaths: []` (projeto inteiro liberado, sem restrição de caminho).

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/sintetica/command.py` | Runtime Python (adendos 002 a 007) | componente-novo | MEDIUM | `cli_command()` lê `SINTETICA_CMD`; padrão `uv run sintetica` |
| `src/sintetica/cli.py`, `providers/harness/provider.py`, `schema/service.py`, `intent/service.py`, `intent/model.py`, `intent/summary.py`, `sample/service.py`, `batch/service.py`, `quality/service.py` | Comando `sintetica` e serviços (adendos 002 a 007) | delta-de-contrato-externo | MEDIUM | 40 mensagens citam o comando de quem chamou; sem a variável, saída idêntica |
| `docs/intent-interview.md`, `schema-builder.md`, `sample-preview.md`, `batch-generator.md`, `quality-evaluator.md` | Documentação das features 004 a 007 | componente-novo | LOW | Nota do lançador `.sintetica/bin/sintetica` |
| `installer/package.json`, `tsconfig.json`, `package-lock.json` | `cli-installer` (`_reversa_sdd/sdd/cli-installer.md#7`) | componente-novo | LOW | Pacote npm `sintetica`, Node ≥ 18, só dependências de desenvolvimento |
| `installer/bin/sintetica.js`, `installer/src/args.js` | `cli-installer` (RF-01) | componente-novo | MEDIUM | Checagem da versão do Node antes de importar o restante |
| `installer/src/detect.js` | `cli-installer` (RF-02) | componente-novo | LOW | Marcadores da Q51; harnesses anteriores mantidos |
| `installer/src/files.js` | `cli-installer` (EC-01, EC-02) | componente-novo | HIGH | Escrita atômica, SHA-256 e diário de desfazer |
| `installer/src/plan.js`, `installer/templates/policy.json` | `cli-installer` (RF-03 a RF-07, RF-09) | componente-novo | HIGH | Arquivos desejados e as 6 ações; política padrão |
| `installer/src/prompt.js` | `cli-installer` (RF-07, RF-11, EC-05) | componente-novo | MEDIUM | Confirmações, `--yes`, terminal não interativo, fora de projeto |
| `installer/src/runtime.js` | `cli-installer` (RF-08) | componente-novo | MEDIUM | `uv` e Python, lançadores `sh` e `.cmd`, wheel |
| `installer/src/install.js` | `cli-installer` (RF-04, RF-05, RF-10) | componente-novo | HIGH | Orquestração, `state.json`, manifest e resumo |
| `installer/skills/sintetica-*/SKILL.md` | Skills do PRD (seção 4, "Pipeline de agentes") | componente-novo | HIGH | As 5 skills, chamando o lançador |
| `installer/runtime/sintetica-0.1.0-py3-none-any.whl` | `cli-installer` (Q50) | componente-novo | LOW | Wheel gerado por `build:runtime`; artefato de build |
| `installer/test/*.js`, `tests/test_command.py`, `tests/test_skills_commands.py`, `tests/test_launcher.py` | `cli-installer` | componente-novo | LOW | 37 testes Node e 16 testes Python |
| `docs/cli-installer.md` | `cli-installer` | componente-novo | LOW | Uso, arquivos, regras e desenvolvimento |

## Diff conceitual por componente

**Runtime Python.** A função `sintetica.command.cli_command()` devolve o prefixo dos comandos citados nas mensagens. O lançador define `SINTETICA_CMD=.sintetica/bin/sintetica`; sem a variável, vale `uv run sintetica`. As 40 mensagens das features 002 a 007 usam a função. Nenhum comportamento muda.

**cli-installer.** Componente novo, conforme `_reversa_sdd/sdd/cli-installer.md`, com estes desvios:
- O pacote npm leva o wheel do runtime; o instalador cria `.sintetica/runtime/` e o lançador `.sintetica/bin/sintetica` (Q50). As skills chamam o lançador.
- Destinos sempre `.agents/skills/` e `.claude/skills/`; a detecção só informa (Q51).
- JavaScript ESM com JSDoc, `tsc --checkJs --strict`, `node:test` e `c8` (Q52).
- Opção `--dir` nova.
- Sem terminal interativo e sem `--yes`, a resposta às confirmações é não.
- Arquivo do manifest editado pelo usuário é tratado como do usuário (pergunta antes).
- Decisão nova da execução: os harnesses do `state.json` anterior continuam detectados quando a pasta só tem as skills do sintetica.

## Preservadas

Nenhuma. Feature greenfield, sem regras 🟢 extraídas de código anterior.

## Modificadas

Nenhuma. Feature greenfield, sem regras 🟢 extraídas de código anterior.
