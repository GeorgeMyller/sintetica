# ADR 010: Lote durável: gravação por bloco e retomada pelo arquivo parcial

> Status: aceito (retroativo). Data da decisão: 2026-10-09 a 2026-10-12. Gerado pelo Detetive do Reversa.
> Confiança: 🟢 a decisão está registrada nas fontes e o código a confirma.

## Contexto

Lotes de até 10.000 registros podem cair no meio (G-03 da spec).

## Decisão

Cada bloco é anexado com `fsync` a `records.partial.jsonl` antes do `run.json`; erro trunca ao bloco anterior. A retomada reconta o arquivo, descarta linha incompleta e não repete custo.

## Consequências

O arquivo parcial é a fonte da verdade. O status final segue a meta de 95% do PRD.

## Fontes

`_reversa_forward/006-batch-generator/` (D-12, D-13); `batch/output.py`
