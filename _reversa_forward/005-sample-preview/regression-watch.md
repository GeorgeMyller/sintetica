# Regression Watch: sample-preview

> Identificador: `005-sample-preview`
> Data: `2026-10-12`
> Feature greenfield. Não há regras 🟢 para vigiar. O watch principal fica vazio. Os requisitos implementados ficam em "Observações", sem peso de regressão, até uma extração `/reversa` futura confirmá-los como 🟢.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|-------------------------|-----------------------------|---------------------|-------------------|

## Observações

| ID | Origem (arquivo, seção) | Regra esperada | Tipo de verificação | Sinal de violação |
|----|-------------------------|----------------|---------------------|-------------------|
| W001 | `_reversa_forward/005-sample-preview/requirements.md#4` RN-01 | A amostra só começa com contrato aprovado e atual | presença | `sample run` com contrato em revisão devolve 0 |
| W002 | `requirements.md#4` RN-02 (Q41) | N de 3 a 5, padrão 3 | presença | Amostra com outro N padrão, ou N fora do intervalo aceito |
| W003 | `roadmap.md#3` D-03, R-01 | Cada tentativa gera pedido com id próprio | presença | `tests/sample/test_request.py::test_attempts_with_same_missing_count_get_distinct_ids` falha |
| W004 | `requirements.md#4` RN-04 | Inválidos e duplicados descartados; motivo sem o valor; até 3 tentativas por rodada | presença | Registro inválido na amostra mostrada, ou valor recebido no motivo |
| W005 | `requirements.md#4` RN-05 | Nenhum valor de PII não mascarado na tela, no estado, na semente ou em `requests/` | ausência | CPF original encontrado em qualquer arquivo do dataset |
| W006 | `actions.md#Notas de execução` (decisão da T013) | A resposta bruta do agente é apagada depois de lida | ausência | `requests/<id>.response.jsonl` presente após `sample run` processar a resposta |
| W007 | `requirements.md#4` RN-07 (Q42) | Semente em `seeds/sample.jsonl` com `seeds/sample.meta.json` | presença | Semente em outro formato ou sem metadados |
| W008 | `requirements.md#4` RN-08 (Q43) | Parcial aprovável no Guiado com alerta; Expresso para; vazia nunca é aprovada | presença | Expresso grava semente parcial sozinho |
| W009 | `requirements.md#4` RN-07 | Contrato com versão nova invalida a amostra | presença | `sample approve` aceita amostra de versão antiga |
| W010 | `interfaces/sample-cli.md#5` | Códigos 11, 12 e 13 exclusivos da amostra | redação | Colisão com os códigos 2 a 10 |

## Histórico de re-extrações

### Re-extração 2026-10-12 12:00

> Watch principal vazio (feature greenfield). Itens de "Observações" verificados de forma informativa, sem peso de regressão.

| ID | Veredito | Observação |
|----|----------|------------|
| W001 | 🟢 verde | regra presente em `_reversa_sdd/sdd/sample-preview.md` e `_reversa_sdd/domain.md` |
| W002 | 🟢 verde | regra presente em `_reversa_sdd/sdd/sample-preview.md` e `_reversa_sdd/domain.md` |
| W003 | 🟢 verde | regra presente em `_reversa_sdd/sdd/sample-preview.md` e `_reversa_sdd/domain.md` |
| W004 | 🟢 verde | regra presente em `_reversa_sdd/sdd/sample-preview.md` e `_reversa_sdd/domain.md` |
| W005 | 🟢 verde | regra presente em `_reversa_sdd/sdd/sample-preview.md` e `_reversa_sdd/domain.md` |
| W006 | 🟢 verde | regra presente em `_reversa_sdd/sdd/sample-preview.md` e `_reversa_sdd/domain.md` |
| W007 | 🟢 verde | regra presente em `_reversa_sdd/sdd/sample-preview.md` e `_reversa_sdd/domain.md` |
| W008 | 🟢 verde | regra presente em `_reversa_sdd/sdd/sample-preview.md` e `_reversa_sdd/domain.md` |
| W009 | 🟢 verde | regra presente em `_reversa_sdd/sdd/sample-preview.md` e `_reversa_sdd/domain.md` |
| W010 | 🟢 verde | regra presente em `_reversa_sdd/sdd/sample-preview.md` e `_reversa_sdd/domain.md` |

| Data | Resultado | Observação |
|------|-----------|------------|

## Arquivadas

| ID | Motivo | Data |
|----|--------|------|
