# Data Delta: sample-preview

> Identificador: `005-sample-preview`
> Data: `2026-10-12`
> Base: `_reversa_sdd/sdd/sample-preview.md#9. Modelo de Dados`. Não há modelo extraído de legado (greenfield).

## 1. `datasets/<slug>/sample.state.json`

```
SampleState {
  status: "aguardando_agente" | "em_revisao" | "aprovada" | "interrompida"
  n: int                          // 3 a 5 (Q41: padrão 3)
  schema_version: string          // versão do contrato no início da rodada
  round: int                      // 0 na 1ª amostra; +1 a cada ajuste
  attempt: int                    // tentativas usadas na rodada, 0 a 3
  adjustment: string | null       // pedido de ajuste já mascarado
  pending_request_id: string | null
  accepted: list<object>          // registros válidos e mascarados (forma de to_json_obj, decimais como texto exato)
  rejected: list<{reason: string}> // motivo do descarte; nunca o valor do registro
  provider: string | null
  provider_reason: string | null
  updated_at: string              // ISO 8601 UTC
}
```

## 2. Arquivos gravados na aprovação

| Caminho | Conteúdo |
|---------|----------|
| `datasets/<slug>/seeds/sample.jsonl` | 1 registro por linha, via `to_jsonl_line` (Q42) |
| `datasets/<slug>/seeds/sample.meta.json` | Metadados abaixo |

```
SampleMeta {
  schema_version: string
  approved_at: string            // ISO 8601 UTC
  provider: string               // ex.: "harness"
  n_requested: int
  n_records: int
  partial: boolean               // n_records < n_requested (Q43)
  rounds: int                    // rodadas de ajuste até a aprovação
}
```

🟡 Diferenças em relação à spec: o `SampleFile` único virou 2 arquivos (Q42); `n_requested`, `n_records`, `partial` e `rounds` são novos.

## 3. Arquivos de outras features usados

| Caminho | Uso |
|---------|-----|
| `datasets/<slug>/intent.json` (004) | Modo e textos para as instruções |
| `datasets/<slug>/schema.json`, `schema.py`, `record.schema.json`, `schema.state.json` (003) | Pré-condição, validação e JSON Schema do pedido |
| `datasets/<slug>/requests/<id>.json` e `<id>.response.jsonl` (002) | Pedido e resposta do harness |
| `datasets/<slug>/.pii_allowlist` (001) | Hashes dos valores falsos inseridos na amostra |

## 4. Migrações necessárias

Nenhuma. Arquivos novos.
