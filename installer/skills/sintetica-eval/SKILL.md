---
name: sintetica-eval
description: Avalia a qualidade do dataset final do sintetica (conformidade, unicidade estrutural e semântica, vazamentos de PII) e explica o veredito. Use depois do lote, ou quando o usuário pedir uma nova avaliação.
---

# sintetica-eval: avaliação de qualidade

O lote já roda a avaliação no fim. Use esta skill para explicar o resultado ou para avaliar de novo. A avaliação é local e não altera o dataset. Rode os comandos na raiz do projeto, pelo lançador `.sintetica/bin/sintetica`.

## Passos

1. Avalie (ou leia o bloco de avaliação na saída do `generate`):
   ```bash
   .sintetica/bin/sintetica eval <slug>
   ```
2. Mostre ao usuário o veredito, os 4 números, a duração e o caminho de `datasets/<slug>/report.md`.
3. Com `REPROVADO`, explique as métricas que falharam e sugira o ajuste:
   - conformidade: retome o lote (`.sintetica/bin/sintetica generate <slug> --resume`) ou revise o contrato;
   - unicidade: ajuste a amostra (`.sintetica/bin/sintetica sample adjust <slug> '<pedido>'`) para pedir mais variação;
   - PII: abra `report.md` e mostre índice, campo e tipo de cada achado (nunca o valor).
4. Para ver o veredito junto do progresso do lote: `.sintetica/bin/sintetica status <slug>`.

## Métricas

| Métrica | Meta |
|---------|------|
| Conformidade (válidos ÷ volume pedido) | ≥ 95% |
| Unicidade estrutural (registros distintos) | ≥ 90% |
| Unicidade semântica (texto livre sem quase-duplicados) | ≥ 90% |
| Vazamentos de PII | 0 |

A meta de tempo (menos de 10 min até 100 registros) aparece no relatório e não entra no veredito.

## Códigos de saída

| Código | Significado |
|--------|-------------|
| 0 | `APROVADO` |
| 2 | Dataset, intenção ou argumento inválido |
| 9 | Detecção de PII indisponível |
| 10 | Falha ao gravar o relatório |
| 11 | Contrato ausente ou ilegível |
| 16 | Lote em andamento |
| 17 | `REPROVADO` |
| 18 | Dataset final ausente ou ilegível |
