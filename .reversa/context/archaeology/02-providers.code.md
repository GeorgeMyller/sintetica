## Módulo `providers` (`src/sintetica/providers/`)

🟢 **Propósito:** porta única de geração por LLM (`LLMProvider`), com 2 famílias de adaptadores: o agente do harness (protocolo de arquivos `request`/`submit`) e as APIs externas (OpenAI, Anthropic, Gemini e Ollama local). A escolha segue a política do projeto; uma pilha de decoradores aplica teto de custo, concorrência, mascaramento de PII e novas tentativas.

### Arquivos

| Arquivo | Papel |
|---------|-------|
| `ports.py` | Protocolo `LLMProvider` (`name`, `is_local`, `generate`, `estimate_cost`) |
| `domain.py` | `GenerationRequest`, `GenerationResult`, `CostEstimate`, `ProviderChoice`, `ModelPrice`; constantes `HARNESS`, `OLLAMA`, `EXTERNAL`, `STOP_BUDGET` |
| `errors.py` | Hierarquia de erros (`ProviderError` e filhas) |
| `policy.py` | `load_provider_policy` de `.sintetica/policy.json` |
| `selection.py` | `select_provider`, `probe_availability`, `probe_ollama`, `external_backend_from_env` |
| `factory.py` | `build_provider`: política → seleção → pilha de decoradores |
| `pricing.py` | `PriceTable` (`defaults.json` + `.sintetica/pricing.json`) |
| `models.py` | `resolve_model` por backend (`SINTETICA_<BACKEND>_MODEL` ou padrão) |
| `prompt.py` | `SYSTEM_PROMPT`, `build_user_prompt`, `parse_records` |
| `external/backends.py` | 4 backends (`build`, `parse`), `check_status`, `ollama_host` |
| `external/provider.py` | `ExternalAPIProvider` sobre `httpx.AsyncClient` |
| `harness/store.py` | `RequestStore`: pedido, `submit` validado, leitura da resposta |
| `harness/provider.py` | `HarnessAgentProvider`, `estimate_tokens` |
| `decorators/budget.py` | `BudgetedProvider`: teto de custo com reserva |
| `decorators/concurrency.py` | `ConcurrencyLimitedProvider`: semáforo, 8 por padrão |
| `decorators/masking.py` | `MaskingProvider`: mascara instruções, sementes e textos do JSON Schema |
| `decorators/retrying.py` | `RetryingProvider`: 3 chamadas, esperas de 1 s e 2 s |
| `data/defaults.json` | Modelo padrão por backend e preços por token |

### Funções e métodos principais

| Função | Assinatura | Retorno | Local |
|--------|-----------|---------|-------|
| `build_provider` | `(n_records, *, dataset_dir, project_dir, harness_available=False, authorized_usd=None, per_request_estimate=None, concurrency=8, transport=None, probe_transport=None, sleep=asyncio.sleep)` | `(LLMProvider, ProviderChoice)` | `factory.py:29` |
| `select_provider` | `(priority, n_records, availability)` | `ProviderChoice` ou `ProviderUnavailable` | `selection.py:39` |
| `load_provider_policy` | `(path)` | `ProviderPolicy` | `policy.py:30` |
| `PriceTable.estimate` | `(model, n_records, avg_tokens)` | `Decimal \| None` | `pricing.py:69` |
| `PriceTable.real_cost` | `(model, input_tokens, output_tokens)` | `Decimal \| None` | `pricing.py:76` |
| `ExternalAPIProvider.generate` | `(request)` | `GenerationResult` | `external/provider.py:66` |
| `HarnessAgentProvider.generate` | `(request)` | `GenerationResult` ou `HarnessResponsePending` | `harness/provider.py:36` |
| `RequestStore.save_request` | `(request)` | id de 12 hex | `harness/store.py:64` |
| `RequestStore.submit` | `(rid, raw: bytes)` | número de registros | `harness/store.py:86` |
| `request_id` | `(request)` | 12 primeiros hex do SHA-256 do pedido canônico | `harness/store.py:36` |
| `parse_records` | `(text)` | `tuple[dict, ...]` ou `MalformedResponse` | `prompt.py:33` |

### Algoritmos e regras

1. 🟢 **Seleção por prioridade** (`selection.py:39-63`): percorre `provider_priority` (padrão `harness → ollama → external`). Harness: exige `harness_available` e `n_records ≤ 100`. Ollama: sonda `GET {OLLAMA_HOST}/api/tags` (timeout 2 s), só quando a prioridade chega a ele. External: usa `SINTETICA_EXTERNAL_BACKEND` se tiver chave, senão o 1º backend com chave na ordem fixa `openai → anthropic → gemini`. O motivo da escolha junta os pulados e o escolhido. Nenhum disponível: `ProviderUnavailable` listando as variáveis verificadas.
2. 🟢 **Pilha de decoradores** (`factory.py:52-73`): harness = `Budgeted(Concurrency(Harness))`; externo = `Budgeted(Concurrency(Masking(Retrying(External))))`, com `Masking` só se `pii_premask` (inclusive Ollama, Q30). O teto padrão é `cost_ceiling_usd` da política; `authorized_usd` o substitui.
3. 🟢 **Teto de custo com reserva** (`decorators/budget.py`): antes de cada pedido, reserva a previsão (média do custo real observado, ou `per_request_estimate`, ou 0) sob `asyncio.Lock`; se `gasto + reservado + previsão > autorizado`, devolve resultado vazio com `stop_reason = "teto de custo"` e marca `stopped`. Sem estimativa, o 1º pedido sai sozinho para medir o custo real.
4. 🟢 **Estimativa e custo real** (`pricing.py:69-80`): estimativa = `n × tokens médios × preço de saída` (superestima, lado seguro); custo real = `entrada × preço de entrada + saída × preço de saída`. Preço desconhecido: estimativa exige autorização (`requires_authorization = True`, `price_known = False`) e custo real registrado como 0 com aviso (`external/provider.py:96-114`). Provedor local custa 0.
5. 🟢 **Retry** (`decorators/retrying.py`): só `TransientProviderError` (429, 5xx, timeout, conexão, resposta malformada); 3 chamadas; esperas de 1 s e 2 s; depois `ProviderExhausted`.
6. 🟢 **Classificação HTTP** (`external/backends.py:191-212`): 429 e ≥ 500 temporários; 401/403 (ou 400 com "api key") viram `CredentialError` com o nome da variável, nunca o valor; 404 cita o modelo e a variável `SINTETICA_<BACKEND>_MODEL` (no Ollama, `ollama pull`).
7. 🟢 **Mascaramento do pedido** (`decorators/masking.py`): mascara instruções, cada semente e, no JSON Schema, só as chaves de texto livre (`description`, `examples`, `default`, `enum`). O `PiiGuard` é criado no 1º pedido: política inválida ou falha da allowlist viram `MaskingUnavailable` e nada é enviado.
8. 🟢 **Protocolo do harness** (`harness/store.py`): o id é o hash do pedido canônico (`n_records`, `instructions`, `schema_json`, `seeds`), então pedido igual tem o mesmo id e reaproveita a resposta. O pedido nunca é reescrito. `submit` aceita até 10 MiB em UTF-8, 1 objeto JSON por linha, de 1 a `n_records` linhas; qualquer erro não grava nada (códigos 4 e 5).
9. 🟢 **Prompt comum** (`prompt.py`): sistema pede só `{"records": [...]}`; usuário leva quantidade, instruções, JSON Schema e exemplos (com `sort_keys`). A resposta precisa ser objeto com lista `records` de objetos.
10. 🟢 **Chaves de API** (`external/provider.py:57-64`, `backends.py`): lidas do ambiente a cada chamada; Gemini recebe a chave no cabeçalho `x-goog-api-key`, nunca na URL; exceções do `httpx` são relançadas `from None` para não carregar os cabeçalhos.
11. 🟢 **Anthropic** (`backends.py:95-125`): `max_tokens = 8192`; resposta com `stop_reason = "max_tokens"` conta como malformada (retry).

### Constantes e configuração

| Constante | Valor | Local |
|-----------|-------|-------|
| `MAX_HARNESS_RECORDS` | 100 | `harness/store.py:19` |
| `MAX_SUBMIT_BYTES` | 10 MiB | `harness/store.py:20` |
| `DEFAULT_CONCURRENCY` | 8 | `decorators/concurrency.py:10` |
| `MAX_ATTEMPTS`, `DELAYS_S` | 3, (1 s, 2 s) | `decorators/retrying.py:12-13` |
| `DEFAULT_CEILING` | US$ 5.00 | `policy.py:18` |
| `DEFAULT_PRIORITY` | `harness, ollama, external` | `policy.py:19` |
| `REQUEST_TIMEOUT_S` | 60 s | `external/provider.py:24` |
| `OLLAMA_PROBE_TIMEOUT_S` | 2 s | `selection.py:22` |
| `DEFAULT_OLLAMA_HOST` | `http://localhost:11434` | `external/backends.py:22` |
| `ANTHROPIC_VERSION`, `ANTHROPIC_MAX_TOKENS` | `2023-06-01`, 8192 | `external/backends.py:23-24` |
| `STOP_BUDGET` | `"teto de custo"` | `domain.py:9` |
| Modelos padrão | `gpt-4o-mini`, `claude-haiku-5-5`, `gemini-1.5-flash`, `llama3.2` | `data/defaults.json` |
| Heurística de tokens | 4 caracteres por token | `harness/provider.py:15-17` |

### Tratamento de erros

🟢 Hierarquia: `ProviderError` → `TransientProviderError` → `MalformedResponse`; `ProviderExhausted`, `CredentialError`, `ProviderUnavailable`, `HarnessLimitExceeded`, `HarnessResponsePending`, `MaskingUnavailable`, `ProviderPolicyError`, `RequestStoreError(exit_code)`. Nenhum erro guarda o valor de uma chave.

### Dependências

🟢 `httpx`; módulo `pii` (só no `MaskingProvider` e no `factory`).
