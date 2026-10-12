# Regression Watch: batch-generator

> Identificador: `006-batch-generator`
> Data: `2026-10-12`
> Feature greenfield. Não há regras 🟢 para vigiar. O watch principal fica vazio. Os requisitos implementados ficam em "Observações", sem peso de regressão, até uma extração `/reversa` futura confirmá-los como 🟢.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|-------------------------|-----------------------------|---------------------|-------------------|

## Observações

| ID | Origem (arquivo, seção) | Regra esperada | Tipo de verificação | Sinal de violação |
|----|-------------------------|----------------|---------------------|-------------------|
| W001 | `_reversa_forward/006-batch-generator/requirements.md#4` RN-01 | O lote só começa com contrato aprovado e atual e amostra da mesma versão | presença | `generate` com amostra de outra versão devolve 0 |
| W002 | `requirements.md#4` RN-02 | O provedor é escolhido pelo volume total, nunca pelo bloco | presença | `build_provider` chamado com o tamanho do bloco; lote acima de 100 vai ao harness |
| W003 | `requirements.md#4` RN-03 (Q44) | Harness: 1 pedido por rodada, com id novo por rodada | presença | `tests/batch/test_cli.py::test_harness_lot_end_to_end` falha |
| W004 | `requirements.md#4` RN-04 | Custo acima do teto ou preço desconhecido: 0 pedidos sem `--authorize-usd`; custo ≤ valor autorizado | presença | Pedido enviado antes da autorização, ou `cost_usd` acima de `authorized_usd` |
| W005 | `requirements.md#4` RN-05 (Q45) | Acima de 100 registros, o comando volta em ≤ 5 s e o `status` detecta processo encerrado | presença | `test_background.py` falha |
| W006 | `requirements.md#4` RN-06 (Q46) | Bloco de até 10, perto de 4.000 tokens de saída; `--block-size` vence | presença | Bloco acima de 10 sem `--block-size` |
| W007 | `requirements.md#4` RN-08 | Nenhum valor de PII não mascarado no disco: parcial, dataset, `run.json`, log, `requests/` | ausência | CPF original encontrado em qualquer arquivo do dataset |
| W008 | `roadmap.md#3` D-04 | A resposta bruta do harness é apagada depois de lida | ausência | `requests/<id>.response.jsonl` presente após o `generate` processar a resposta |
| W009 | `requirements.md#4` RN-09 | Retomada sem repetir blocos gravados e sem duplicados | presença | `test_engine.py::test_provider_failure_keeps_blocks_and_resume_finishes` falha |
| W010 | `requirements.md#4` RN-10 | Status final pela conformidade de 95%; arquivo final gerado em todo status final | presença | Status `concluido` com menos de 95%, ou dataset ausente após `incompleto` |
| W011 | `requirements.md#4` RN-11 | Só 1 lote por dataset (trava de arquivo) | presença | 2º `generate` com o lote rodando devolve 0 |
| W012 | `actions.md#Notas de execução` (decisão da T023) | Sementes do prompt sem `Decimal`; provedor simulado monta o prompt real | presença | `TypeError: Object of type Decimal` no `worker.log` |
| W013 | `actions.md#Notas de execução` (decisão da T023) | Erro inesperado no background registra só o nome da exceção | ausência | Traceback no `worker.log` |
| W014 | `interfaces/generate-cli.md#5` | Códigos 14, 15 e 16 exclusivos do lote | redação | Colisão com os códigos 2 a 13 |

## Histórico de re-extrações

### Re-extração 2026-10-12 12:00

> Watch principal vazio (feature greenfield). Itens de "Observações" verificados de forma informativa, sem peso de regressão.

| ID | Veredito | Observação |
|----|----------|------------|
| W001 | 🟢 verde | regra presente em `_reversa_sdd/sdd/batch-generator.md` e `_reversa_sdd/domain.md` |
| W002 | 🟢 verde | regra presente em `_reversa_sdd/sdd/batch-generator.md` e `_reversa_sdd/domain.md` |
| W003 | 🟢 verde | regra presente em `_reversa_sdd/sdd/batch-generator.md` e `_reversa_sdd/domain.md` |
| W004 | 🟢 verde | regra presente em `_reversa_sdd/sdd/batch-generator.md` e `_reversa_sdd/domain.md` |
| W005 | 🟢 verde | regra presente em `_reversa_sdd/sdd/batch-generator.md` e `_reversa_sdd/domain.md` |
| W006 | 🟢 verde | regra presente em `_reversa_sdd/sdd/batch-generator.md` e `_reversa_sdd/domain.md` |
| W007 | 🟢 verde | regra presente em `_reversa_sdd/sdd/batch-generator.md` e `_reversa_sdd/domain.md` |
| W008 | 🟢 verde | regra presente em `_reversa_sdd/sdd/batch-generator.md` e `_reversa_sdd/domain.md` |
| W009 | 🟢 verde | regra presente em `_reversa_sdd/sdd/batch-generator.md` e `_reversa_sdd/domain.md` |
| W010 | 🟢 verde | regra presente em `_reversa_sdd/sdd/batch-generator.md` e `_reversa_sdd/domain.md` |
| W011 | 🟢 verde | regra presente em `_reversa_sdd/sdd/batch-generator.md` e `_reversa_sdd/domain.md` |
| W012 | 🟡 amarelo | Correção registrada em `actions.md` e coberta por teste; a spec `sdd/batch-generator.md` não descreve o detalhe de serialização das sementes |
| W013 | 🟢 verde | regra presente em `_reversa_sdd/sdd/batch-generator.md` e `_reversa_sdd/domain.md` |
| W014 | 🟢 verde | regra presente em `_reversa_sdd/sdd/batch-generator.md` e `_reversa_sdd/domain.md` |

| Data | Resultado | Observação |
|------|-----------|------------|

## Arquivadas

| ID | Motivo | Data |
|----|--------|------|
