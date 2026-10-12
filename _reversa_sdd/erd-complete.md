# ERD: sintetica

> Gerado pelo Arquiteto do Reversa em 2026-10-12. 🟢 extraído do código.
> Não há banco de dados. As "entidades" são arquivos por dataset e por projeto; as chaves são o `slug`, a versão do contrato (`schema_version`) e o id do pedido. Campos completos em `data-dictionary.md`.

```mermaid
erDiagram
    PROJECT ||--o{ DATASET : "datasets/<slug>/"
    PROJECT ||--|| POLICY : ".sintetica/policy.json"
    PROJECT ||--o| PRICING : ".sintetica/pricing.json"
    PROJECT ||--o| INSTALL_STATE : ".sintetica/state.json"
    PROJECT ||--o| INSTALL_MANIFEST : ".sintetica/install-manifest.json"

    DATASET ||--|| INTENT : "intent.json"
    DATASET ||--o| SCHEMA_SPEC : "schema.json (versão)"
    DATASET ||--o| SCHEMA_STATE : "schema.state.json"
    DATASET ||--o| ALLOWLIST : ".pii_allowlist"
    DATASET ||--o{ HARNESS_REQUEST : "requests/<id>.json"
    DATASET ||--o| SAMPLE_STATE : "sample.state.json"
    DATASET ||--o| SEED : "seeds/sample.jsonl + meta"
    DATASET ||--o| RUN_STATE : "output/run.json"
    DATASET ||--o| REPORT : "report.json + report.md"

    SCHEMA_SPEC ||--|| SCHEMA_STATE : "schema_version"
    SCHEMA_SPEC ||--o{ SAMPLE_STATE : "schema_version"
    SCHEMA_SPEC ||--o{ SEED : "schema_version (meta)"
    SCHEMA_SPEC ||--o{ RUN_STATE : "schema_version"
    SCHEMA_SPEC ||--o{ REPORT : "schema_version"
    HARNESS_REQUEST ||--o| HARNESS_RESPONSE : "<id>.response.jsonl (apagada após leitura)"
    SAMPLE_STATE ||--o| HARNESS_REQUEST : "pending_request_id"
    RUN_STATE ||--o| HARNESS_REQUEST : "pending_request_id"
    RUN_STATE ||--|| PARTIAL_RECORDS : "records.partial.jsonl"
    RUN_STATE ||--o| FINAL_DATASET : "dataset.<ext>"
    REPORT }o--|| FINAL_DATASET : "avalia"
    REPORT }o--o| RUN_STATE : "run_status, volume"
    INTENT ||--o{ REPORT : "started_at → duração"

    INTENT {
        string slug PK
        string mode
        string started_at
        object objective
        object structure
        object rules
        string format
        int volume
        string confirmed_at
    }
    SCHEMA_SPEC {
        string schema_version PK "SHA-256"
        string format
        string kind
        list fields
    }
    SCHEMA_STATE {
        string schema_version FK
        string status
        int rounds
        string approved_at
    }
    SAMPLE_STATE {
        string status
        int n
        string schema_version FK
        int round
        int attempt
        list accepted
        string pending_request_id FK
    }
    SEED {
        string schema_version FK
        int n_records
        bool partial
    }
    HARNESS_REQUEST {
        string id PK "12 hex"
        int n_records
        string instructions
        object schema_json
        list seeds
    }
    RUN_STATE {
        string slug FK
        string status
        int volume_requested
        int accepted
        decimal cost_usd
        decimal authorized_usd
        string schema_version FK
        string pending_request_id FK
    }
    REPORT {
        string verdict
        decimal conformity_pct
        decimal structural_uniqueness_pct
        decimal semantic_uniqueness_pct
        int pii_leaks
        string schema_version FK
        string finished_at
    }
    POLICY {
        bool pii_premask
        decimal cost_ceiling_usd
        list provider_priority
        list pii_custom_patterns
    }
    INSTALL_MANIFEST {
        string sintetica_version
        list files "path + sha256"
    }
```

## Cardinalidades e regras

| Relação | Regra | Confiança |
|---------|-------|-----------|
| Dataset → intenção | 1:1, criada no `start` | 🟢 |
| Contrato → amostra, semente, lote, relatório | A versão amarra tudo; versão nova invalida amostra e bloqueia lote antigo | 🟢 |
| Lote → pedido do harness | 0..1 pendente por vez; 1 pedido por rodada | 🟢 |
| Pedido → resposta | 0..1; a resposta é apagada depois de lida | 🟢 |
| Dataset → lote | 0..1 em andamento (trava) | 🟢 |
| Projeto → allowlist | 1 por dataset, só cresce | 🟢 |
