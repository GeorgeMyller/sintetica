# ADR 006: Contrato declarativo com código gerado de forma determinística

> Status: aceito (retroativo). Data da decisão: 2026-10-09 a 2026-10-12. Gerado pelo Detetive do Reversa.
> Confiança: 🟢 a decisão está registrada nas fontes e o código a confirma.

## Contexto

O contrato precisa ser Pydantic v2, mas o runtime não pode executar código escrito pelo modelo.

## Decisão

O agente escreve só um rascunho JSON; o runtime valida, normaliza e gera o `schema.py` com textos escapados, cabeçalho de versão (SHA-256 do JSON canônico) e saída estável sob `ruff format`. O código gerado passa por `mypy --strict` nos testes (Q36).

## Consequências

Mesma definição, mesmo código, byte a byte. Contrato mudado invalida amostra e lote pela versão.

## Fontes

Q35 a Q37; `_reversa_forward/003-schema-builder/`; `schema/codegen.py`, `schema/version.py`
