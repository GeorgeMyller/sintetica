# Interface: OpenAI Chat Completions

> Tipo: HTTP. Backend `openai` do `ExternalAPIProvider`. Confidência: 🟡. Conferir contra a documentação vigente no início do coding.

## Requisição

- `POST https://api.openai.com/v1/chat/completions`
- Cabeçalhos: `Authorization: Bearer $OPENAI_API_KEY`, `Content-Type: application/json`
- Corpo:

```json
{
  "model": "<SINTETICA_OPENAI_MODEL ou padrão>",
  "messages": [
    { "role": "system", "content": "<instruções comuns de formato>" },
    { "role": "user", "content": "<prompt já mascarado>" }
  ],
  "response_format": { "type": "json_object" }
}
```

## Resposta usada

| Campo | Uso |
|-------|-----|
| `choices[0].message.content` | Texto JSON `{"records": [...]}` |
| `usage.prompt_tokens` | `input_tokens` |
| `usage.completion_tokens` | `output_tokens` |

## Erros e comportamento

| Situação | Comportamento |
|----------|---------------|
| 429, 5xx, timeout de 60 s, JSON inválido | Retry (3 tentativas, esperas 1 s e 2 s) |
| 401, 403 | `CredentialError` citando `OPENAI_API_KEY`, sem retry |
| 404 de modelo | `ProviderError` citando `SINTETICA_OPENAI_MODEL`, sem retry |
| Outros 4xx | `ProviderError`, sem retry |

## Idempotência

🟡 A API não é idempotente. Um retry após timeout pode gerar cobrança dupla. O `BudgetedProvider` conta só o custo das respostas recebidas; o risco fica documentado.
