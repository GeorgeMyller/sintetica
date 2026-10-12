# Fluxograma: módulo `providers`

> 🟢 Extraído de `src/sintetica/providers/factory.py`, `selection.py`, `decorators/*.py` e `harness/*.py`.

## `build_provider` e `select_provider`

```mermaid
flowchart TD
    A[build_provider n_records] --> B[load_provider_policy .sintetica/policy.json]
    B --> C[percorre provider_priority]
    C --> D{harness?}
    D -- disponível e n ≤ 100 --> H[HarnessAgentProvider]
    D -- não --> E{ollama?}
    E -- GET /api/tags 200 em 2 s --> O[ExternalAPIProvider ollama]
    E -- não --> F{external?}
    F -- chave no ambiente --> X[ExternalAPIProvider openai, anthropic ou gemini]
    F -- não --> C
    C -- fim da lista --> U[ProviderUnavailable]
    O --> R[RetryingProvider 3 chamadas]
    X --> R
    R --> M{pii_premask?}
    M -- sim --> MP[MaskingProvider]
    M -- não --> CC
    MP --> CC[ConcurrencyLimitedProvider 8]
    H --> CC
    CC --> BB[BudgetedProvider teto = authorized_usd ou cost_ceiling_usd]
```

## Pedido externo com teto e retry

```mermaid
sequenceDiagram
    participant C as Chamador
    participant B as Budgeted
    participant S as Concurrency
    participant M as Masking
    participant R as Retrying
    participant E as External
    C->>B: generate(pedido)
    B->>B: gasto + reservado + previsão > autorizado?
    alt acima do teto
        B-->>C: resultado vazio, stop_reason "teto de custo"
    else dentro do teto
        B->>S: generate
        S->>M: generate (semáforo)
        M->>M: mascara instruções, sementes e textos do schema
        M->>R: generate(pedido mascarado)
        loop até 3 chamadas
            R->>E: POST na API
            E-->>R: 429/5xx/timeout/malformada → espera 1 s, 2 s
        end
        E-->>B: registros, tokens, custo real
        B->>B: soma o custo real
        B-->>C: GenerationResult
    end
```

## Protocolo do harness

```mermaid
flowchart TD
    A[HarnessAgentProvider.generate] --> B{n ≤ 100?}
    B -- não --> L[HarnessLimitExceeded]
    B -- sim --> C[id = 12 hex do SHA-256 do pedido canônico]
    C --> D[grava requests/id.json se não existe]
    D --> E{requests/id.response.jsonl existe?}
    E -- não --> P[HarnessResponsePending id + comando submit]
    E -- sim --> G[devolve registros, tokens estimados, custo 0]
    P -.agente gera e roda sintetica submit.-> S[RequestStore.submit]
    S --> V{UTF-8, ≤ 10 MiB, 1 objeto por linha,<br/>1 a n linhas?}
    V -- não --> X[código 5, nada gravado]
    V -- sim --> W[grava id.response.jsonl de forma atômica]
```
