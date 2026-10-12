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
