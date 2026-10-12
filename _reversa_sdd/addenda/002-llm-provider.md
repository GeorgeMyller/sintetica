# Adendo: llm-provider (porta de geração por LLM, custo e mascaramento)

> Identificador: `002-llm-provider`
> Data: `2026-10-09`
> Cenário: greenfield

## Vigência

Vigente desde 2026-10-09.
Superado pela re-extração de 2026-10-12.

## Resumo da entrega

O pacote `sintetica.providers` é a porta única pela qual o sintetica pede registros a um LLM. Ele oferece 2 adaptadores: o `ExternalAPIProvider` (OpenAI, Anthropic, Gemini e Ollama, sobre 1 cliente `httpx`) e o `HarnessAgentProvider` (o agente do harness, pelo protocolo de arquivo `request`/`submit`). A fábrica `build_provider` escolhe o provedor pela política do projeto e monta 4 camadas: teto de custo, concorrência (8 por padrão), mascaramento de PII e retry (3 chamadas). A entrega também criou o comando `sintetica` (`request` e `submit`).

Ações concluídas: 36 de 36 (`progress.jsonl` com 36 registros). Verificação: 205 testes (92 da feature 001 + 113 novos), cobertura de 99% em `sintetica.providers` e `sintetica.cli`, `mypy --strict` e `ruff` sem erros. Auditoria do revisor Antigravity: aprovada.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/prd.md` | 6. Restrições (Técnica) | componente-novo | O projeto Python agora depende de `httpx` e expõe o comando `sintetica`; a suíte padrão exclui os marcadores `perf` e `live`. |
| `_reversa_sdd/prd.md` | 7. Dependências externas | componente-novo | As APIs OpenAI, Anthropic, Gemini e Ollama são chamadas só pelo `ExternalAPIProvider`, com chaves lidas de variáveis de ambiente no momento da requisição. |
| `_reversa_sdd/sdd/llm-provider.md` | 6. Requisitos Funcionais (RF-01 a RF-03) | componente-novo | Implementados como protocolo `LLMProvider`, 4 backends e `select_provider`; o motivo da escolha vem em `ProviderChoice.reason`. Backend externo: `SINTETICA_EXTERNAL_BACKEND` ou o 1º com chave na ordem `openai`, `anthropic`, `gemini`. |
| `_reversa_sdd/sdd/llm-provider.md` | 6. Requisitos Funcionais (RF-04) | componente-novo | Leia o harness como protocolo em 2 passos por arquivo (Q29): `sintetica request` grava `datasets/<slug>/requests/<id>.json`; `sintetica submit` recebe o JSONL; `generate` sem resposta levanta `HarnessResponsePending` com o comando. Limite de 100 registros. |
| `_reversa_sdd/sdd/llm-provider.md` | 6. Requisitos Funcionais (RF-05) | componente-novo | O mascaramento cobre instruções, sementes e textos do schema, e vale também para o Ollama local (Q30). Política de PII inválida ou allowlist sem gravação geram `MaskingUnavailable` sem envio. |
| `_reversa_sdd/sdd/llm-provider.md` | 6. Requisitos Funcionais (RF-06, RF-07) | componente-novo | Leia o preço como 2 valores por modelo (entrada e saída). A estimativa usa o preço de saída (lado seguro do teto, Q33); o custo real usa os 2. Preços embutidos em `defaults.json`, sobrescritos por `.sintetica/pricing.json`. |
| `_reversa_sdd/sdd/llm-provider.md` | 6. Requisitos Funcionais (RF-08) | componente-novo | Leia a interrupção como resultado vazio com `stop_reason = "teto de custo"`, e não como status de lote; a reserva de custo vale também com pedidos simultâneos. |
| `_reversa_sdd/sdd/llm-provider.md` | 6. Requisitos Funcionais (RF-09 a RF-11) | componente-novo | Leia o retry como 3 chamadas no total, com esperas de 1 s e 2 s (Q33); a espera de 4 s não ocorre. 401 e 403 viram `CredentialError` sem retry. |
| `_reversa_sdd/sdd/llm-provider.md` | 9. Modelo de Dados | componente-novo | Leia `GenerationResult` com os campos extras `provider` e `stop_reason`, `CostEstimate` com `model` e `price_known`, e os tipos novos `ProviderChoice` e `ModelPrice`. Valores monetários em `Decimal`. |
| `_reversa_sdd/sdd/llm-provider.md` | 14. Open Questions (OQ-01 a OQ-03) | componente-novo | Resolvidas: OQ-01 e OQ-02 pelas Q31, Q32 e Q34 (padrões `gpt-4o-mini`, `claude-haiku-5-5`, `gemini-1.5-flash`, `llama3.2`, override por `SINTETICA_*_MODEL`); OQ-03 pela Q30 (mascarar o Ollama). |
| `_reversa_sdd/sdd/sample-preview.md` | 14. Open Questions (OQ-02) | componente-novo | Resolvida pela Q29: o agente envia os registros por `uv run sintetica submit <slug> <id>`. A skill deve chamar o runtime com `harness_available=True` e tratar `HarnessResponsePending`. |
| `_reversa_sdd/sdd/batch-generator.md` | 6. Requisitos Funcionais (RF-02, RF-03) | componente-novo | A dependência existe: o gerador chama `estimate_cost`, pede autorização se `requires_authorization` e reconstrói com `build_provider(..., authorized_usd=valor)`; a concorrência já é limitada pelo provedor. |
| `_reversa_sdd/sdd/cli-installer.md` | 6. Requisitos Funcionais (RF-06) | componente-novo | O `llm-provider` já lê `pii_premask`, `cost_ceiling_usd` e `provider_priority` de `.sintetica/policy.json`, com os padrões deste requisito quando o arquivo não existe. |

## Regras sob vigilância

W001, W002, W003, W004, W005, W006, W007, W008, W009, W010. Todos em "Observações", sem peso de regressão (cenário greenfield). Detalhes em `_reversa_forward/002-llm-provider/regression-watch.md`.

## Fontes

- `_reversa_forward/002-llm-provider/legacy-impact.md`
- `_reversa_forward/002-llm-provider/regression-watch.md`
- `_reversa_forward/002-llm-provider/requirements.md`
- `_reversa_forward/002-llm-provider/data-delta.md`
- `_reversa_forward/002-llm-provider/progress.jsonl`
- `_reversa_forward/002-llm-provider/actions.md`
