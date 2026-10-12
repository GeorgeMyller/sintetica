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
