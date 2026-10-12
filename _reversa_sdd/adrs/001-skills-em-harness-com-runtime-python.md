# ADR 001: Skills em harnesses de IA com runtime Python local

> Status: aceito (retroativo). Data da decisão: 2026-10-09 a 2026-10-12. Gerado pelo Detetive do Reversa.
> Confiança: 🟢 a decisão está registrada nas fontes e o código a confirma.

## Contexto

O usuário quer descrever o dataset em linguagem natural dentro do assistente que já usa, sem programar geradores (Q1 a Q4).

## Decisão

Distribuir o produto como 5 skills no formato universal de Agent Skills, que chamam um runtime Python (`uv`, Pydantic v2, `asyncio`) por linha de comando (Q7, Q22).

## Consequências

O agente conduz a conversa e o runtime garante validação, privacidade e estado. Cada etapa é um comando com código de saída próprio.

## Fontes

Q2, Q7, Q22; `prd.md#4`; `src/sintetica/cli.py`
