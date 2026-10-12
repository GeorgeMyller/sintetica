# ADR 013: Teto de custo com autorização explícita

> Status: aceito (retroativo). Data da decisão: 2026-10-09 a 2026-10-12. Gerado pelo Detetive do Reversa.
> Confiança: 🟢 a decisão está registrada nas fontes e o código a confirma.

## Contexto

O custo de tokens recai sobre o usuário (Q17).

## Decisão

Estimativa pelo preço de saída (lado seguro, Q33); acima de US$ 5,00 ou com preço desconhecido, o comando para sem pedir nada e mostra o valor; o agente pergunta e roda de novo com `--authorize-usd`. Um decorador reserva a previsão antes de cada pedido e para no teto.

## Consequências

O gasto real nunca passa do autorizado; a retomada desconta o já gasto.

## Fontes

Q17, Q31 a Q34; `providers/decorators/budget.py`, `batch/service.py`
