# Regression Watch: quality-evaluator

> Identificador: `007-quality-evaluator`
> Data: `2026-10-12`
> Feature greenfield. Não há regras 🟢 para vigiar. O watch principal fica vazio. Os requisitos implementados ficam em "Observações", sem peso de regressão, até uma extração `/reversa` futura confirmá-los como 🟢.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|-------------------------|-----------------------------|---------------------|-------------------|

## Observações

| ID | Origem (arquivo, seção) | Regra esperada | Tipo de verificação | Sinal de violação |
|----|-------------------------|----------------|---------------------|-------------------|
| W001 | `_reversa_forward/007-quality-evaluator/requirements.md#4` RN-01 | Conformidade = válidos pelo contrato atual ÷ volume pedido pelo lote | presença | Conformidade calculada sobre os registros lidos |
| W002 | `requirements.md#4` RN-02 | Unicidade estrutural por hash do JSON canônico | presença | `test_metrics.py::test_structural_uniqueness_with_exact_copies` falha |
| W003 | `requirements.md#4` RN-03 (Q47) | 3-gramas de palavras do texto livre; menos de 3 palavras vira 1 trecho; `enum`, números e datas fora | presença | `test_text.py` falha |
| W004 | `roadmap.md#3` D-07 | Busca de quase-duplicados exata: filtro de prefixo igual ao par a par | presença | `test_semantic.py::test_prefix_filter_matches_pairwise` falha |
| W005 | `requirements.md#4` RN-05 | Vazamento = achado fora da allowlist; sem allowlist, todo achado conta | presença | Valor falso registrado contado como vazamento |
| W006 | `requirements.md#4` RN-05 | O relatório e a saída nunca mostram o valor completo de um achado de PII | ausência | Valor completo em `report.md`, `report.json`, saída ou `worker.log` |
| W007 | `requirements.md#4` RN-07 | Veredito `APROVADO` só com todas as metas; semântica "não aplicável" fora do veredito | presença | `APROVADO` com conformidade < 95% |
| W008 | `requirements.md#4` RN-08 | A avaliação não altera o dataset nem chama a rede | ausência | `output/dataset.<ext>` alterado após `sintetica eval` |
| W009 | `requirements.md#4` RN-10 (Q48) | `sintetica eval`: 0 `APROVADO`, 17 `REPROVADO`, 18 dataset ausente | redação | Código 2 para `REPROVADO` |
| W010 | `requirements.md#4` RN-11 (Q49) | O fim do lote roda a avaliação; o código do `generate` não muda | presença | `tests/batch/test_quality_chain.py` falha |
| W011 | `requirements.md#5` RF-15 | `report.json` igual entre execuções, exceto data e duração | presença | `test_report.py::test_report_is_deterministic` falha |
| W012 | `actions.md#Notas de execução` (decisão da T013) | Linha inválida também passa pela busca de PII | presença | PII em linha inválida não contada |
| W013 | `requirements.md#6` RNF de desempenho | 10.000 registros avaliados em ≤ 120 s | presença | `tests/quality/test_perf.py` falha |

## Histórico de re-extrações

### Re-extração 2026-10-12 12:00

> Watch principal vazio (feature greenfield). Itens de "Observações" verificados de forma informativa, sem peso de regressão.

| ID | Veredito | Observação |
|----|----------|------------|
| W001 | 🟢 verde | regra presente em `_reversa_sdd/sdd/quality-evaluator.md` e `_reversa_sdd/domain.md` |
| W002 | 🟢 verde | regra presente em `_reversa_sdd/sdd/quality-evaluator.md` e `_reversa_sdd/domain.md` |
| W003 | 🟢 verde | regra presente em `_reversa_sdd/sdd/quality-evaluator.md` e `_reversa_sdd/domain.md` |
| W004 | 🟢 verde | regra presente em `_reversa_sdd/sdd/quality-evaluator.md` e `_reversa_sdd/domain.md` |
| W005 | 🟢 verde | regra presente em `_reversa_sdd/sdd/quality-evaluator.md` e `_reversa_sdd/domain.md` |
| W006 | 🟢 verde | regra presente em `_reversa_sdd/sdd/quality-evaluator.md` e `_reversa_sdd/domain.md` |
| W007 | 🟢 verde | regra presente em `_reversa_sdd/sdd/quality-evaluator.md` e `_reversa_sdd/domain.md` |
| W008 | 🟢 verde | regra presente em `_reversa_sdd/sdd/quality-evaluator.md` e `_reversa_sdd/domain.md` |
| W009 | 🟢 verde | regra presente em `_reversa_sdd/sdd/quality-evaluator.md` e `_reversa_sdd/domain.md` |
| W010 | 🟢 verde | regra presente em `_reversa_sdd/sdd/quality-evaluator.md` e `_reversa_sdd/domain.md` |
| W011 | 🟢 verde | regra presente em `_reversa_sdd/sdd/quality-evaluator.md` e `_reversa_sdd/domain.md` |
| W012 | 🟢 verde | regra presente em `_reversa_sdd/sdd/quality-evaluator.md` e `_reversa_sdd/domain.md` |
| W013 | 🟢 verde | regra presente em `_reversa_sdd/sdd/quality-evaluator.md` e `_reversa_sdd/domain.md` |

| Data | Resultado | Observação |
|------|-----------|------------|

## Arquivadas

| ID | Motivo | Data |
|----|--------|------|
