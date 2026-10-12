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
