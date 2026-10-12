## Módulo `sample`

### `SampleState` (`state.py:31`) — `datasets/<slug>/sample.state.json`

| Campo | Tipo | Obrigatório | Padrão | Regra |
|-------|------|-------------|--------|-------|
| `status` | `aguardando_agente \| em_revisao \| aprovada \| interrompida` | sim | — | — |
| `n` | `int` | sim | — | 3 a 5 |
| `schema_version` | `str` | sim | — | Versão do contrato da rodada |
| `round` | `int` | não | 0 | +1 a cada ajuste |
| `attempt` | `int` | não | 0 | 0 a 3 na rodada |
| `adjustment` | `str \| null` | não | `null` | Já mascarado |
| `pending_request_id`, `pending_command` | `str \| null` | não | `null` | Pedido do harness pendente |
| `accepted` | `list[str]` | não | `[]` | Linhas JSONL canônicas, já mascaradas |
| `rejected` | `list[str]` | não | `[]` | Motivos, nunca valores |
| `provider`, `provider_reason` | `str \| null` | não | `null` | — |
| `updated_at` | `str` | não | agora | ISO 8601 UTC |

### `SampleMeta` (`state.py:54`) — `seeds/sample.meta.json`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `schema_version` | `str` | Versão do contrato da amostra (conferida pelo lote) |
| `approved_at` | `str` | ISO 8601 UTC |
| `provider` | `str` | Ex.: `harness` |
| `n_requested`, `n_records` | `int` | Pedidos e aprovados |
| `partial` | `bool` | `n_records < n_requested` |
| `rounds` | `int` | Rodadas de ajuste até a aprovação |

### `seeds/sample.jsonl`

🟢 1 registro aprovado por linha, via `to_jsonl_line` (decimal exato). Usado como sementes pelo lote (Q42).

### `ReviewResult` (`review.py:19`)

| Campo | Tipo |
|-------|------|
| `accepted` | `list[str]` (linhas JSONL mascaradas) |
| `rejected` | `list[str]` (motivos) |
