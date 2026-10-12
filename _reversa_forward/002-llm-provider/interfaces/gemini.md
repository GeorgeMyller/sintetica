# Interface: Gemini generateContent

> Tipo: HTTP. Backend `gemini` do `ExternalAPIProvider`. Confidência: 🟡. Conferir contra a documentação vigente no início do coding.

## Requisição

- `POST https://generativelanguage.googleapis.com/v1beta/models/<modelo>:generateContent`
- Cabeçalhos: `x-goog-api-key: $GEMINI_API_KEY`, `Content-Type: application/json`
- 🟡 A chave vai no cabeçalho, nunca na URL, para não aparecer em log de URL (RN-07).
- Corpo:

```json
{
  "systemInstruction": { "parts": [ { "text": "<instruções comuns de formato>" } ] },
  "contents": [ { "role": "user", "parts": [ { "text": "<prompt já mascarado>" } ] } ],
  "generationConfig": { "responseMimeType": "application/json" }
}
```

## Resposta usada

| Campo | Uso |
|-------|-----|
| `candidates[0].content.parts[*].text` | Texto JSON `{"records": [...]}` |
| `usageMetadata.promptTokenCount` | `input_tokens` |
| `usageMetadata.candidatesTokenCount` | `output_tokens` |

## Erros e comportamento

| Situação | Comportamento |
|----------|---------------|
| 429, 5xx, timeout de 60 s, JSON inválido, sem `candidates` | Retry (3 tentativas, esperas 1 s e 2 s) |
| 401, 403 | `CredentialError` citando `GEMINI_API_KEY`, sem retry |
| 400 com chave inválida | 🟡 Tratar como `CredentialError` quando a mensagem indicar chave inválida |
| 404 de modelo | `ProviderError` citando `SINTETICA_GEMINI_MODEL`, sem retry |
| Outros 4xx | `ProviderError`, sem retry |
