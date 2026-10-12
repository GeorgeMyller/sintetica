## Módulo `batch`

### `RunState` (`state.py:48`) — `datasets/<slug>/output/run.json`

| Campo | Tipo | Obrigatório | Padrão | Regra |
|-------|------|-------------|--------|-------|
| `slug` | `str` | sim | — | — |
| `status` | `iniciando \| em_andamento \| aguardando_agente \| concluido \| incompleto \| interrompido_custo \| falha_provedor` | sim | — | 4 últimos são finais |
| `mode` | `foreground \| background` | não | `foreground` | — |
| `pid` | `int \| null` | não | `null` | Gravado pelo processo em background |
| `volume_requested` | `int ≥ 1` | sim | — | Volume do lote |
| `format` | `csv \| json \| jsonl` | sim | — | Do contrato |
| `accepted` | `int ≥ 0` | não | 0 | Espelho do arquivo parcial |
| `discarded_invalid`, `discarded_duplicate` | `int ≥ 0` | não | 0 | — |
| `round` | `int` | não | 0 | 0 a 4 |
| `block_size` | `int` | sim | — | 1 a 100 |
| `avg_tokens` | `int ≥ 1` | sim | — | Média da amostra |
| `estimate_usd` | `Decimal \| null` | não | `null` | `null` com preço desconhecido |
| `authorized_usd` | `Decimal \| null` | não | `null` | Valor autorizado ou teto da política |
| `cost_usd` | `Decimal` | não | 0 | Custo real acumulado |
| `provider`, `provider_reason` | `str` | sim | — | — |
| `schema_version` | `str` | sim | — | Versão do contrato do lote |
| `pending_request_id`, `pending_command` | `str \| null` | não | `null` | Só com o harness |
| `stop_cause` | `str \| null` | não | `null` | Sem valores de registro |
| `started_at`, `updated_at` | `str` | não | agora | ISO 8601 UTC |
| `finished_at` | `str \| null` | não | `null` | — |

🟢 Decimais gravados como texto exato (`"0.42"`, modo JSON do Pydantic).

### Arquivos em `datasets/<slug>/output/`

| Arquivo | Conteúdo |
|---------|----------|
| `records.partial.jsonl` | Registros aceitos e mascarados, 1 por linha, anexados por bloco com `fsync` |
| `dataset.<ext>` | Lista JSON, JSONL ou CSV (cabeçalho, `\r\n`, RFC 4180) |
| `run.lock` | Trava (conteúdo vazio) |
| `worker.log` | Progresso do background, sem valores de registro |

### `BlockReview` (`review.py:49`)

| Campo | Tipo |
|-------|------|
| `accepted` | `list[str]` |
| `invalid`, `duplicate` | `int` |
| `reasons` | `list[str]` (motivos, sem valores) |

### `DedupIndex` (`review.py:23`)

🟢 2 conjuntos de SHA-256 (32 bytes): linhas mascaradas e linhas brutas. Só em memória; reconstruído do arquivo parcial (só as mascaradas) na retomada.
