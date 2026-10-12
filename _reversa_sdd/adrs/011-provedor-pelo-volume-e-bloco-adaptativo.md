# ADR 011: Provedor pelo volume total e bloco adaptativo

> Status: aceito (retroativo). Data da decisão: 2026-10-09 a 2026-10-12. Gerado pelo Detetive do Reversa.
> Confiança: 🟢 a decisão está registrada nas fontes e o código a confirma.

## Contexto

A seleção do provedor recebe o número de registros do pedido; blocos de 10 fariam um lote de 10.000 cair no harness. Registros longos estouram a saída (OQ-02).

## Decisão

O lote escolhe o provedor pelo volume total. Harness: 1 pedido por rodada (Q44). Automático: bloco de até 10 registros, reduzido para ~4.000 tokens de saída, com `--block-size` (Q46).

## Consequências

Lotes grandes vão a Ollama ou API externa. Conversas longas usam blocos menores.

## Fontes

Q44, Q46; `batch/plan.py`, `batch/service.py`
