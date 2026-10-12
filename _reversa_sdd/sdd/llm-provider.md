# Spec: llm-provider

> Selo 🟢 CONFORME CÓDIGO em todos os itens, salvo marcação. Fonte: `src/sintetica/providers/`, `src/sintetica/cli.py` (`request`, `submit`), testes `tests/providers/` e `tests/cli/`.
> Consolida os adendos `002-llm-provider.md` e a mudança de mensagens da `008-cli-installer.md`. Versão planejada em `sdd/_planejado/llm-provider.md`.

**Versão:** 2.0 (extraída do código)
**Status:** Implementado
**Autor:** reversa-writer
**Data:** 2026-10-12

---

## 1. Resumo

🟢 O `llm-provider` é o pacote `sintetica.providers`: a porta única `LLMProvider` para gerar registros. Há 2 famílias de adaptadores: o agente do harness, pelo protocolo de arquivos `request`/`submit`, e as APIs externas (OpenAI, Anthropic, Gemini e Ollama local) sobre `httpx`. A escolha segue `.sintetica/policy.json`. Uma pilha de decoradores aplica teto de custo, limite de concorrência, mascaramento de PII e novas tentativas.

## 2. Contexto

🟢 A amostra precisa funcionar sem chave de API (o próprio agente gera), e o lote precisa de alta vazão (Q8). O custo de tokens recai sobre o usuário (Q17). Nenhum dado pessoal pode sair para uma API sem mascaramento (Q21, Q30).

## 3. Goals

- 🟢 G-01: Uma interface para os 5 provedores, escolhidos por política.
- 🟢 G-02: Custo acumulado nunca acima do autorizado.
- 🟢 G-03: Pedido mascarado antes de qualquer backend automático.
- 🟢 G-04: Chaves só no ambiente; nunca em disco, log ou mensagem.

## 4. Non-Goals

- 🟢 NG-01: Sem streaming; cada pedido é uma resposta JSON inteira.
- 🟢 NG-02: Sem cache de respostas das APIs (só o harness reaproveita pela identidade do pedido).

## 5. Usuários

🟢 `sample` e `batch` (via `build_provider`); o agente do harness (via `sintetica request`/`submit`).

## 6. Requisitos Funcionais

| ID | Requisito | Critério de aceite | Fonte |
|----|-----------|--------------------|-------|
| RF-01 | 🟢 Porta `LLMProvider` com `name`, `is_local`, `async generate(GenerationRequest) -> GenerationResult` e `estimate_cost(n, avg_tokens) -> CostEstimate` | Todos os adaptadores e decoradores a cumprem | `ports.py` |
| RF-02 | 🟢 `build_provider(n_records, *, dataset_dir, project_dir, harness_available=False, authorized_usd=None, per_request_estimate=None, concurrency=8, …)` devolve `(provedor, ProviderChoice)` | `ProviderChoice(provider, backend, reason, skipped)` | `factory.py:29-73` |
| RF-03 | 🟢 Seleção por `provider_priority` (padrão `harness → ollama → external`): harness exige `harness_available`; para `n_records > 100`, tenta provedor automático e, se indisponível, faz fallback para harness em blocos de até 100 registros; Ollama é sondado (`GET /api/tags`, 2 s) só quando chega a vez; external usa `SINTETICA_EXTERNAL_BACKEND` com chave, ou o 1º com chave em `openai → anthropic → gemini` | Fallback para harness em blocos de até 100 quando offline | `selection.py:39-99` |
| RF-04 | 🟢 Nenhum provedor: `ProviderUnavailable` listando as variáveis verificadas e o `OLLAMA_HOST` | Mensagem cita `OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, OLLAMA_HOST (...)` | `selection.py:34-36`, `63` |
| RF-05 | 🟢 Pilha: harness = `Budgeted(Concurrency(Harness))`; automático = `Budgeted(Concurrency(Masking(Retrying(External))))`, com `Masking` só se `pii_premask` (inclusive Ollama) | Ollama recebe pedido mascarado | `factory.py:52-73` |
| RF-06 | 🟢 Política em `.sintetica/policy.json` (ou `SINTETICA_PROVIDER`): `pii_premask` (bool, padrão `true`), `cost_ceiling_usd` (número ≥ 0, padrão 5.00), `provider_priority` (lista não vazia de valores conhecidos); arquivo ausente = padrões; chaves desconhecidas ignoradas; conteúdo inválido = `ProviderPolicyError` | `{"telemetry": false, …}` é aceito; `SINTETICA_PROVIDER` prioriza provedor | `policy.py` |
| RF-07 | 🟢 Preços: `data/defaults.json` embutido, sobrescrito por modelo em `.sintetica/pricing.json`; valores como `Decimal` exato | Preço inválido = `ProviderPolicyError` | `pricing.py` |
| RF-08 | 🟢 Modelo por backend: `SINTETICA_<BACKEND>_MODEL` ou o padrão (`gpt-4o-mini`, `claude-haiku-5-5`, `gemini-1.5-flash`, `llama3.2`) | — | `models.py`, `data/defaults.json`, Q31, Q32, Q34 |
| RF-09 | 🟢 Estimativa = `n × tokens médios × preço de saída`; `requires_authorization` se acima do teto; preço desconhecido = `usd 0`, `requires_authorization = True`, `price_known = False`; provedor local custa 0 | — | `pricing.py:69-74`, `external/provider.py:107-114`, Q33 |
| RF-10 | 🟢 Custo real = `entrada × preço de entrada + saída × preço de saída`; preço desconhecido registra 0 com aviso | — | `pricing.py:76-80`, `external/provider.py:96-105` |
| RF-11 | 🟢 Teto: antes de cada pedido, reserva a previsão (média real observada, ou `per_request_estimate`, ou 0) sob lock; se `gasto + reservado + previsão > autorizado`, devolve resultado vazio com `stop_reason = "teto de custo"` e passa a recusar; sem estimativa, o 1º pedido sai sozinho | `spent_usd` e `stopped` expostos | `decorators/budget.py` |
| RF-12 | 🟢 Concorrência: semáforo, 8 por padrão | — | `decorators/concurrency.py` |
| RF-13 | 🟢 Retry só de `TransientProviderError` (429, ≥ 500, timeout, conexão, resposta malformada): 3 chamadas, esperas de 1 s e 2 s; depois `ProviderExhausted` | 401 não repete | `decorators/retrying.py` |
| RF-14 | 🟢 Mascaramento do pedido: instruções, cada semente e, no JSON Schema, só `description`, `examples`, `default` e `enum`; o `PiiGuard` nasce no 1º pedido; política ou allowlist com falha = `MaskingUnavailable`, nada enviado | — | `decorators/masking.py` |
| RF-15 | 🟢 Prompt: sistema pede só `{"records": [...]}`; usuário leva quantidade, instruções, JSON Schema (`sort_keys`) e exemplos; resposta precisa ser objeto com lista `records` de objetos | Fora disso = `MalformedResponse` | `prompt.py` |
| RF-16 | 🟢 Classificação HTTP: 429/≥ 500 temporários; 401/403 (ou 400 com "api key") = `CredentialError` com o nome da variável; 404 cita o modelo e `SINTETICA_<BACKEND>_MODEL` (Ollama: `ollama pull`) | — | `external/backends.py:191-212` |
| RF-17 | 🟢 Backends: OpenAI `response_format: json_object`; Anthropic `max_tokens: 8192`, `anthropic-version: 2023-06-01`, truncada por `max_tokens` = malformada; Gemini chave no cabeçalho `x-goog-api-key`, `responseMimeType: application/json`; Ollama `/api/chat`, `format: json`, `stream: false` | Timeout de 60 s por pedido | `external/backends.py`, `external/provider.py:24` |
| RF-18 | 🟢 Harness: id = 12 primeiros hex do SHA-256 do pedido canônico (`n_records`, `instructions`, `schema_json`, `seeds`); grava `requests/<id>.json` se não existe (nunca reescreve); sem resposta, `HarnessResponsePending(id, comando submit)`; com resposta, devolve os registros, tokens estimados (4 caracteres/token) e custo 0 | Pedido igual reaproveita a resposta | `harness/store.py`, `harness/provider.py` |
| RF-19 | 🟢 `sintetica request <slug> --n-records N --instructions T --schema arquivo [--seeds arquivo.jsonl]` grava o pedido e imprime o comando `submit` | N > 100 = código 3 | `cli.py:251-276` |
| RF-20 | 🟢 `sintetica submit <slug> <id>` lê até 10 MiB da entrada padrão, UTF-8, 1 objeto JSON por linha, de 1 a N linhas; qualquer erro não grava nada; avisa ao substituir resposta anterior | Pedido inexistente = 4; resposta inválida = 5 | `cli.py:279-293`, `harness/store.py:86-116` |
| RF-21 | 🟢 Mensagens citam o comando de quem chamou (`cli_command()`: `SINTETICA_CMD` ou `uv run sintetica`) | Pelo lançador: `.sintetica/bin/sintetica submit …` | `harness/provider.py:33-34`, `command.py` |

## 7. Requisitos Não-Funcionais

| ID | Requisito | Evidência |
|----|-----------|-----------|
| RNF-01 | 🟢 Timeout de 60 s por pedido externo; 2 s na sonda do Ollama | `external/provider.py:24`, `selection.py:22` |
| RNF-02 | 🟢 Disponibilidade: retry de 3 chamadas com espera crescente | `decorators/retrying.py` |
| RNF-03 | 🟢 Segurança: chave lida por chamada; exceções do `httpx` relançadas `from None` (sem cabeçalhos) | `external/provider.py:57-80` |
| RNF-04 | 🟢 Testes sem rede (transportes simulados); `-m live` para fumaça real | `tests/providers/test_live.py` |

## 8. Interface

```python
provider, choice = build_provider(50, dataset_dir=ds, project_dir=root, harness_available=True)
estimate = provider.estimate_cost(50, avg_tokens=120)         # CostEstimate
result = await provider.generate(GenerationRequest(schema, seeds, instructions, 10))
```

```
uv run sintetica request <slug> --n-records 10 --instructions '...' --schema record.schema.json [--seeds sample.jsonl]
uv run sintetica submit <slug> <id> < registros.jsonl
```

| Código | Significado |
|--------|-------------|
| 0 | Sucesso |
| 2 | Dataset inexistente, `--n-records < 1`, arquivo ilegível |
| 3 | Mais de 100 registros no pedido |
| 4 | Pedido inexistente |
| 5 | Resposta inválida (UTF-8, tamanho, linha que não é objeto, quantidade) |

## 9. Modelo de Dados

🟢 `GenerationRequest`, `GenerationResult`, `CostEstimate`, `ProviderChoice`, `ModelPrice`, `ProviderPolicy`; pedido `requests/<id>.json` (`version`, `id`, `created_at`, pedido canônico, `response_format`) e resposta `<id>.response.jsonl`. Detalhe em `data-dictionary.md#módulo-providers`.

## 10. Integrações

| Integração | Endpoint | Autenticação |
|------------|----------|--------------|
| 🟢 OpenAI | `https://api.openai.com/v1/chat/completions` | `Authorization: Bearer $OPENAI_API_KEY` |
| 🟢 Anthropic | `https://api.anthropic.com/v1/messages` | `x-api-key: $ANTHROPIC_API_KEY` |
| 🟢 Gemini | `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent` | `x-goog-api-key: $GEMINI_API_KEY` |
| 🟢 Ollama | `{OLLAMA_HOST}/api/chat` (padrão `http://localhost:11434`) | — |
| 🟢 `pii` | `MaskingProvider` | — |

## 11. Edge Cases

| Cenário | Comportamento |
|---------|---------------|
| 🟢 Pedido igual ao anterior no harness | Mesmo id; reaproveita a resposta (por isso os chamadores numeram tentativas e rodadas) |
| 🟢 Resposta truncada da Anthropic | Malformada → retry |
| 🟢 Teto atingido com pedidos simultâneos | A reserva impede que os 8 pedidos passem juntos do teto |
| 🟢 Modelo sem preço | Estimativa exige autorização; custo real 0 com aviso |
| 🟢 Política inválida | `ProviderPolicyError` antes de qualquer pedido |

## 12. Segurança e Privacidade

- 🟢 Nenhum erro guarda o valor de uma chave (`errors.py`).
- 🟢 O pedido ao harness não é mascarado: o agente já vê a conversa; o mascaramento acontece nos consumidores antes de gravar.

## 13. Decisões (consolidadas)

| Decisão | Fonte |
|---------|-------|
| 🟢 Porta única com escolha por política | Q8, ADR 002 |
| 🟢 Protocolo `request`/`submit` por arquivo, até 100 registros | Q29, ADR 003 |
| 🟢 Mascarar também no Ollama | Q30, ADR 004 |
| 🟢 Estimativa pelo preço de saída; retry de 3 chamadas | Q33, ADR 013 |
| 🟢 Modelos padrão econômicos com override | Q31, Q32, Q34 |

## 14. Lacunas

- 🟡 A estimativa ignora os tokens de entrada; o custo real pode passar do estimado (o teto contém).
- 🟡 Identificadores de modelo padrão podem expirar; o override por variável contorna.

## Histórico

| Versão | Data | Mudança |
|--------|------|---------|
| 1.0 | 2026-10-09 | Spec planejada (`_planejado/`) |
| 2.0 | 2026-10-12 | Reescrita conforme o código; adendos 002 e 008 consolidados |
