# batch-generator

Geração do lote completo do dataset (1 a 10.000 registros). É a skill `sintetica-generate`. O runtime estima o custo, pede os registros ao provedor, valida cada um pelo contrato, descarta duplicados, troca dados pessoais por valores falsos e grava o progresso a cada bloco. No fim, gera `output/dataset.<ext>` no formato do contrato.

> No projeto do usuário, instalado por `npx sintetica install`, os comandos rodam pelo lançador `.sintetica/bin/sintetica` no lugar de `uv run sintetica` (`docs/cli-installer.md`).

## Pré-condições

- Contrato aprovado e atual (`docs/schema-builder.md`).
- Amostra aprovada para a mesma versão do contrato (`docs/sample-preview.md`).
- Volume e formato definidos na intenção.

## Fluxo para a skill `sintetica-generate`

1. Rode `uv run sintetica generate <slug>`. O provedor é escolhido pelo volume total do lote: acima de 100 registros, o harness nunca é usado.
2. Se a saída pedir autorização (código 15), mostre o valor ao usuário e pergunte. Com o sim, rode de novo com o valor:
   ```bash
   uv run sintetica generate <slug> --authorize-usd 6.00
   ```
   O custo acumulado nunca passa do valor autorizado.
3. Siga o caminho do provedor escolhido:
   - **Harness (até 100 registros):** a saída traz "Pedido para o agente" com 1 pedido de todo o volume. Gere os registros, envie com `uv run sintetica submit <slug> <id> < registros.jsonl` e rode `uv run sintetica generate <slug>` de novo. Cada rodada extra pede só os faltantes, com novo pedido.
   - **Ollama ou API externa, até 100 registros:** o lote roda em primeiro plano, com 1 linha de progresso por bloco.
   - **Acima de 100 registros:** o lote roda num processo separado e o comando devolve o controle em até 5 s. Acompanhe com `uv run sintetica status <slug>`.
4. No fim, mostre ao usuário o status, as contagens, o custo e o caminho do dataset. O lote já roda a avaliação de qualidade (`docs/quality-evaluator.md`): mostre também o veredito e o caminho de `report.md`. O código de saída do `generate` não muda com o veredito.

No Expresso, o lote começa sem pergunta. A única exceção é a autorização de custo.

## Regras

- Blocos: até 10 registros por pedido, reduzidos para a saída estimada ficar perto de 4.000 tokens (tamanho médio da amostra). `--block-size N` (1 a 100) define o bloco à mão.
- Cada registro é validado pelo contrato. Inválidos e duplicados exatos são descartados e repostos em até 3 rodadas extras.
- Dados pessoais viram valores falsos antes de ir ao disco. A resposta bruta do harness é apagada depois de lida. O log do background só tem contagens.
- Status final:
  - `concluido`: pelo menos 95% do volume pedido;
  - `incompleto`: menos de 95% depois das rodadas extras;
  - `interrompido_custo`: o teto de custo foi atingido;
  - `falha_provedor`: o provedor falhou depois das novas tentativas.
- Em todo status final, o arquivo `output/dataset.<ext>` é gerado com os registros aceitos.
- Só 1 lote por dataset roda de cada vez.

## Retomada e lote existente

| Situação | Comando |
|----------|---------|
| Processo encerrado, `falha_provedor`, `incompleto` | `uv run sintetica generate <slug> --resume` |
| `interrompido_custo` | `uv run sintetica generate <slug> --resume --authorize-usd <novo total>` |
| Gerar de novo depois de um lote (apaga `output/`) | `uv run sintetica generate <slug> --new` |

A retomada reconta `records.partial.jsonl` e pede só o restante. Os blocos já gravados não são pedidos de novo nem geram custo.

## Arquivos

| Arquivo | Conteúdo |
|---------|----------|
| `datasets/<slug>/output/run.json` | Status, contagens, custo, valor autorizado, provedor, bloco e rodada |
| `datasets/<slug>/output/records.partial.jsonl` | Registros aceitos e mascarados, gravados por bloco |
| `datasets/<slug>/output/dataset.<ext>` | Lista JSON, JSONL ou CSV com cabeçalho na ordem do contrato (RFC 4180) |
| `datasets/<slug>/output/worker.log` | Progresso do processo em background |
| `datasets/<slug>/output/run.lock` | Trava do lote |
| `datasets/<slug>/report.json` e `report.md` | Avaliação de qualidade do fim do lote; `sintetica status` mostra o veredito |

## Códigos de saída

| Código | Significado |
|--------|-------------|
| 0 | Sucesso, aguardando o agente, background iniciado, ou fim com `concluido`, `incompleto` ou `interrompido_custo` |
| 2 | Dataset, intenção ou argumento inválido |
| 9 | Mascaramento de PII indisponível |
| 10 | Falha de escrita |
| 11 | Contrato não aprovado ou desatualizado |
| 12 | Falha do provedor (inclusive o status final `falha_provedor`) |
| 14 | Amostra ausente ou de outra versão do contrato |
| 15 | Custo exige autorização |
| 16 | Lote em andamento, interrompido ou já existente |

Os códigos 17 (`REPROVADO`) e 18 (dataset final ausente) são só do `sintetica eval` (`docs/quality-evaluator.md`).
