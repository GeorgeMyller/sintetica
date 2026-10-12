# Legacy Impact: quality-evaluator

> Identificador: `007-quality-evaluator`
> Data: `2026-10-12`
> Feature greenfield, sem legado pré-existente. Âncora: prd.md + specs SDD.
> Política de edição no momento da execução: `allowLegacyEdits: true`, `allowedPaths: []` (projeto inteiro liberado, sem restrição de caminho).

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/sintetica/cli.py` | Comando `sintetica` (`_reversa_sdd/addenda/004-intent-interview.md`) | delta-de-contrato-externo | MEDIUM | Comando `eval` e códigos 17 e 18; demais inalterados |
| `src/sintetica/batch/service.py` | `batch-generator` (`_reversa_sdd/addenda/006-batch-generator.md`) | delta-de-contrato-externo | MEDIUM | Avaliação ao fim do lote, veredito no `status`, linha de próximo passo removida; códigos do `generate` inalterados |
| `tests/batch/test_cli.py`, `tests/batch/test_engine.py`, `tests/batch/test_quality_chain.py` | `batch-generator` | componente-novo | LOW | 2 asserções trocadas; 5 testes da ligação com o lote |
| `docs/batch-generator.md` | `batch-generator` | componente-novo | LOW | Avaliação ao fim do lote e códigos 17 e 18 |
| `src/sintetica/quality/reader.py` | `quality-evaluator` (`_reversa_sdd/sdd/quality-evaluator.md#6`, RF-01) | componente-novo | MEDIUM | Leitura em fluxo de JSON, JSONL e CSV, com linhas ilegíveis como inválidas |
| `src/sintetica/quality/text.py`, `semantic.py` | `quality-evaluator` (RF-03, RF-04) | componente-novo | MEDIUM | Texto livre, 3-gramas de palavras e busca exata de quase-duplicados com filtro de prefixo |
| `src/sintetica/quality/metrics.py` | `quality-evaluator` (RF-01, RF-02, RF-05 a RF-08) e `pii-guard` | componente-novo | HIGH | Conformidade, unicidade estrutural, PII fora da allowlist, duração e veredito |
| `src/sintetica/quality/report.py` | `quality-evaluator` (RF-09, RF-10, `#9`) | componente-novo | HIGH | `report.json` e `report.md` do mesmo objeto; só a prévia dos achados de PII |
| `src/sintetica/quality/service.py`, `__init__.py` | `quality-evaluator` (RF-11, `#11`) | componente-novo | HIGH | Pré-condições, trava do lote, códigos 0, 17 e 18, avaliação ao fim do lote |
| `tests/quality/*.py` | `quality-evaluator` | componente-novo | LOW | 40 testes, mais 1 `perf` |
| `docs/quality-evaluator.md` | `quality-evaluator` | componente-novo | LOW | Fluxo da skill `sintetica-eval` |

## Diff conceitual por componente

**Comando `sintetica`.** Ganha `eval <slug>`, importado de forma tardia. Os códigos 17 (`REPROVADO`) e 18 (dataset final ausente ou ilegível) somam-se aos 0 e 2 a 16.

**batch-generator.** Em todo status final, depois do arquivo final, o `_execute` roda `evaluate_after_lot` dentro da trava do lote e acrescenta o bloco da avaliação à saída e ao `worker.log`. Um erro da avaliação vira aviso com o comando `sintetica eval`. O código de saída do `generate` não muda com o veredito. O `status` mostra "Avaliação: <veredito> (<caminho>)" quando `report.json` existe. A linha "Próximo passo: avaliação de qualidade" saiu.

**quality-evaluator.** Componente novo, conforme `_reversa_sdd/sdd/quality-evaluator.md`, com estes desvios:
- Unicidade semântica com busca exata por filtro de prefixo, no lugar do MinHash com LSH (D-07, aprovado pelo revisor).
- Código 17 para `REPROVADO` e 18 para dataset ausente (Q48), no lugar do código 2.
- O lote chama a avaliação ao terminar (Q49); `sintetica eval` serve para avaliação avulsa e CI.
- O volume da conformidade vem de `run.json`; sem ele, da intenção.
- `finished_at` fica só no relatório; a intenção não muda.
- Decisões novas da execução: linha inválida também passa pela busca de PII; JSON que não é lista dá o código 18.

## Preservadas

Nenhuma. Feature greenfield, sem regras 🟢 extraídas de código anterior.

## Modificadas

Nenhuma. Feature greenfield, sem regras 🟢 extraídas de código anterior.
