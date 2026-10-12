# Interface: `sintetica generate` e `sintetica status` (geração do lote)

> Tipo: arquivo + CLI. Origem: RN-01 a RN-12, RF-01 a RF-16, D-02 a D-22. Confidência: 🟡.

## 1. `sintetica generate`

```
uv run sintetica generate <slug> [--resume] [--new] [--authorize-usd <valor>]
                                 [--block-size 1..100] [--project-dir <dir>]
```

| Situação | Resultado | Código de saída |
|----------|-----------|-----------------|
| Dataset ou intenção ausente; volume ou formato indefinido; argumento inválido | Erro | 2 |
| Contrato não aprovado ou desatualizado | Erro que cita `sintetica schema approve` ou `build` | 11 |
| Amostra ausente ou aprovada para outra versão do contrato | Erro que cita `sintetica sample run` | 14 |
| Custo estimado acima do teto, ou preço desconhecido, sem `--authorize-usd` | 0 pedidos; mostra o valor e o comando com `--authorize-usd` | 15 |
| Lote em andamento (trava ocupada) | Mostra o status atual | 16 |
| Lote interrompido (`em_andamento` sem processo, `falha_provedor`) sem `--resume` | Sugere `--resume` | 16 |
| Lote com status final sem `--new` | Sugere `--new` (apaga `output/` e começa de novo) | 16 |
| Harness: pedido gravado sem resposta | `aguardando_agente`; caminho do pedido e comando `submit` | 0 |
| Volume > 100 | Inicia o processo separado; mostra o PID e `sintetica status <slug>` em ≤ 5 s | 0 |
| Fim com `concluido`, `incompleto` ou `interrompido_custo` | Contagens, custo, caminho absoluto de `dataset.<ext>` e o próximo passo (avaliação de qualidade) | 0 |
| Fim com `falha_provedor` | Mensagem do provedor, blocos gravados e comando `--resume` | 12 |
| Mascaramento indisponível | Bloco não gravado; lote para | 9 |
| Falha de escrita | Parcial truncado ao último bloco íntegro; caminho e causa | 10 |

- 🟡 `--resume` reconta `records.partial.jsonl` e pede só o restante; o teto passa a ser `autorizado − custo já gasto`.
- 🟡 `--authorize-usd` aceita valor decimal positivo; valor abaixo da estimativa gera aviso de que o lote pode parar com `interrompido_custo`.
- 🟡 `--block-size` vale só para provedor automático; com o harness, é ignorado com aviso.
- 🟡 Com o harness, rodar `generate <slug>` de novo lê a resposta e segue para a próxima rodada; não precisa de `--resume`.

Saída em primeiro plano, 1 linha por bloco:

```
Lote do dataset <slug>: 50 registros em JSON (provedor ollama: <motivo>)
Estimativa: US$ 0,00; bloco de 10 registros
Bloco 1/5, 10 válidos, 0 descartados, US$ 0,00
...
Lote concluido: 50 de 50 registros válidos (0 inválidos, 1 duplicado descartado), custo US$ 0,00
Dataset: /caminho/absoluto/datasets/<slug>/output/dataset.json
Próximo passo: avaliação de qualidade (feature quality-evaluator).
```

Saída com autorização necessária:

```
Custo estimado US$ 6,00 acima do teto de US$ 5,00. Nenhum pedido foi enviado.
Para autorizar: uv run sintetica generate <slug> --authorize-usd 6.00
```

## 2. `sintetica status`

```
uv run sintetica status <slug> [--project-dir <dir>]
```

| Situação | Resultado | Código de saída |
|----------|-----------|-----------------|
| Dataset ausente | Erro | 2 |
| Sem lote | "nenhum lote iniciado" | 16 |
| Lote em andamento com processo vivo | Status, aceitos/volume, descartados, custo, provedor, bloco, rodada | 0 |
| `em_andamento` com a trava livre | "processo encerrado" e comando `--resume` | 0 |
| Status final | Resumo e caminho do dataset | 0 |

## 3. Processo em background (interno)

```
<python do ambiente> -m sintetica.batch.worker <project_dir> <slug>
```

- 🟡 Sessão própria, entrada nula, saída em `output/worker.log`; herda a trava em POSIX (D-15, D-16).
- 🟡 Não é comando para o usuário nem para o agente.

## 4. Idempotência e concorrência

- 🟡 1 lote por dataset (`output/run.lock`).
- 🟡 Pedidos do harness têm id pelo conteúdo; a rodada no texto garante id novo por rodada.
- 🟡 A retomada nunca repete um bloco gravado nem gera custo por ele.

## 5. Códigos de saída do comando `sintetica`

| Código | Significado | Origem |
|--------|-------------|--------|
| 0 | Sucesso | todas |
| 2 | Dataset, intenção ou argumento inválido | 002 a 006 |
| 3, 4, 5 | Protocolo do harness | 002 |
| 6, 7 | Contrato de schema | 003 |
| 8 | Resposta inválida na entrevista | 004 |
| 9 | Mascaramento de PII indisponível | 004 a 006 |
| 10 | Falha de escrita | 004 a 006 |
| 11 | Contrato não aprovado ou desatualizado | 005, 006 |
| 12 | Falha do provedor | 005, 006 |
| 13 | Amostra não aprovável no estado atual | 005 |
| 14 | Amostra ausente ou de outra versão do contrato | 006 |
| 15 | Custo exige autorização | 006 |
| 16 | Lote em andamento, interrompido ou já existente | 006 |
