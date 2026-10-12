# ADR 014: Avaliação determinística e local, sem LLM-juiz

> Status: aceito (retroativo). Data da decisão: 2026-10-09 a 2026-10-12. Gerado pelo Detetive do Reversa.
> Confiança: 🟢 a decisão está registrada nas fontes e o código a confirma.

## Contexto

As métricas do PRD precisam ser verificáveis e reprodutíveis (Q5, Q16).

## Decisão

Conformidade, unicidade estrutural (hash) e semântica (Jaccard ≥ 0,8 em 3-gramas de palavras do texto livre, Q27, Q47) e vazamentos de PII, com busca exata por filtro de prefixo no lugar do MinHash (D-07). `REPROVADO` termina com 17 e dataset ausente com 18 (Q48). O lote roda a avaliação no fim (Q49).

## Consequências

Mesmo dataset, mesmo relatório (exceto data e duração). Não há medida de diversidade temática.

## Fontes

Q16, Q27, Q47 a Q49; `_reversa_forward/007-quality-evaluator/`; `quality/`
