# ADR 003: Protocolo `request`/`submit` por arquivo com o harness

> Status: aceito (retroativo). Data da decisão: 2026-10-09 a 2026-10-12. Gerado pelo Detetive do Reversa.
> Confiança: 🟢 a decisão está registrada nas fontes e o código a confirma.

## Contexto

O runtime Python não tem como chamar o assistente do harness diretamente (Q29).

## Decisão

O runtime grava o pedido em `requests/<id>.json`; o agente gera os registros e os envia por `sintetica submit` (JSONL na entrada padrão, até 100 registros e 10 MiB). O id é o hash do pedido canônico.

## Consequências

Fronteira rastreável entre chat e runtime; pedido igual reaproveita a resposta, então tentativas e rodadas levam o seu número no texto. A resposta bruta é apagada depois de lida, porque pode ter PII.

## Fontes

Q29, Q33; `_reversa_forward/002-llm-provider/`, `005-sample-preview/` (decisão W006); `providers/harness/store.py`
