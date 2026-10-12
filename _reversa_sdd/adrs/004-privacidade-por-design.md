# ADR 004: Privacidade por design: mascarar antes de gravar e de enviar

> Status: aceito (retroativo). Data da decisão: 2026-10-09 a 2026-10-12. Gerado pelo Detetive do Reversa.
> Confiança: 🟢 a decisão está registrada nas fontes e o código a confirma.

## Contexto

O usuário pode digitar dados reais; os modelos podem gerar dados reais (Q15, Q21).

## Decisão

Detecção local e determinística de 7 tipos de PII; troca por valor falso do mesmo formato; mascaramento da intenção, de cada registro aceito e de todo pedido a provedor automático, inclusive o Ollama (Q30). Política inválida bloqueia a gravação.

## Consequências

Nenhum dado pessoal detectável chega ao disco ou a uma API. A métrica de vazamento cobre só o que os detectores cobrem (Q9).

## Fontes

Q9, Q15, Q21, Q25, Q30; `_reversa_forward/001-pii-guard/`; `pii/`, `providers/decorators/masking.py`
