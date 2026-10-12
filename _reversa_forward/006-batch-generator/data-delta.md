# Data Delta: batch-generator

> Identificador: `006-batch-generator`
> Data: `2026-10-12`
> Base: `_reversa_sdd/sdd/batch-generator.md#9. Modelo de Dados`. Não há modelo extraído de legado (greenfield).

## 1. `datasets/<slug>/output/run.json`

```
RunState {
  slug: string
  status: "iniciando" | "em_andamento" | "aguardando_agente"
        | "concluido" | "incompleto" | "interrompido_custo" | "falha_provedor"
  mode: "foreground" | "background"
  pid: int | null                  // só em background
  volume_requested: int
  format: "csv" | "json" | "jsonl"
  accepted: int                    // espelho do arquivo parcial (fonte da verdade, D-13)
  discarded_invalid: int
  discarded_duplicate: int
  round: int                       // 1 a 4 (1ª rodada + 3 extras)
  block_size: int                  // bloco adaptativo ou --block-size (D-05)
  avg_tokens: int                  // média da amostra
  estimate_usd: decimal | null     // estimativa antes do 1º pedido
  authorized_usd: decimal | null   // valor autorizado; null = teto da política
  cost_usd: decimal                // custo acumulado real
  provider: string
  provider_reason: string
  schema_version: string
  pending_request_id: string | null   // só com o harness
  pending_command: string | null      // comando submit para o agente
  stop_cause: string | null           // motivo do status final, sem valores de registro
  started_at: string               // ISO 8601 UTC
  updated_at: string
  finished_at: string | null
}
```

🟡 Diferenças em relação à spec:
- status `iniciando` (janela do processo filho no Windows, D-16) e `aguardando_agente` (harness, D-04) são novos;
- `discarded` virou `discarded_invalid` e `discarded_duplicate`, como já estava na spec;
- `mode`, `format`, `round`, `block_size`, `avg_tokens`, `estimate_usd`, `provider_reason`, `pending_*`, `stop_cause` e `updated_at` são novos.
- Valores monetários gravados como texto decimal exato (`"0.42"`), como no restante do projeto.

## 2. Outros arquivos em `datasets/<slug>/output/`

| Caminho | Conteúdo | Ciclo de vida |
|---------|----------|---------------|
| `records.partial.jsonl` | Registros aceitos e mascarados, 1 por linha (`to_jsonl_line`), anexados por bloco com `fsync` | Fica após o fim, para retomada e auditoria |
| `dataset.<ext>` | Arquivo final: lista JSON, JSONL ou CSV com cabeçalho na ordem do contrato (RFC 4180) | Gerado no fim, em qualquer status final |
| `run.lock` | Trava por dataset (D-16); conteúdo vazio | Criado no 1º lote; a trava some com o processo |
| `worker.log` | Linhas de progresso e erros do processo em background, sem valores de registro | Só em background |

## 3. Arquivos de outras features usados

| Caminho | Uso |
|---------|-----|
| `datasets/<slug>/intent.json` (004) | Volume, formato, modo e textos das instruções |
| `datasets/<slug>/schema.json`, `schema.py`, `record.schema.json`, `schema.state.json` (003) | Pré-condição, validação e JSON Schema do pedido |
| `datasets/<slug>/seeds/sample.jsonl` e `sample.meta.json` (005) | Sementes, tamanho médio e versão do contrato da amostra |
| `datasets/<slug>/requests/<id>.json` e `<id>.response.jsonl` (002) | Pedido e resposta do harness; a resposta é apagada depois de lida |
| `datasets/<slug>/.pii_allowlist` (001) | Hashes dos valores falsos inseridos no lote |
| `.sintetica/policy.json` e `.sintetica/pricing.json` (002) | Prioridade dos provedores, teto e preços |

## 4. Migrações necessárias

Nenhuma. Arquivos novos.
