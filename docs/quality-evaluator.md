# quality-evaluator

Avaliação de qualidade do dataset final. É a skill `sintetica-eval`. O runtime lê `output/dataset.<ext>`, valida cada registro pelo contrato atual, mede 4 números e dá o veredito `APROVADO` ou `REPROVADO`. A avaliação é local: 0 chamadas de rede e nenhuma alteração no dataset.

> No projeto do usuário, instalado por `npx sintetica install`, os comandos rodam pelo lançador `.sintetica/bin/sintetica` no lugar de `uv run sintetica` (`docs/cli-installer.md`).

## Quando roda

- **No fim do lote:** `sintetica generate` roda a avaliação sozinho, em primeiro plano e em background, em todo status final. O código de saída do `generate` não muda com o veredito.
- **Avulsa ou em CI:** `uv run sintetica eval <slug>`.

## Fluxo para a skill `sintetica-eval`

1. Rode `uv run sintetica eval <slug>` se o usuário pedir uma nova avaliação. Depois de um lote, leia o bloco de avaliação na saída do `generate` ou rode `uv run sintetica status <slug>`.
2. Mostre ao usuário o veredito, os 4 números, a duração e o caminho de `report.md`.
3. Com `REPROVADO`, explique as métricas que falharam e sugira o ajuste:
   - **conformidade:** retome o lote com `--resume` ou revise o contrato;
   - **unicidade:** ajuste a amostra (`sintetica sample adjust`) ou a intenção, para pedir mais variação;
   - **PII:** abra `report.md` e veja índice, campo e tipo de cada achado.

## Métricas

| Métrica | Cálculo | Meta |
|---------|---------|------|
| Conformidade | Registros válidos pelo contrato atual ÷ volume pedido pelo lote (`run.json`; sem ele, a intenção) | ≥ 95% |
| Unicidade estrutural | Registros distintos pelo JSON canônico ÷ registros lidos | ≥ 90% |
| Unicidade semântica | Registros com texto livre que não são quase-duplicados ÷ registros com texto livre | ≥ 90% |
| Vazamentos de PII | Achados do `PiiGuard` fora da allowlist de valores falsos | 0 |

- Quase-duplicado: 3-gramas de palavras do texto livre normalizado (minúsculas, sem pontuação), com Jaccard ≥ 0,8 em relação a um registro anterior. Texto com menos de 3 palavras vira 1 trecho. Campos `enum`, números e datas ficam fora.
- Contrato sem campo de texto livre: unicidade semântica "não aplicável", fora do veredito.
- Linha ilegível, JSON quebrado ou CSV com colunas a mais ou a menos contam como inválidos.
- Duração: de `started_at` da intenção até a emissão do relatório. A meta de tempo (< 10 min) só vale para volume ≤ 100 e não entra no veredito.

## Arquivos

| Arquivo | Conteúdo |
|---------|----------|
| `datasets/<slug>/report.json` | Veredito, métricas, achados de PII (só a prévia), duração, status do lote, avisos e índices dos registros com problema (a partir de 0) |
| `datasets/<slug>/report.md` | Os mesmos números para leitura, com a seção "Escopo e limites da detecção de PII" |

## Códigos de saída de `sintetica eval`

| Código | Significado |
|--------|-------------|
| 0 | `APROVADO` |
| 2 | Dataset, intenção ou argumento inválido |
| 9 | Detecção de PII indisponível (nenhum relatório gravado) |
| 10 | Falha ao gravar o relatório |
| 11 | Contrato ausente ou ilegível |
| 16 | Lote em andamento |
| 17 | `REPROVADO` |
| 18 | Dataset final ausente ou ilegível |
