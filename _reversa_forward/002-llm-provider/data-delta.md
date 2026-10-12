# Data delta: llm-provider

> Identificador: `002-llm-provider`
> Data: `2026-10-09`
> Base: `_reversa_sdd/sdd/llm-provider.md#9. Modelo de Dados`, `_reversa_sdd/sdd/cli-installer.md#9`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Tipos de domínio (memória)

🟡 Todos `@dataclass(frozen=True, slots=True)`. Valores monetários em `Decimal`.

```
GenerationRequest {
  schema_json: Mapping[str, object]   // JSON Schema do Record
  seeds: Sequence[Mapping[str, object]]
  instructions: str
  n_records: int                       // 1 ≤ n_records
}

GenerationResult {
  records: tuple[dict[str, object], ...]   // brutos, não validados
  input_tokens: int
  output_tokens: int
  cost_usd: Decimal
  provider: str                        // NOVO: "harness" | "openai" | "anthropic" | "gemini" | "ollama"
  stop_reason: str | None              // NOVO: None | "teto de custo"
}

CostEstimate {
  provider: str
  model: str | None                    // NOVO: None para harness
  n_records: int
  avg_tokens: int
  usd: Decimal
  requires_authorization: bool
  price_known: bool                    // NOVO: False quando o modelo não tem preço (EC-04)
}

ProviderChoice {                       // NOVO
  provider: str
  backend: str | None
  reason: str                          // ex.: "harness pulado: 101 > 100 registros; ollama indisponível em http://localhost:11434"
}

ModelPrice {                           // NOVO
  input_usd_per_token: Decimal
  output_usd_per_token: Decimal
}
```

| Tipo | Mudança vs. spec | Motivo |
|------|------------------|--------|
| `GenerationResult.provider` | campo novo | Observabilidade (RNF): o `run.json` registra o provedor por resultado |
| `GenerationResult.stop_reason` | campo novo | RF-08: devolver o motivo da parada junto com os registros obtidos |
| `CostEstimate.model`, `price_known` | campos novos | RN-08 e EC-04: mostrar o modelo e explicar por que a autorização foi exigida |
| `ProviderChoice` | tipo novo | RF-03: informar o provedor escolhido e o motivo |
| `ModelPrice` | tipo novo | D-16: preços de entrada e saída separados |
| `GenerationResult.records` | tupla em vez de lista | Imutabilidade do resultado |

## 2. Arquivo embutido no pacote

🟡 `src/sintetica/providers/data/defaults.json`:

```json
{
  "version": 1,
  "models": {
    "openai": "<Q32>",
    "anthropic": "<Q32>",
    "gemini": "<Q32>",
    "ollama": "llama3.2"
  },
  "prices": {
    "<modelo>": { "input_usd_per_token": "0.00000025", "output_usd_per_token": "0.00000125" }
  }
}
```

- 🟡 Preços em texto, convertidos para `Decimal` sem passar por `float`.
- 🟡 Modelos do Ollama não entram em `prices`. O custo do Ollama é sempre US$ 0 (RN-05).
- 🔴 Valores dos modelos externos e preços dependem da Q32.

## 3. Arquivos do projeto do usuário

| Caminho | Situação | Conteúdo | Quem escreve |
|---------|----------|----------|--------------|
| `.sintetica/policy.json` | existente (planejado pelo `cli-installer`) | Leitura de `pii_premask`, `cost_ceiling_usd`, `provider_priority`. Ausente: padrões de `cli-installer` RF-06 | `cli-installer` (futuro); usuário |
| `.sintetica/pricing.json` | **novo, opcional** | Mesmo formato de `prices` do `defaults.json`. Cada entrada substitui a entrada embutida do mesmo modelo | usuário |
| `datasets/<slug>/requests/<id>.json` | **novo** | Pedido do harness (ver `interfaces/harness-cli.md`) | `sintetica request` |
| `datasets/<slug>/requests/<id>.response.jsonl` | **novo** | 1 registro JSON por linha, enviado pelo agente | `sintetica submit` |
| `datasets/<slug>/.pii_allowlist` | existente (feature 001) | Recebe os hashes dos substitutos gerados pelo `MaskingProvider` | `PiiGuard.mask` |

🟡 Variáveis de ambiente lidas (nunca gravadas):
- Chaves: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`.
- Endereço: `OLLAMA_HOST` (padrão `http://localhost:11434`).
- Modelos: `SINTETICA_OPENAI_MODEL`, `SINTETICA_ANTHROPIC_MODEL`, `SINTETICA_GEMINI_MODEL`, `SINTETICA_OLLAMA_MODEL`.
- Backend externo: `SINTETICA_EXTERNAL_BACKEND` (opcional).

## 4. Migrações

🟡 Nenhuma. Não há dados anteriores. `datasets/` já está no `.gitignore`.
