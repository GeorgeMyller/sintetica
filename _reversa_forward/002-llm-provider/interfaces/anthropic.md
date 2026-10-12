# Interface: Anthropic Messages

> Tipo: HTTP. Backend `anthropic` do `ExternalAPIProvider`. Confidência: 🟡. Conferir contra a documentação vigente no início do coding.

## Requisição

- `POST https://api.anthropic.com/v1/messages`
- Cabeçalhos: `x-api-key: $ANTHROPIC_API_KEY`, `anthropic-version: 2023-06-01`, `content-type: application/json`
- Corpo:

```json
{
  "model": "<SINTETICA_ANTHROPIC_MODEL ou padrão>",
  "max_tokens": 8192,
  "system": "<instruções comuns de formato>",
  "messages": [ { "role": "user", "content": "<prompt já mascarado>" } ]
}
```

🟡 A saída JSON é pedida pelas instruções de sistema. O parse comum trata texto fora do objeto JSON como resposta malformada (retry).

## Resposta usada

| Campo | Uso |
|-------|-----|
| `content[*].text` (blocos `type: "text"`, concatenados) | Texto JSON `{"records": [...]}` |
| `usage.input_tokens` | `input_tokens` |
| `usage.output_tokens` | `output_tokens` |
| `stop_reason == "max_tokens"` | Resposta truncada: conta como malformada (retry) |

## Erros e comportamento

| Situação | Comportamento |
|----------|---------------|
| 429, 5xx (inclui 529 sobrecarga), timeout de 60 s, JSON inválido | Retry (3 tentativas, esperas 1 s e 2 s) |
| 401, 403 | `CredentialError` citando `ANTHROPIC_API_KEY`, sem retry |
| 404 de modelo | `ProviderError` citando `SINTETICA_ANTHROPIC_MODEL`, sem retry |
| Outros 4xx | `ProviderError`, sem retry |

## Idempotência

🟡 Mesma observação do backend OpenAI: retry após timeout pode gerar cobrança dupla.
