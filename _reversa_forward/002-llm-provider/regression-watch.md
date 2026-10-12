# Regression Watch: llm-provider

> Identificador: `002-llm-provider`
> Data: `2026-10-09`
> Feature greenfield. Não há regras 🟢 para vigiar: nada foi extraído de código existente. O watch principal fica vazio. Os requisitos implementados ficam em "Observações", sem peso de regressão, até uma extração `/reversa` futura confirmá-los como 🟢.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|-------------------------|-----------------------------|---------------------|-------------------|

## Observações

| ID | Origem (arquivo, seção) | Regra esperada | Tipo de verificação | Sinal de violação |
|----|-------------------------|----------------|---------------------|-------------------|
| W001 | `_reversa_forward/002-llm-provider/requirements.md#4` RN-03, RN-04 (Q30) | Todo pedido aos 4 backends externos, inclusive Ollama, passa pelo `MaskingProvider` quando `pii_premask` está ativo | presença | `build_provider` monta um `ExternalAPIProvider` sem `MaskingProvider` com `pii_premask: true` |
| W002 | `requirements.md#4` RN-03 (D-07) | Mascaramento indisponível bloqueia o envio | presença | Pedido enviado após `PolicyError` ou falha de escrita da allowlist |
| W003 | `requirements.md#4` RN-07 | Chaves de API nunca aparecem em mensagens, `repr`, logs ou arquivos | ausência | Valor de `*_API_KEY` em exceção, log ou arquivo em `datasets/` |
| W004 | `requirements.md#5` RF-07, RN-05 | Estimativa acima de `cost_ceiling_usd`, ou modelo sem preço, exige autorização; US$ 5,00 exatos não exigem | presença | `requires_authorization` falso para US$ 5,01 ou para modelo sem preço |
| W005 | `requirements.md#5` RF-08 (D-18) | O custo acumulado nunca passa do valor autorizado, inclusive com pedidos simultâneos | presença | `BudgetedProvider.spent_usd` maior que o autorizado |
| W006 | `requirements.md#5` RF-09, RF-10 (D-19) | 3 chamadas no total em falha temporária; 401 e 403 sem retry | presença | Mais de 3 chamadas, ou retry após 401/403 |
| W007 | `requirements.md#4` RN-02, RF-04, RF-14 (Q29) | Harness atende até 100 registros pelo protocolo `request`/`submit`; erro de `submit` não grava resposta | presença | Pedido de 101 registros aceito, ou `<id>.response.jsonl` gravado após erro |
| W008 | `requirements.md#4` RN-01 | Provedor escolhido pela ordem de `provider_priority`, pulando indisponíveis | presença | Escolha fora da ordem da política |
| W009 | `requirements.md#4` RN-08 (Q31, Q32, Q34) | Modelos padrão e preços só em `defaults.json`; `SINTETICA_*_MODEL` e `.sintetica/pricing.json` sobrescrevem | redação | Modelo ou preço fixo no código Python |
| W010 | `requirements.md#6` RNF de testabilidade | A suíte padrão roda sem rede | ausência | Teste fora de `@pytest.mark.live` que abre conexão real |

## Histórico de re-extrações

### Re-extração 2026-10-12 12:00

> Watch principal vazio (feature greenfield). Itens de "Observações" verificados de forma informativa, sem peso de regressão.

| ID | Veredito | Observação |
|----|----------|------------|
| W001 | 🟢 verde | regra presente em `_reversa_sdd/sdd/llm-provider.md` e `_reversa_sdd/domain.md` |
| W002 | 🟢 verde | regra presente em `_reversa_sdd/sdd/llm-provider.md` e `_reversa_sdd/domain.md` |
| W003 | 🟢 verde | regra presente em `_reversa_sdd/sdd/llm-provider.md` e `_reversa_sdd/domain.md` |
| W004 | 🟢 verde | regra presente em `_reversa_sdd/sdd/llm-provider.md` e `_reversa_sdd/domain.md` |
| W005 | 🟢 verde | regra presente em `_reversa_sdd/sdd/llm-provider.md` e `_reversa_sdd/domain.md` |
| W006 | 🟢 verde | regra presente em `_reversa_sdd/sdd/llm-provider.md` e `_reversa_sdd/domain.md` |
| W007 | 🟢 verde | regra presente em `_reversa_sdd/sdd/llm-provider.md` e `_reversa_sdd/domain.md` |
| W008 | 🟢 verde | regra presente em `_reversa_sdd/sdd/llm-provider.md` e `_reversa_sdd/domain.md` |
| W009 | 🟢 verde | regra presente em `_reversa_sdd/sdd/llm-provider.md` e `_reversa_sdd/domain.md` |
| W010 | 🟢 verde | regra presente em `_reversa_sdd/sdd/llm-provider.md` e `_reversa_sdd/domain.md` |

| Data | Resultado | Observação |
|------|-----------|------------|

## Arquivadas

| ID | Motivo | Data |
|----|--------|------|
