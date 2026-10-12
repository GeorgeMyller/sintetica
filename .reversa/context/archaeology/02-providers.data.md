## Módulo `providers`

### `GenerationRequest` (dataclass imutável, `domain.py:18`)

| Campo | Tipo | Obrigatório | Regra |
|-------|------|-------------|-------|
| `schema_json` | `Mapping[str, object]` | sim | JSON Schema do registro |
| `seeds` | `Sequence[Mapping[str, object]]` | sim | Exemplos; podem ter PII até o mascaramento |
| `instructions` | `str` | sim | Texto livre do pedido |
| `n_records` | `int` | sim | ≥ 1 (`ValueError` abaixo disso) |

### `GenerationResult` (`domain.py:32`)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `records` | `tuple[dict, ...]` | Registros brutos, ainda não validados pelo contrato |
| `input_tokens`, `output_tokens` | `int` | Tokens informados pela API (estimados no harness) |
| `cost_usd` | `Decimal` | Custo real |
| `provider` | `str` | Nome do provedor |
| `stop_reason` | `str \| None` | `"teto de custo"` quando o teto bloqueou o pedido |

### `CostEstimate` (`domain.py:44`)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `provider`, `model` | `str`, `str \| None` | Provedor e modelo |
| `n_records`, `avg_tokens` | `int` | Base da estimativa |
| `usd` | `Decimal` | Estimativa (0 se local ou preço desconhecido) |
| `requires_authorization` | `bool` | Acima do teto, ou preço desconhecido |
| `price_known` | `bool` | Padrão `True` |

### `ProviderChoice` (`domain.py:55`)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `provider` | `str` | `harness`, `ollama` ou `external` |
| `backend` | `str \| None` | `openai`, `anthropic`, `gemini`, `ollama` ou `None` (harness) |
| `reason` | `str` | Pulados e escolhido, separados por `;` |
| `skipped` | `tuple[str, ...]` | Motivos dos pulados |

### `ModelPrice` (`domain.py:65`)

| Campo | Tipo |
|-------|------|
| `input_usd_per_token`, `output_usd_per_token` | `Decimal` |

### `ProviderPolicy` (`policy.py:24`) — chaves de `.sintetica/policy.json`

| Chave | Tipo | Padrão | Validação |
|-------|------|--------|-----------|
| `pii_premask` | `bool` | `true` | Booleano |
| `cost_ceiling_usd` | número ou texto numérico | `5.00` | Finito, ≥ 0 |
| `provider_priority` | lista | `["harness", "ollama", "external"]` | Não vazia; só valores conhecidos |
| (outras chaves) | — | — | Ignoradas (ex.: `telemetry`) |

### `.sintetica/pricing.json` e `data/defaults.json`

🟢 Objeto `modelo → {input_usd_per_token, output_usd_per_token}` (números ou textos); `pricing.json` sobrescreve por modelo. `defaults.json` também tem `models: backend → modelo`.

### Pedido do harness `datasets/<slug>/requests/<id>.json`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `version` | `int` | 1 |
| `id` | `str` | 12 hex do SHA-256 do pedido canônico |
| `created_at` | `str` | ISO 8601 UTC |
| `n_records`, `instructions`, `schema_json`, `seeds` | — | Pedido canônico |
| `response_format` | `str` | "1 objeto JSON por linha (JSONL), sem texto extra" |

### Resposta `requests/<id>.response.jsonl`

🟢 1 objeto JSON por linha, de 1 a `n_records` linhas, UTF-8, até 10 MiB. Apagada pelos consumidores (`sample`, `batch`) depois de lida.

### Variáveis de ambiente

| Variável | Uso |
|----------|-----|
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` | Chaves; lidas por chamada |
| `SINTETICA_EXTERNAL_BACKEND` | Força o backend externo (se tiver chave) |
| `SINTETICA_<BACKEND>_MODEL` | Troca o modelo padrão |
| `OLLAMA_HOST` | Endereço do Ollama (padrão `http://localhost:11434`) |
