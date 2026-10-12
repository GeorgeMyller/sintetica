# Interface: `sintetica request` / `sintetica submit` (protocolo do harness)

> Tipo: arquivo + CLI. Origem: Q29, RN-02, RF-04, RF-14. Confidência: 🟢 no protocolo (Q29), 🟡 nos detalhes.

## 1. `sintetica request`

```
uv run sintetica request <slug> --n-records <N> --instructions <texto> --schema <arquivo.json> [--seeds <arquivo.jsonl>] [--project-dir <dir>]
```

| Item | Regra |
|------|-------|
| `<slug>` | Pasta `datasets/<slug>/` existente (criada pelo `intent-interview`). Ausente: erro, código de saída 2 |
| `--n-records` | 1 a 100. Acima de 100: `HarnessLimitExceeded`, código de saída 3, nada gravado |
| Saída em arquivo | `datasets/<slug>/requests/<id>.json` |
| Saída padrão | Bloco legível para o agente: id, número de registros, caminho do pedido e o comando `submit` exato |
| Idempotência | Mesmo conteúdo → mesmo `<id>`; arquivo existente não é reescrito |
| Código de saída | 0 em sucesso |

Conteúdo do pedido:

```json
{
  "version": 1,
  "id": "3f9a1c0b7e21",
  "created_at": "2026-10-09T18:00:00Z",
  "n_records": 5,
  "instructions": "…",
  "schema_json": { "…": "…" },
  "seeds": [ { "…": "…" } ],
  "response_format": "1 objeto JSON por linha (JSONL), sem texto extra"
}
```

🟡 `id` = 12 primeiros caracteres hex do SHA-256 de `{n_records, instructions, schema_json, seeds}` em JSON canônico. `created_at` não entra no hash.

## 2. `sintetica submit`

```
<JSONL na entrada padrão> | uv run sintetica submit <slug> <id>
```

| Situação | Resultado | Código de saída |
|----------|-----------|-----------------|
| Pedido `<id>` inexistente | Erro "pedido inexistente"; nada gravado | 4 |
| Linha que não é objeto JSON | Erro com o número da linha; nada gravado | 5 |
| 0 linhas, ou mais linhas que `n_records` | Erro com a contagem; nada gravado | 5 |
| 1 a `n_records` linhas válidas | Grava `<id>.response.jsonl` (escrita atômica) e mostra a contagem | 0 |
| Resposta já existe para `<id>` | Substitui (o agente pode corrigir a resposta) e avisa | 0 |

🟡 Linhas em branco são ignoradas. Entrada maior que 10 MB é recusada (código 5).

## 3. Leitura pelo `HarnessAgentProvider`

1. `generate(request)` calcula o `<id>`.
2. Com `<id>.response.jsonl` presente: devolve `GenerationResult(records, input_tokens=ceil(len(pedido)/4), output_tokens=ceil(len(resposta)/4), cost_usd=0, provider="harness")`.
3. Sem resposta: grava o pedido (se ainda não existe) e levanta `HarnessResponsePending(request_id, command)`.
4. `n_records > 100`: levanta `HarnessLimitExceeded` antes de gravar.

## 4. Segurança

- 🟡 O pedido não passa pelo mascaramento: o harness não é provedor externo (Q30, D-05).
- 🟡 Os arquivos ficam em `datasets/`, que está no `.gitignore`.
