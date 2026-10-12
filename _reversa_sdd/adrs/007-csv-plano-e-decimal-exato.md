# ADR 007: CSV plano e decimal exato

> Status: aceito (retroativo). Data da decisão: 2026-10-09 a 2026-10-12. Gerado pelo Detetive do Reversa.
> Confiança: 🟢 a decisão está registrada nas fontes e o código a confirma.

## Contexto

CSV não tem aninhamento; decimais em ponto flutuante perdem precisão (Q35, Q37).

## Decisão

Objeto vira colunas com prefixo; lista simples vira 1 coluna com `|`; lista de objetos é recusada. Decimal sai como número exato em JSON/JSONL e com casas fixas em CSV.

## Consequências

Valores com `|` em listas CSV são recusados. A serialização usa marcador com nonce para manter o número exato.

## Fontes

Q35, Q37; `schema/csvflat.py`, `schema/formats.py`
