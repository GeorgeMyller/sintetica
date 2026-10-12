# ADR 009: Amostra aprovada como semente do lote

> Status: aceito (retroativo). Data da decisão: 2026-10-09 a 2026-10-12. Gerado pelo Detetive do Reversa.
> Confiança: 🟢 a decisão está registrada nas fontes e o código a confirma.

## Contexto

Gerar milhares de registros sem validar o estilo antes é caro e arriscado (premissa 1 do PRD).

## Decisão

Amostra de 3 a 5 registros (padrão 3, Q41), até 3 tentativas por rodada, aprovada pelo usuário e gravada em `seeds/sample.jsonl` com `sample.meta.json` (Q42). Parcial: Guiado aprova com alerta, Expresso para (Q43).

## Consequências

O lote só começa com a amostra da versão atual do contrato e usa os registros dela como exemplos.

## Fontes

Q41 a Q43; `_reversa_forward/005-sample-preview/`; `sample/`
