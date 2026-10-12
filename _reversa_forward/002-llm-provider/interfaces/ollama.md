# Interface: Ollama `/api/chat` e `/api/tags`

> Tipo: HTTP. Backend `ollama` do `ExternalAPIProvider`. Confidência: 🟡. Conferir contra a documentação vigente no início do coding.

## Sonda de disponibilidade

- `GET {OLLAMA_HOST}/api/tags`, timeout de 2 s.
- Resposta 200: disponível. Qualquer outro resultado: indisponível, com o endereço citado no motivo da seleção.

## Requisição de geração

- `POST {OLLAMA_HOST}/api/chat` (padrão `http://localhost:11434`)
- Sem autenticação.
- Corpo:

```json
{
  "model": "<SINTETICA_OLLAMA_MODEL ou llama3.2>",
  "stream": false,
  "format": "json",
  "messages": [
    { "role": "system", "content": "<instruções comuns de formato>" },
    { "role": "user", "content": "<prompt já mascarado>" }
  ]
}
```

🟢 O prompt passa pelo `MaskingProvider` mesmo com host local (Q30).

## Resposta usada

| Campo | Uso |
|-------|-----|
| `message.content` | Texto JSON `{"records": [...]}` |
| `prompt_eval_count` | `input_tokens` (0 quando ausente) |
| `eval_count` | `output_tokens` (0 quando ausente) |

🟡 Custo sempre US$ 0 (RN-05).

## Erros e comportamento

| Situação | Comportamento |
|----------|---------------|
| 5xx, timeout de 60 s, JSON inválido, conexão recusada | Retry (3 tentativas, esperas 1 s e 2 s) |
| 404 com modelo ausente | `ProviderError` com a dica `ollama pull <modelo>`, sem retry |
| Outros 4xx | `ProviderError`, sem retry |
