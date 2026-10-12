# Spec Impact Matrix: sintetica

> Gerado pelo Arquiteto do Reversa em 2026-10-12. 🟢 extraído das importações do código.
> Leitura: a linha **muda** → a coluna **é impactada**. `●` dependência direta (importação); `○` dependência por contrato de arquivo; `—` sem relação.

| Muda ↓ / Impacta → | pii | providers | schema | intent | sample | batch | quality | installer | cli |
|--------------------|-----|-----------|--------|--------|--------|-------|---------|-----------|-----|
| **pii** | — | ● (`MaskingProvider`) | — | ● (`apply_answers`) | ● (`_masker`) | ● (`_masker`) | ● (`leaks`, `coverage`) | — | — |
| **providers** | — | — | — | — | ● (`build_provider`) | ● (`build_provider`, `RequestStore`) | — | ○ (política padrão) | ● (`request`, `submit`) |
| **schema** | — | — | — | — | ● (`Record`, `formats`) | ● (`Record`, `formats`, `csv_columns`) | ● (`read_spec`, `Record`) | — | ● |
| **intent** | — | — | ○ (`intent.json` lido por `schema/intent.py`) | — | ● (`IntentModel`) | ● (`IntentModel`, volume) | ● (`started_at`, volume) | — | ● |
| **sample** | — | — | — | — | — | ● (sementes, `review`, `CommandResult`) | ● (`first_error`, `CommandResult`) | ○ (skill) | ● |
| **batch** | — | — | — | — | — | — | ● (`state`, `lock`) | ○ (skill) | ● |
| **quality** | — | — | — | — | — | ● (`evaluate_after_lot`, `load_report`) | — | ○ (skill) | ● |
| **installer** | — | — | — | — | — | — | — | — | ○ (lançador, `SINTETICA_CMD`) |
| **command** (`cli_command`) | — | ● | ● | ● | ● | ● | ● | ○ (lançador define) | ● |
| **fsutil** (`write_atomic`) | — | — | — | ● | ● | ● | ● | — | — |

## Contratos de arquivo entre componentes

| Arquivo | Produtor | Consumidores |
|---------|----------|--------------|
| `intent.json` | `intent` | `schema`, `sample`, `batch`, `quality` |
| `schema.json`, `schema.py`, `record.schema.json`, `schema.state.json` | `schema` | `sample`, `batch`, `quality` |
| `seeds/sample.jsonl`, `seeds/sample.meta.json` | `sample` | `batch` |
| `requests/<id>.json`, `<id>.response.jsonl` | `providers` (harness), agente (`submit`) | `sample`, `batch` |
| `output/run.json`, `output/dataset.<ext>`, `output/run.lock` | `batch` | `quality` |
| `report.json` | `quality` | `batch` (`status`) |
| `.pii_allowlist` | `pii` (via `intent`, `sample`, `batch`, `providers`) | `pii` (via `quality`) |
| `.sintetica/policy.json` | `installer` (padrão), usuário | `providers`, `pii` |
| Skills `SKILL.md` | `installer` | Agente (cita comandos da `cli`) |

## Pontos de maior impacto

1. 🟢 **`pii`**: 6 consumidores; mudança no formato do hash ou na normalização invalida allowlists existentes.
2. 🟢 **`schema`** (`schema_version`, `formats`): amarra amostra, lote e avaliação; mudança no JSON canônico muda todas as versões.
3. 🟢 **`command`**: 40 mensagens; o lançador depende do nome `SINTETICA_CMD`.
4. 🟢 **CLI (nomes de comandos)**: as skills citam os comandos; `tests/test_skills_commands.py` protege essa ligação.
