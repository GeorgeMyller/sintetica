# Data Delta: quality-evaluator

> Identificador: `007-quality-evaluator`
> Data: `2026-10-12`
> Base: `_reversa_sdd/sdd/quality-evaluator.md#9. Modelo de Dados`. Não há modelo extraído de legado (greenfield).

## 1. `datasets/<slug>/report.json`

```
Report {
  slug: string
  verdict: "APROVADO" | "REPROVADO"
  failed_metrics: list<"conformidade" | "unicidade_estrutural" | "unicidade_semantica" | "pii">
  volume_requested: int
  records_read: int
  valid_records: int
  conformity_pct: decimal                 // 1 casa
  structural_uniqueness_pct: decimal      // 1 casa
  semantic_uniqueness_pct: decimal | null // null = não aplicável
  semantic_applicable: boolean
  pii_leaks: int
  pii_findings: list<{index: int, field: string, type: string, preview: string}>
  pii_coverage: { types: list<string>, custom_patterns: int, limits: list<string> }
  duration_min: decimal | null            // null = não medida
  time_target_met: boolean | null         // só para volume ≤ 100
  run_status: string | null               // status de run.json, null sem run.json
  schema_version: string                  // contrato usado na avaliação
  warnings: list<string>                  // status do lote, contrato divergente, volume, allowlist
  problem_indices: { invalid: list<int>, duplicates: list<int>, near_duplicates: list<int>, pii: list<int> }
  finished_at: string                     // ISO 8601 UTC
}
```

🟡 Diferenças em relação à spec:
- `problem_indices.near_duplicates` separa os quase-duplicados dos duplicados exatos;
- `pii_findings`, `semantic_applicable`, `volume_requested`, `records_read`, `valid_records`, `schema_version` e `warnings` são novos;
- índices começam em 0 (posição do registro no dataset).
- Valores decimais gravados como número exato (`96.0`), como no restante do projeto.

## 2. `datasets/<slug>/report.md`

Gerado do mesmo `Report`: veredito, tabela das métricas com meta e resultado, duração, avisos, registros com problema (até 20 índices por tipo, com o total) e a seção "Escopo e limites da detecção de PII".

## 3. Arquivos de outras features usados (só leitura)

| Caminho | Uso |
|---------|-----|
| `datasets/<slug>/intent.json` (004) | `started_at` e volume (sem `run.json`) |
| `datasets/<slug>/schema.json`, `schema.py`, `schema.state.json` (003) | Contrato atual, texto livre e validação |
| `datasets/<slug>/output/dataset.<ext>` e `output/run.json` (006) | Registros, status, volume e versão do contrato do lote |
| `datasets/<slug>/output/run.lock` (006) | Lote em andamento |
| `datasets/<slug>/.pii_allowlist` (001) | Valores falsos que não contam como vazamento |
| `.sintetica/policy.json` (001) | Padrões extras de PII |

## 4. Migrações necessárias

Nenhuma. Arquivos novos.
