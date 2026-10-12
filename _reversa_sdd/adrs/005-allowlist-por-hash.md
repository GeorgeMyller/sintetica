# ADR 005: Allowlist por hash dos valores falsos

> Status: aceito (retroativo). Data da decisão: 2026-10-09 a 2026-10-12. Gerado pelo Detetive do Reversa.
> Confiança: 🟢 a decisão está registrada nas fontes e o código a confirma.

## Contexto

O usuário pode pedir campos de PII de propósito; o valor falso inserido não pode contar como vazamento (Q23, Q26).

## Decisão

Cada valor falso inserido grava o SHA-256 do valor normalizado em `.pii_allowlist`. Só conta como vazamento o achado fora dela.

## Consequências

A avaliação distingue dado falso de dado real sem guardar o valor. Sem a allowlist, todo achado conta.

## Fontes

Q23, Q26; `pii/allowlist.py`, `pii/normalize.py`
