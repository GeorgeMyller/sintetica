# ADR 002: Porta `LLMProvider` com escolha por política

> Status: aceito (retroativo). Data da decisão: 2026-10-09 a 2026-10-12. Gerado pelo Detetive do Reversa.
> Confiança: 🟢 a decisão está registrada nas fontes e o código a confirma.

## Contexto

A geração precisa funcionar sem chave (amostra e testes) e em alta vazão (lotes grandes) (Q8).

## Decisão

Uma porta `LLMProvider` com 2 famílias de adaptadores: o agente do harness e as APIs externas (OpenAI, Anthropic, Gemini, Ollama). A ordem vem de `provider_priority` (padrão harness → ollama → external).

## Consequências

O mesmo código de amostra e lote serve a qualquer provedor. Lotes acima de 100 registros nunca vão ao harness.

## Fontes

Q8, Q28; `_reversa_forward/002-llm-provider/`; `providers/factory.py`, `providers/selection.py`
