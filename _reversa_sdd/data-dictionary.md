# Dicionário de dados: sintetica

> Gerado pelo Arqueólogo do Reversa em 2026-10-12. Nível: completo.
> Confiança: 🟢 CONFIRMADO (todos os itens lidos do código), salvo marcação.
> Não há banco de dados: as entidades são modelos Pydantic, dataclasses e arquivos JSON/JSONL por dataset em `datasets/<slug>/`.

## Mapa de arquivos por dataset

| Arquivo | Entidade | Módulo dono |
|---------|----------|-------------|
| `intent.json` | `IntentModel` | `intent` |
| `schema.draft.json`, `schema.json` | `SchemaSpecModel` | `schema` |
| `schema.state.json` | `SchemaState` | `schema` |
| `schema.py`, `record.schema.json` | `Record` gerado e JSON Schema | `schema` |
| `.pii_allowlist` | hashes SHA-256 | `pii` |
| `requests/<id>.json`, `<id>.response.jsonl` | pedido e resposta do harness | `providers` |
| `sample.state.json` | `SampleState` | `sample` |
| `seeds/sample.jsonl`, `seeds/sample.meta.json` | semente e `SampleMeta` | `sample` |
| `output/run.json` | `RunState` | `batch` |
| `output/records.partial.jsonl`, `output/dataset.<ext>`, `output/run.lock`, `output/worker.log` | lote | `batch` |
| `report.json`, `report.md` | `Report` | `quality` |

Arquivos do projeto: `.sintetica/policy.json` (`providers`, `pii`), `.sintetica/pricing.json` (`providers`), `.sintetica/state.json`, `.sintetica/install-manifest.json`, `.sintetica/bin/`, `.sintetica/runtime/` (`installer`).

## Módulo `pii`

### `PiiType` (enum, `domain.py:10`)

| Valor | Observação |
|-------|------------|
| `cpf`, `cnpj`, `email`, `phone`, `card`, `ipv4`, `ipv6` | `FIXED_TYPES`, os 7 tipos fixos (Q9) |
| `custom` | Padrões extras de `pii_custom_patterns` |

### `PiiFinding` (dataclass imutável, `domain.py:35`)

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `type` | `PiiType` | sim | Tipo detectado |
| `start` | `int` | sim | Índice inicial, inclusivo |
| `end` | `int` | sim | Índice final, exclusivo |
| `field` | `str \| None` | sim | Caminho do campo (ex.: `end.cidade`, `tags[]`) |
| `preview` | `str` | sim | 2 primeiros caracteres + `***`; nunca o valor completo |

### `MaskResult` (`domain.py:46`)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `text` | `str` | Texto mascarado |
| `counts` | `Mapping[PiiType, int]` | Achados trocados por tipo |
| `fallbacks` | `int` | Trocas por `***` (substituto indisponível) |

### `Coverage` (`domain.py:55`)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `types` | `tuple[PiiType, ...]` | Os 7 tipos fixos |
| `custom_patterns` | `int` | Número de padrões extras |
| `limits` | `tuple[str, ...]` | 6 limites conhecidos |

### `PolicyError` (exceção, `domain.py:63`)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `index` | `int` | Padrão com problema, ou -1 para o arquivo |

### Arquivo `datasets/<slug>/.pii_allowlist`

🟢 Texto UTF-8, 1 SHA-256 hexadecimal por linha, do valor falso normalizado por tipo. Só cresce (anexo com `fsync`).

### Chave `pii_custom_patterns` de `.sintetica/policy.json`

🟢 Lista de regex não vazias, até 200 caracteres cada, compiláveis pelo `re`. Ausente vale `[]`.


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


## Módulo `schema`

### `SchemaSpecModel` (`spec.py:56`) — `schema.draft.json` e `schema.json`

| Campo | Tipo | Obrigatório | Padrão | Regra |
|-------|------|-------------|--------|-------|
| `model_name` | `"Record"` | não | `Record` | Fixo |
| `format` | `csv \| json \| jsonl` | sim | — | Igual ao da intenção |
| `kind` | `records \| conversation` | não | `records` | Conversa só em JSON/JSONL |
| `fields` | `list[FieldSpecModel]` | sim | — | ≥ 1; até 100 no total |

### `FieldSpecModel` (`spec.py:44`)

| Campo | Tipo | Obrigatório | Padrão | Regra |
|-------|------|-------------|--------|-------|
| `name` | `str` | sim (fora de item de lista) | `""` | Normalizado para snake_case ASCII |
| `type` | `text \| int \| decimal \| bool \| date \| datetime \| enum \| list \| object` | sim | — | — |
| `required` | `bool` | não | `true` | Opcional vira `\| None = None` |
| `description` | `str` | não | `""` | Entra no código por `py_str` |
| `constraints` | `Constraints` | não | vazio | Permitidas por tipo |
| `items` | `FieldSpecModel` | só em `list` | — | Obrigatório em `list` |
| `fields` | `list[FieldSpecModel]` | só em `object` | — | ≥ 1 em `object` |

### `Constraints` (`spec.py:28`)

| Campo | Tipo | Tipos aceitos |
|-------|------|---------------|
| `ge`, `le` | `bool \| int \| float \| str` | `int`, `decimal` (número), `date`, `datetime` (ISO 8601) |
| `min_length`, `max_length` | `int ≥ 0` | `text`, `list` |
| `pattern` | `str` | `text` (re do Python e validador do Pydantic) |
| `choices` | `list[str]` | `enum` (obrigatório, sem vazios e sem repetidos) |
| `casas_decimais` | `int` (0 a 10) | `decimal` |

### `SchemaState` (`state.py:36`) — `schema.state.json`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `status` | `em_revisao \| aprovado` | Estado da revisão |
| `rounds` | `int` | Rodadas de ajuste (versões novas) |
| `schema_version` | `str` | SHA-256 do contrato |
| `approved_at` | `str \| null` | ISO 8601 UTC |
| `warnings` | `list[str]` | Avisos do último `build` |

### `SchemaIssue` (`spec.py:18`)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `path` | `str` | Caminho do campo (`itens[].sku`, `fields[2].name`) |
| `message` | `str` | Problema |

### Arquivos gerados por dataset

| Arquivo | Conteúdo |
|---------|----------|
| `schema.json` | Definição final (normalizada; plana em CSV), `sort_keys`, indentada |
| `schema.py` | Código gerado; cabeçalho `# schema_version: <sha256>`; classe `Record` |
| `record.schema.json` | JSON Schema do `Record` (usado nos pedidos de geração) |
| `errors.log` | Tracebacks de falhas do código gerado |
| `.schema.staged.py` | Arquivo de preparo; some depois do `build` |

### `Intent` local (`intent.py:21`)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `slug` | `str` | Do `intent.json`, ou o nome da pasta |
| `mode` | `guiado \| expresso` | — |
| `format` | `csv \| json \| jsonl` | Obrigatório |
| `structure_defined` | `bool` | Falso só com `structure.status = "indefinido"` |


## Módulo `intent`

### `IntentModel` (`model.py:46`) — `datasets/<slug>/intent.json`

🟢 `extra="allow"`: chaves gravadas por outras features são preservadas.

| Campo | Tipo | Obrigatório | Padrão | Regra |
|-------|------|-------------|--------|-------|
| `slug` | `str` | sim | — | kebab-case ASCII, até 60 caracteres |
| `mode` | `guiado \| expresso` | não | `guiado` | — |
| `started_at` | `str` | sim | — | ISO 8601 UTC, gravado por `start` |
| `objective`, `structure`, `rules` | `Item` | não | `pendente` | Texto já mascarado |
| `format` | `csv \| json \| jsonl \| null` | não | `null` | Padrão por "não sei": `jsonl` |
| `format_source` | `usuario \| padrao \| null` | não | `null` | — |
| `volume` | `int \| null` | não | `null` | 1 a 10.000; padrão por "não sei": 10 |
| `volume_source` | `usuario \| padrao \| null` | não | `null` | — |
| `volume_rejections` | `int ≥ 0` | não | 0 | Zera ao aceitar; na 3ª recusa vale o padrão |
| `pii_masked` | `bool` | não | `false` | Alguma resposta teve PII trocada |
| `confirmed_at` | `str \| null` | não | `null` | Zerado por qualquer resposta nova |

### `Item` (`model.py:39`)

| Campo | Tipo | Padrão | Valores |
|-------|------|--------|---------|
| `status` | `str` | `pendente` | `pendente`, `definido`, `indefinido` |
| `text` | `str \| null` | `null` | Só com `definido` |

### `Answers` (`answers.py:71`)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `texts` | `dict[str, str]` | `objective`, `structure`, `rules` |
| `format`, `volume` | `str \| None` | Como digitado pelo usuário |
| `unknown` | `set[str]` | Itens respondidos com "não sei" |

### `Question` (`questions.py:11`)

| Campo | Tipo |
|-------|------|
| `item`, `text` | `str` |
| `examples` | `tuple[str, ...]` (1 por persona) |


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


## Módulo `quality`

### `Report` (`report.py:48`) — `datasets/<slug>/report.json`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `slug` | `str` | — |
| `verdict` | `APROVADO \| REPROVADO` | — |
| `failed_metrics` | `list[conformidade \| unicidade_estrutural \| unicidade_semantica \| pii]` | Ordem fixa |
| `volume_requested`, `records_read`, `valid_records` | `int` | — |
| `conformity_pct`, `structural_uniqueness_pct` | `Decimal` (1 casa) | — |
| `semantic_uniqueness_pct` | `Decimal \| null` | `null` = não aplicável |
| `semantic_applicable` | `bool` | Contrato com texto livre |
| `pii_leaks` | `int` | — |
| `pii_findings` | `list[PiiFindingOut]` | Índice, campo, tipo, prévia |
| `pii_coverage` | `PiiCoverage` | Tipos, padrões extras, limites |
| `duration_min` | `Decimal \| null` | `null` = não medida |
| `time_target_met` | `bool \| null` | Só para volume ≤ 100 |
| `run_status` | `str \| null` | Status de `run.json` |
| `schema_version` | `str` | Contrato usado |
| `warnings` | `list[str]` | — |
| `problem_indices` | `ProblemIndices` | `invalid`, `duplicates`, `near_duplicates`, `pii` (a partir de 0) |
| `finished_at` | `str` | ISO 8601 UTC |

🟢 Decimais gravados como número exato (`90.0`). `report.md` traz os mesmos números.

### `PiiFindingOut` (`report.py:30`)

| Campo | Tipo |
|-------|------|
| `index` | `int` |
| `field` | `str` (`registro` em linha inválida) |
| `type` | `str` |
| `preview` | `str` (2 caracteres + `***`) |

### `Item` (`reader.py:30`)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `index` | `int` | Posição, a partir de 0 |
| `record` | `BaseModel \| None` | Registro válido |
| `canonical` | `str` | Linha canônica (válido) ou bruta (inválido) |
| `reason` | `str \| None` | Motivo da invalidez, sem o valor |

### `Stats` (`metrics.py:37`)

| Campo | Tipo |
|-------|------|
| `records_read`, `valid`, `with_text` | `int` |
| `invalid`, `duplicates`, `near_duplicates` | `list[int]` |
| `pii` | `list[PiiHit]` |


## Módulo `installer`

### `.sintetica/install-manifest.json`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `sintetica_version` | `string` | Versão do pacote npm (= versão do wheel) |
| `installed_at` | `string` | ISO 8601 UTC sem milissegundos; muda só quando a lista muda |
| `files` | `list<{path, sha256}>` | Caminhos relativos com `/`, ordenados; sem o próprio manifest |

### `.sintetica/state.json`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `version` | `string` | Versão instalada |
| `harnesses` | `list<string>` | `claude-code`, `antigravity`, `cursor`, `gemini-cli`, `codex` |
| `runtime_ready` | `boolean` | `uv` e Python ≥ 3.10 encontrados |

### `.sintetica/policy.json` (padrão em `installer/templates/policy.json`)

| Chave | Valor padrão | Lida por |
|-------|--------------|----------|
| `telemetry` | `false` | Nenhum código (declaração de política) |
| `pii_premask` | `true` | `providers.policy` |
| `cost_ceiling_usd` | `5.00` | `providers.policy` |
| `provider_priority` | `["harness", "ollama", "external"]` | `providers.policy` |
| `pii_custom_patterns` | `[]` | `pii.policy` |

### Arquivos instalados no projeto do usuário

| Caminho | Modo |
|---------|------|
| `.agents/skills/sintetica-<etapa>/SKILL.md`, `.claude/skills/sintetica-<etapa>/SKILL.md` | 644 |
| `.sintetica/bin/sintetica` | 755 |
| `.sintetica/bin/sintetica.cmd` | 644 |
| `.sintetica/runtime/sintetica-<versão>-py3-none-any.whl` | 644 |

### Opções do instalador (`InstallOptions`)

| Campo | Tipo | Uso |
|-------|------|-----|
| `dir` | `string` | Pasta do projeto |
| `yes` | `boolean` | Responde sim (exceto política) |
| `out` | `(line) => void` | Saída |
| `ask`, `interactive`, `fs`, `spawn`, `env`, `nodeVersion`, `home`, `platform`, `packageDir`, `now` | — | Injeção para testes |

### Variável de ambiente

| Variável | Definida por | Lida por |
|----------|--------------|----------|
| `SINTETICA_CMD` | Lançador | `sintetica.command.cli_command()` (padrão `uv run sintetica`) |
