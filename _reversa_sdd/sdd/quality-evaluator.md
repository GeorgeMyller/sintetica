# Spec: quality-evaluator

> Selo 🟢 CONFORME CÓDIGO em todos os itens, salvo marcação. Fonte: `src/sintetica/quality/`, testes `tests/quality/` e `tests/batch/test_quality_chain.py`.
> Consolida os adendos `007-quality-evaluator.md` e `008-cli-installer.md` (mensagens). Versão planejada em `sdd/_planejado/quality-evaluator.md`.

**Versão:** 2.0 (extraída do código)
**Status:** Implementado
**Autor:** reversa-writer
**Data:** 2026-10-12

---

## 1. Resumo

🟢 O `quality-evaluator` é o pacote `sintetica.quality` e a skill `sintetica-eval`. Ele lê `output/dataset.<ext>` em fluxo, valida cada registro pelo contrato atual e mede conformidade, unicidade estrutural, unicidade semântica e vazamentos de PII. Calcula a duração desde `started_at`, dá o veredito `APROVADO` ou `REPROVADO` e grava `report.json` e `report.md`. Roda no fim do lote e pelo comando `sintetica eval`. É local e não altera o dataset.

## 2. Contexto

🟢 As métricas do PRD precisam ser verificáveis (Q5, Q9, Q16, Q20). A CI do usuário precisa de um código de saída (spec RF-11, Q48).

## 3. Goals

- 🟢 G-01: Medir as 4 métricas em todo dataset gerado.
- 🟢 G-02: Avaliar 10.000 registros de ~1 KB em ≤ 120 s (medido: ~4 s).
- 🟢 G-03: Mesmo dataset, mesmo relatório (exceto data e duração).

## 4. Non-Goals

- 🟢 NG-01: Sem LLM-juiz; sem correção automática; sem comparação com dados reais.

## 5. Usuários

🟢 As 3 personas (veredito); CI (código de saída e `report.json`); `batch` (`status`).

## 6. Requisitos Funcionais

| ID | Requisito | Critério de aceite | Fonte |
|----|-----------|--------------------|-------|
| RF-01 | 🟢 Pré-condições: dataset e intenção (2); `schema.json` e `Record` legíveis (11); no comando avulso, trava do lote ocupada = 16; `output/dataset.<ext>` ausente = 18 (cita `generate` e `--resume`); `PiiGuard` indisponível = 9 sem relatório | — | `service.py:83-160` |
| RF-02 | 🟢 Leitura em fluxo: JSONL por linha (vazias ignoradas; inválida fica inválida); lista JSON com decimal exato (não lista = 18); CSV pelo `csv.reader`, células comparadas ao cabeçalho, convertidas pelo contrato (vazio → `None` ou `[]`; lista por `|`) | Índices a partir de 0 | `reader.py` |
| RF-03 | 🟢 Conformidade = `min(válidos, volume) ÷ volume`, 1 casa (`ROUND_HALF_UP`); volume de `run.json`, ou da intenção sem ele; divergência gera aviso | 96 de 100 = 96,0% | `service.py:131-144`, `197`, `metrics.py:47-51` |
| RF-04 | 🟢 Unicidade estrutural = registros sem cópia exata (SHA-256 da linha canônica ou bruta) ÷ lidos | 100 com 5 cópias = 95,0% | `metrics.py:73-80` |
| RF-05 | 🟢 Texto livre: campos `text` (inclusive em listas e objetos), na ordem do contrato; conversa: `messages[].content` + `text` dos rótulos; `enum`, números e datas fora; normalização (minúsculas, pontuação Unicode → espaço, espaços únicos); 3-gramas de palavras; < 3 palavras = 1 trecho | Q47 | `text.py` |
| RF-06 | 🟢 Quase-duplicado: Jaccard ≥ 0,8 (em inteiros) com algum registro anterior; até 1.000, par a par; acima, filtro de prefixo exato (AllPairs); só o posterior conta | Q27, D-07 | `semantic.py` |
| RF-07 | 🟢 Unicidade semântica = (com texto − quase-duplicados) ÷ com texto; sem texto livre no contrato = "não aplicável", fora do veredito | — | `service.py:199-203` |
| RF-08 | 🟢 PII: cada texto do registro válido (texto livre e `enum`) com o caminho do campo passa por `leaks`; linha inválida passa inteira (campo `registro`); cada achado guarda índice, campo, tipo e prévia | — | `metrics.py:84-96` |
| RF-09 | 🟢 Duração em minutos com 1 casa de `started_at` à emissão; sem `started_at` = não medida; meta < 10 min só para volume ≤ 100, fora do veredito | Q20 | `metrics.py:99-114` |
| RF-10 | 🟢 Veredito `APROVADO` só com conformidade ≥ 95%, unicidades ≥ 90% e 0 vazamentos; métricas que falharam em ordem fixa | — | `metrics.py:117-129` |
| RF-11 | 🟢 Avisos: lote não `concluido`, contrato mudado depois do lote, volume divergente, `run.json` ausente ou ilegível, allowlist ausente | — | `service.py:96-100`, `161-176` |
| RF-12 | 🟢 `report.json` (decimais como número exato) e `report.md` do mesmo objeto, com métricas, avisos, até 20 índices por tipo e "Escopo e limites da detecção de PII" | Gravação atômica; falha = 10 | `report.py` |
| RF-13 | 🟢 Saída: veredito, 5 linhas de métricas com `[ok]`/`[falhou]`, avisos, caminho absoluto de `report.md` | — | `report.py:93-122`, `service.py:225-231` |
| RF-14 | 🟢 Códigos: 0 `APROVADO`, 17 `REPROVADO` | Q48 | `service.py:244-250` |
| RF-15 | 🟢 `evaluate_after_lot`: mesma avaliação sem checar a trava; erro vira 1 linha de aviso com o comando `eval` | Q49 | `service.py:253-259` |

## 7. Requisitos Não-Funcionais

| ID | Requisito | Evidência |
|----|-----------|-----------|
| RNF-01 | 🟢 Desempenho: 10.000 registros em ≤ 120 s | Teste `perf` (~4 s) |
| RNF-02 | 🟢 Determinismo | `test_report_is_deterministic` |
| RNF-03 | 🟢 0 chamadas de rede; dataset não alterado | `service.py` |
| RNF-04 | 🟢 Privacidade: só a prévia de cada achado | `report.py:30-36` |

## 8. Interface

```
uv run sintetica eval <slug>
```

| Código | Significado |
|--------|-------------|
| 0 | `APROVADO` |
| 2 | Dataset, intenção ou argumento inválido |
| 9 | Detecção de PII indisponível |
| 10 | Falha ao gravar o relatório |
| 11 | Contrato ausente ou ilegível |
| 16 | Lote em andamento |
| 17 | `REPROVADO` |
| 18 | Dataset final ausente ou ilegível |

## 9. Modelo de Dados

🟢 `Report` (`verdict`, `failed_metrics`, volumes e contagens, percentuais, `pii_findings`, `pii_coverage`, `duration_min`, `time_target_met`, `run_status`, `schema_version`, `warnings`, `problem_indices`, `finished_at`). Detalhe em `data-dictionary.md#módulo-quality`.

## 10. Integrações

🟢 `schema`, `intent`, `pii`, `batch` (`state`, `lock`), `sample` (`first_error`, `CommandResult`).

## 11. Edge Cases

| Cenário | Comportamento |
|---------|---------------|
| 🟢 Dataset vazio | Conformidade 0,0%; `REPROVADO` |
| 🟢 Linha corrompida | Inválida com índice |
| 🟢 Contrato só numérico | Semântica "não aplicável" |
| 🟢 Allowlist ausente | Todo achado conta; aviso |
| 🟢 Contrato mudou depois do lote | Aviso; avalia com o atual |
| 🟢 `schema.py` editado | Regerado pela carga do contrato |

## 12. Segurança

- 🟢 Relatório e saída nunca mostram o valor completo de um achado.

## 13. Decisões (consolidadas)

| Decisão | Fonte |
|---------|-------|
| 🟢 3-gramas de palavras do texto livre | Q27, Q47 |
| 🟢 Busca exata por filtro de prefixo no lugar do MinHash | D-07 (feature 007), ADR 014 |
| 🟢 Códigos 17 e 18 | Q48 |
| 🟢 Avaliação no fim do lote | Q49 |
| 🟢 Sem LLM-juiz | NG-01, OQ-02 |

## 14. Lacunas

- 🟢 Diversidade temática fora do MVP: as métricas vigentes são as unicidades (Q16); dispersão temática fica no roadmap (Q54).

## Histórico

| Versão | Data | Mudança |
|--------|------|---------|
| 1.0 | 2026-10-09 | Spec planejada (`_planejado/`) |
| 2.0 | 2026-10-12 | Reescrita conforme o código; adendos 007 e 008 consolidados |
