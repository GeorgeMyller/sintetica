---
name: sintetica-generate
description: Gera o lote completo (1 a 10.000 registros) do dataset do sintetica, com estimativa e autorização de custo, execução em background e retomada. Use depois da amostra aprovada (sintetica-sample).
---

# sintetica-generate: lote completo

O runtime estima o custo, pede os registros ao provedor da política, valida, descarta duplicados, mascara dados pessoais e grava o progresso a cada bloco. No fim, gera `output/dataset.<ext>` e roda a avaliação de qualidade. Rode os comandos na raiz do projeto, pelo lançador `.sintetica/bin/sintetica`.

## Passos

1. Inicie o lote:
   ```bash
   .sintetica/bin/sintetica generate <slug>
   ```
2. Código 15 (custo acima do teto, ou preço desconhecido): mostre o valor ao usuário e pergunte. Com o "sim", rode de novo com o valor:
   ```bash
   .sintetica/bin/sintetica generate <slug> --authorize-usd 6.00
   ```
3. Siga o caminho da saída:
   - "Pedido para o agente" (até 100 registros, harness): leia o pedido, gere os registros, envie com `.sintetica/bin/sintetica submit <slug> <id> < registros.jsonl` e rode `generate <slug>` de novo, até o fim.
   - "Lote em background" (acima de 100 registros): o comando volta logo. Acompanhe com `.sintetica/bin/sintetica status <slug>`.
   - Linhas "Bloco N/M": o lote roda em primeiro plano; aguarde o fim.
4. No fim, mostre ao usuário o status, as contagens, o custo, o caminho do dataset e o veredito da avaliação (`report.md`).

## Retomada e lote existente

| Situação | Comando |
|----------|---------|
| `status` mostra "Processo encerrado", `falha_provedor` ou `incompleto` | `.sintetica/bin/sintetica generate <slug> --resume` |
| `interrompido_custo` | `.sintetica/bin/sintetica generate <slug> --resume --authorize-usd <novo total>` |
| Gerar de novo um lote já concluído (apaga `output/`) | `.sintetica/bin/sintetica generate <slug> --new` |

- `--block-size N` (1 a 100) muda o número de registros por pedido; use só se o usuário pedir.
- No Expresso, o lote começa sem pergunta; a única exceção é a autorização de custo.

## Códigos de saída

| Código | Significado |
|--------|-------------|
| 0 | Sucesso, aguardando o agente, background iniciado, ou fim com `concluido`, `incompleto` ou `interrompido_custo` |
| 2 | Dataset, intenção ou argumento inválido |
| 9 | Mascaramento de PII indisponível |
| 10 | Falha de escrita |
| 11 | Contrato não aprovado ou desatualizado |
| 12 | Falha do provedor (inclui o status final `falha_provedor`) |
| 14 | Amostra ausente ou de outra versão do contrato |
| 15 | Custo exige autorização |
| 16 | Lote em andamento, interrompido ou já existente |
