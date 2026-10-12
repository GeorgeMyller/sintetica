# Investigation: sample-preview

> Identificador: `005-sample-preview`
> Data: `2026-10-12`
> Fonte: `_reversa_forward/005-sample-preview/roadmap.md`

## 1. Pesquisa de fundo (código entregue)

### 1.1 `HarnessAgentProvider` (feature 002)
- 🟢 `generate(request)` calcula o id pelo SHA-256 do pedido canônico (`n_records`, `instructions`, `schema_json`, `seeds`), grava o pedido se não existir e devolve a resposta se `<id>.response.jsonl` existir; senão levanta `HarnessResponsePending(request_id, command)`.
- 🟢 Consequência: 2 pedidos iguais compartilham a mesma resposta. A amostra precisa variar o pedido a cada tentativa (roadmap §1, D-03).
- 🟢 `sintetica submit` já recusa linhas que não são objeto JSON e respostas com mais linhas que `n_records` (código 5). A amostra só vê respostas bem formadas.
- 🟢 O harness devolve custo 0 e tokens estimados; não passa pelo mascaramento (Q30, D-05 da feature 002).

### 1.2 `build_provider` (feature 002)
- 🟢 Escolhe pela `provider_priority` da política; com `harness_available=True` e a política padrão, devolve o harness envolto em `ConcurrencyLimitedProvider` e `BudgetedProvider`.
- 🟢 As exceções do provedor herdam de `ProviderError`: `ProviderUnavailable`, `CredentialError`, `ProviderExhausted`, `MaskingUnavailable`, `HarnessLimitExceeded`, `HarnessResponsePending`.

### 1.3 Contrato (feature 003)
- 🟢 `load_record_model(dataset_dir)` confere a versão e importa o `Record`.
- 🟢 `to_json_obj`, `to_jsonl_line`, `to_csv_row` e `csv_columns` serializam com decimal exato e listas com `|`.
- 🟢 `schema.state.json` guarda `status` e `schema_version`.

### 1.4 Intenção (feature 004)
- 🟢 `load_intent_model` traz o modo e os textos já mascarados de objetivo, estrutura e regras.

### 1.5 Mascaramento (feature 001)
- 🟢 `PiiGuard.mask(texto, field=...)` troca cada achado por valor falso do mesmo formato e grava o hash na allowlist; `PolicyError` e `OSError` sinalizam indisponibilidade.

## 2. Alternativas avaliadas

| Alternativa | Prós | Contras | Veredito |
|-------------|------|---------|----------|
| O agente gera a amostra e chama só um `validate` | Menos passos | Sem o caminho da política de provedores; sem rastreio de pedido | Descartada |
| Chamar o `HarnessAgentProvider` direto | Simples | Ignora `provider_priority` e o teto de custo | Descartada |
| Laço de tentativas dentro de uma chamada, esperando o agente | Uma chamada só | O runtime não chama o agente; bloquearia | Descartada |
| `sample run` reentrante sobre o estado em arquivo | Mesmo padrão da Q29; cada chamada é curta e testável | Agente chama `run` mais de uma vez | **Escolhida** |

## 3. Padrões aplicáveis

- 🟡 **Máquina de estados em arquivo:** `aguardando_agente` → `em_revisao` → `aprovada`, com `interrompida` no Expresso parcial; `adjust` e versão nova reiniciam.
- 🟡 **Validar, mascarar, revalidar** antes de guardar qualquer registro.
- 🟡 **Pedido único por tentativa** para não reaproveitar resposta antiga.

## 4. Fontes externas

- Documentação Python: `asyncio.run`, `json`.
- Contratos internos: `_reversa_forward/002-llm-provider/interfaces/harness-cli.md`, `_reversa_forward/003-schema-builder/interfaces/schema-cli.md`.
