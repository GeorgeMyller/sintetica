# ADR 012: Background por processo separado e trava de arquivo

> Status: aceito (retroativo). Data da decisão: 2026-10-09 a 2026-10-12. Gerado pelo Detetive do Reversa.
> Confiança: 🟢 a decisão está registrada nas fontes e o código a confirma.

## Contexto

Lotes acima de 100 registros não podem prender o chat (Q28).

## Decisão

Processo `python -m sintetica.batch.worker` em sessão própria, com o PID em `run.json` (Q45). Uma trava de arquivo (`flock`/`msvcrt`), herdada pelo processo filho, garante 1 lote por dataset e detecta processo encerrado sem depender do PID.

## Consequências

`status` mostra o progresso e sugere `--resume`. O ramo Windows não tem teste real.

## Fontes

Q28, Q45; `_reversa_forward/006-batch-generator/` (D-15, D-16); `batch/lock.py`, `batch/background.py`
