# Relatório de confiança: sintetica

> Gerado pelo Revisor do Reversa em 2026-10-12. Nível: completo. Re-extração completa sobre um projeto greenfield com 8 features entregues pelo ciclo forward.
> Contagem de selos por arquivo (inclui a legenda do cabeçalho, quando houver).

## 1. Specs SDD (`sdd/`, versão 2.0)

| Spec | 🟢 | 🟡 | 🔴 | % 🟢 |
|------|----|----|----|------|
| `pii-guard.md` | 43 | 0 | 1 | 97,7% |
| `llm-provider.md` | 53 | 2 | 0 | 96,4% |
| `schema-builder.md` | 41 | 2 | 0 | 95,3% |
| `intent-interview.md` | 36 | 1 | 0 | 97,3% |
| `sample-preview.md` | 35 | 4 | 0 | 89,7% |
| `batch-generator.md` | 47 | 4 | 0 | 92,2% |
| `quality-evaluator.md` | 42 | 0 | 0 | 100,0% |
| `cli-installer.md` | 43 | 3 | 0 | 93,5% |
| **Total** | **340** | **16** | **1** | **95,2%** |

🟢 Todos os requisitos funcionais (133 no total) têm selo 🟢 CONFORME CÓDIGO com arquivo e linha de origem. Os 🟡 e 🔴 ficam nas seções de lacunas, edge cases e RNF de portabilidade.

## 2. Artefatos transversais

| Artefato | 🟢 | 🟡 | 🔴 |
|----------|----|----|----|
| `code-analysis.md` | 119 | 6 | 1 |
| `domain.md` | 78 | 5 | 0 |
| `architecture.md` | 21 | 5 | 1 (legenda) |
| `state-machines.md` | 7 | 0 | 0 |
| `permissions.md` | 10 | 1 | 0 |
| `adrs/` (15) | 15 | 0 | 0 |

## 3. Verificações feitas

- 🟢 Amostra de afirmações conferida contra o código: referências de `sample/service.py`, `batch/service.py`, `batch/engine.py`, `quality/service.py` e `*/request.py`.
- 🟢 1 referência de linha corrigida (`batch/service.py:500-505` → `505-509`) em `sdd/batch-generator.md`, `code-analysis.md`, `architecture.md`, `domain.md` e `modules.json`.
- 🟢 1 inconsistência real encontrada e registrada (G-03, Q55).
- 🟢 Matriz código/spec: 98 de 100 arquivos mapeados; os 2 restantes (`__init__.py`, `py.typed`) não têm comportamento.
- 🟢 Matriz de impacto conferida contra as importações reais.
- 🟢 Units esperadas (`surface.json.modules`): 8 módulos, 8 specs.

## 4. Reclassificações

| De → Para | Quantidade | Itens |
|-----------|-----------|-------|
| 🟢 → 🟡 | 1 | Instrução de formato da amostra (G-03) |
| 🔴 → 🟡 | 1 lacuna (4 selos) | Windows experimental (G-01, Q53) |
| 🔴 → 🟢 | 1 lacuna (2 selos) | Diversidade temática fora do MVP (G-02, Q54) |
| 🟡 → 🟢 | 0 | G-03 e G-04 continuam 🟡 até a correção no código (Q55, Q56) |

## 5. Verificação de regressão (8 features)

| Feature | Itens | 🟢 | 🟡 | 🔴 |
|---------|-------|----|----|----|
| 001-pii-guard | 10 | 9 | 1 (W009) | 0 |
| 002-llm-provider | 10 | 10 | 0 | 0 |
| 003-schema-builder | 10 | 10 | 0 | 0 |
| 004-intent-interview | 10 | 9 | 1 (W007) | 0 |
| 005-sample-preview | 10 | 10 | 0 | 0 |
| 006-batch-generator | 14 | 13 | 1 (W012) | 0 |
| 007-quality-evaluator | 13 | 13 | 0 | 0 |
| 008-cli-installer | 13 | 13 | 0 | 0 |
| **Total** | **90** | **87** | **3** | **0** |

🟢 Os watch principais estão vazios (features greenfield); os itens de "Observações" foram verificados de forma informativa, sem peso de regressão. O histórico foi gravado em cada `regression-watch.md`.

🟢 Adendos `001` a `008` marcados como "Superado pela re-extração de 2026-10-12".

## 6. Revisão cruzada

- Engine externa consultada: nenhuma (plugin do Codex indisponível nesta sessão).

## 7. Perguntas

| Geradas | Respondidas | Pendentes |
|---------|-------------|-----------|
| 4 (Q53 a Q56) | 4 | 0 |

## 8. Confiança geral

**95,2%** de afirmações 🟢 nas specs; **0** regressões; **0** lacunas 🔴 abertas. O único 🔴 restante nas specs é um limite de escopo aceito (`pii-guard`: nomes e endereços). Há 2 correções decididas e pendentes no código (G-03 e G-04).
