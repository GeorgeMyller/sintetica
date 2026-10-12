# llm-provider

Porta única pela qual o sintetica pede registros a um modelo de linguagem. Ela escolhe o provedor, estima o custo, aplica o teto e mascara PII antes de qualquer envio externo.

## Uso

```python
import asyncio
from pathlib import Path
from sintetica.providers import GenerationRequest, build_provider

provider, choice = build_provider(
    1000,
    dataset_dir=Path("datasets/pedidos"),
    project_dir=Path("."),
    harness_available=False,      # True quando o runtime roda dentro do agente do harness
)
print(choice.reason)              # "harness indisponível: ...; escolhido external/openai com OPENAI_API_KEY"

estimate = provider.estimate_cost(1000, avg_tokens=500)
if estimate.requires_authorization:
    ...                           # pergunte ao usuário e chame build_provider(..., authorized_usd=valor)

request = GenerationRequest(schema_json={...}, seeds=[...], instructions="...", n_records=10)
result = asyncio.run(provider.generate(request))
result.records, result.input_tokens, result.output_tokens, result.cost_usd, result.stop_reason
```

- A autorização é do chamador. O provedor só informa `requires_authorization`.
- `result.stop_reason == "teto de custo"` indica que o pedido não saiu porque passaria do valor autorizado.

## Escolha do provedor

A ordem vem de `provider_priority` em `.sintetica/policy.json` (padrão `["harness", "ollama", "external"]`). Provedores indisponíveis são pulados.

| Provedor | Disponível quando |
|----------|-------------------|
| `harness` | `harness_available=True` e até 100 registros |
| `ollama` | `GET {OLLAMA_HOST}/api/tags` responde em 2 s |
| `external` | Existe ao menos 1 chave: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` ou `GEMINI_API_KEY` |

O backend externo é `SINTETICA_EXTERNAL_BACKEND`, quando definido. Senão, é o primeiro com chave na ordem `openai`, `anthropic`, `gemini`.

## Variáveis de ambiente

| Variável | Uso |
|----------|-----|
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` | Chaves. Nunca aparecem em mensagens, logs ou arquivos |
| `OLLAMA_HOST` | Endereço do Ollama (padrão `http://localhost:11434`) |
| `SINTETICA_OPENAI_MODEL`, `SINTETICA_ANTHROPIC_MODEL`, `SINTETICA_GEMINI_MODEL`, `SINTETICA_OLLAMA_MODEL` | Troca o modelo padrão |
| `SINTETICA_EXTERNAL_BACKEND` | Força `openai`, `anthropic` ou `gemini` |

Modelos padrão: `gpt-4o-mini`, `claude-haiku-5-5`, `gemini-1.5-flash` e `llama3.2`. Eles ficam em `src/sintetica/providers/data/defaults.json` e são atualizados a cada versão.

## Custo e preços

- Estimativa: `registros × tokens médios × preço de saída por token`. Ela tende a superestimar, o que é o lado seguro do teto.
- Custo real: tokens de entrada × preço de entrada + tokens de saída × preço de saída.
- Harness e Ollama custam US$ 0.
- Modelo sem preço conhecido sempre exige autorização.
- Teto padrão: `cost_ceiling_usd: 5.00` em `.sintetica/policy.json`.

Para corrigir ou acrescentar preços, crie `.sintetica/pricing.json`. Cada entrada substitui a entrada embutida do mesmo modelo:

```json
{ "gpt-4o-mini": { "input_usd_per_token": "0.00000015", "output_usd_per_token": "0.0000006" } }
```

## Protocolo do harness

O runtime Python não chama o agente. O agente gera os registros e os entrega por arquivo:

```bash
uv run sintetica request <slug> --n-records 5 --instructions "clientes de uma loja" --schema schema.json
# o agente lê datasets/<slug>/requests/<id>.json e gera os registros
uv run sintetica submit <slug> <id> < registros.jsonl
```

- Até 100 registros por pedido.
- O mesmo conteúdo gera o mesmo `<id>`.
- `submit` aceita de 1 a `n_records` linhas, cada uma um objeto JSON. Em erro, nada é gravado.
- Códigos de saída: 0 sucesso, 2 dataset ou argumento inválido, 3 limite do harness, 4 pedido inexistente, 5 resposta inválida.
- Sem resposta enviada, `generate` levanta `HarnessResponsePending` com o comando `submit`.

## Mascaramento

Com `pii_premask: true` (padrão), as instruções, as sementes e os textos do schema passam pelo `PiiGuard.mask` antes do envio. Isso vale para os 4 backends externos, inclusive o Ollama local. O harness não é mascarado.

- Um dado pessoal escrito nas instruções é trocado por um valor falso do mesmo tipo, mesmo quando o usuário o escreveu de propósito.
- Os hashes dos valores falsos vão para `datasets/<slug>/.pii_allowlist`, para não contarem como vazamento.
- Política de PII inválida ou allowlist sem gravação: `MaskingUnavailable`, e nada é enviado.

## Ordem das camadas

`BudgetedProvider` → `ConcurrencyLimitedProvider` → `MaskingProvider` → `RetryingProvider` → adaptador.

- Teto: reserva o custo previsto antes de cada pedido.
- Concorrência: até 8 pedidos simultâneos por padrão.
- Retry: 3 chamadas no total, esperas de 1 s e 2 s, para 429, 5xx, timeout de 60 s e resposta malformada. 401 e 403 não são repetidos.

## Problemas comuns

| Sintoma | Causa provável | Ação |
|---------|----------------|------|
| `ProviderUnavailable` com a lista de variáveis | Nenhuma chave e Ollama desligado | Defina 1 chave ou inicie o Ollama |
| `CredentialError` citando `OPENAI_API_KEY` | Chave ausente ou inválida | Troque a chave |
| Erro 404 citando `SINTETICA_<BACKEND>_MODEL` | Modelo descontinuado | Defina a variável com um modelo vigente |
| Erro citando `ollama pull` | Modelo não baixado no Ollama | Execute o comando sugerido |
| `MaskingUnavailable` | `pii_custom_patterns` inválido | Corrija `.sintetica/policy.json` |

## Testes

```bash
uv run pytest tests/providers tests/cli   # suíte padrão, sem rede
uv run pytest -m live                     # fumaça com API real: gera custo
```
