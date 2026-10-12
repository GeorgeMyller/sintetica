# Legacy Impact: batch-generator

> Identificador: `006-batch-generator`
> Data: `2026-10-12`
> Feature greenfield, sem legado pré-existente. Âncora: prd.md + specs SDD.
> Política de edição no momento da execução: `allowLegacyEdits: true`, `allowedPaths: []` (projeto inteiro liberado, sem restrição de caminho).

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/sintetica/cli.py` | Comando `sintetica` (`_reversa_sdd/addenda/004-intent-interview.md`) | delta-de-contrato-externo | MEDIUM | Comandos `generate` e `status` e códigos 14, 15 e 16; demais inalterados |
| `src/sintetica/sample/review.py` | `sample-preview` (`_reversa_sdd/addenda/005-sample-preview.md`) | delta-de-contrato-externo | LOW | `first_error` e `mask_value` públicos (antes privados); `review_records` inalterado |
| `src/sintetica/sample/request.py` | `sample-preview` | delta-de-contrato-externo | LOW | `intent_lines` extraída; `build_instructions` com a mesma saída (teste) |
| `src/sintetica/sample/service.py` | `sample-preview` | delta-de-contrato-externo | LOW | A aprovação indica `uv run sintetica generate <slug>` como próximo passo |
| `tests/sample/test_cli.py`, `tests/sample/test_shared.py` | `sample-preview` | componente-novo | LOW | 1 asserção ajustada ao texto novo; 4 testes das mudanças |
| `src/sintetica/batch/state.py` | `batch-generator` (`_reversa_sdd/sdd/batch-generator.md#9`) | componente-novo | MEDIUM | `RunState` e caminhos de `output/` |
| `src/sintetica/batch/plan.py`, `request.py` | `batch-generator` (RF-03, Q46) | componente-novo | MEDIUM | Bloco adaptativo e instruções com bloco e rodada |
| `src/sintetica/batch/review.py` | `batch-generator` (RF-04 a RF-06) e `pii-guard` | componente-novo | HIGH | Validação, duplicados por SHA-256, mascaramento e revalidação antes do disco |
| `src/sintetica/batch/output.py` | `batch-generator` (RF-07, RF-10, RF-11) | componente-novo | HIGH | Gravação por bloco com `fsync`, retomada e conversão final |
| `src/sintetica/batch/engine.py` | `batch-generator` (RF-03 a RF-07) e `llm-provider` | componente-novo | HIGH | Fila de blocos, rodadas, status finais e caminho do harness |
| `src/sintetica/batch/lock.py`, `background.py`, `worker.py` | `batch-generator` (RF-08, EC-04, EC-06) | componente-novo | HIGH | Trava por dataset e processo separado em sessão própria |
| `src/sintetica/batch/service.py`, `__init__.py` | `batch-generator` (RF-01, RF-02, RF-09) | componente-novo | HIGH | Pré-condições, custo e autorização, lote existente, `generate` e `status` |
| `tests/batch/*.py` | `batch-generator` | componente-novo | LOW | 55 testes, mais 1 `perf`; processo real e `sintetica submit` real |
| `docs/batch-generator.md` | `batch-generator` | componente-novo | LOW | Fluxo da skill `sintetica-generate` |

## Diff conceitual por componente

**Comando `sintetica`.** Ganha `generate <slug> [--resume] [--new] [--authorize-usd] [--block-size]` e `status <slug>`, importados de forma tardia. Os códigos 14 (amostra ausente ou de outra versão), 15 (custo exige autorização) e 16 (lote em andamento, interrompido ou existente) somam-se aos 0 e 2 a 13.

**sample-preview.** Só acréscimos e 1 texto. `first_error` e `mask_value` passam a ser públicos para a revisão do lote. `intent_lines` sai de `build_instructions` sem mudar a saída. A aprovação da amostra agora indica o comando `generate`.

**llm-provider.** Sem mudança de código. O lote chama `build_provider` com o volume total, o valor autorizado e a estimativa por pedido. O harness recebe 1 pedido por rodada; a resposta bruta é apagada depois de lida.

**batch-generator.** Componente novo, conforme `_reversa_sdd/sdd/batch-generator.md`, com estes desvios:
- Comando `generate --resume` e `status`, com `--new`, `--authorize-usd` e `--block-size` novos.
- Harness para lotes de até 100 registros, em 1 pedido por rodada (Q44).
- Bloco adaptativo, de até 10 registros (Q46), no lugar do bloco fixo de 10.
- Background por processo em sessão própria, com trava de arquivo para detectar processo encerrado (Q45).
- Status `iniciando` e `aguardando_agente` novos; o `quality-evaluator` não é chamado nesta feature (Q40).
- Decisões novas da execução: sementes lidas sem `Decimal`, erro inesperado do background sem traceback no log, retomada zera o contador de rodadas.

## Preservadas

Nenhuma. Feature greenfield, sem regras 🟢 extraídas de código anterior.

## Modificadas

Nenhuma. Feature greenfield, sem regras 🟢 extraídas de código anterior.
