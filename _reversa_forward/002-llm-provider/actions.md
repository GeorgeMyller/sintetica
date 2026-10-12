# Actions: llm-provider (porta de geração por LLM, custo e mascaramento)

> Identificador: `002-llm-provider`
> Data: `2026-10-09`
> Roadmap: `_reversa_forward/002-llm-provider/roadmap.md`
> Fontes auxiliares: `data-delta.md`, `requirements.md` (20 cenários Gherkin), `interfaces/` (5 contratos), `_reversa_sdd/questions.md` (Q32, Q33).

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 36 |
| Paralelizáveis (`[//]`) | 25 |
| Maior cadeia de dependência | 8 (T004 → T015 → T021 → T022 → T023 → T031 → T032 → T034) |
| Ações bloqueadas por pergunta aberta | 1 (T002, Q34) |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Editar `pyproject.toml` de forma aditiva: dependência `httpx`; seção `[project.scripts]` com `sintetica = "sintetica.cli:main"`; marcador `live` no pytest e `addopts = "-m 'not perf and not live'"`. Não remover nada da feature 001 (D-03, D-22, R-02) | - | `[//]` | `pyproject.toml` | 🟡 | `[X]` |
| T002 | Criar `defaults.json` (formato de `data-delta.md#2`) com modelos e preços da Q32 em texto decimal por token: `openai` = `gpt-4o-mini` (0.00000015 / 0.0000006); `gemini` = `gemini-1.5-flash` (0.000000075 / 0.0000003); `ollama` = `llama3.2` (sem preço); `anthropic` = valor da Q34 (D-17) | - | `[//]` | `src/sintetica/providers/data/defaults.json` | 🔴 | `[X]` |
| T003 | Executar `uv sync` para instalar `httpx` e atualizar `uv.lock` | T001 | - | `uv.lock` | 🟡 | `[X]` |
| T004 | Criar a árvore de pacotes vazia: `providers/__init__.py`, `providers/decorators/__init__.py`, `providers/external/__init__.py`, `providers/harness/__init__.py` (D-01) | - | `[//]` | `src/sintetica/providers/` | 🟡 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T005 | Criar fixtures comuns: fábrica de `httpx.MockTransport` por backend com respostas programáveis (status, corpo, atraso) e registro das chamadas; `sleep` falso que registra as esperas; variáveis de ambiente limpas por teste (`monkeypatch`) | T003, T004 | - | `tests/providers/conftest.py` | 🟡 | `[X]` |
| T006 | Escrever a suíte de contrato reutilizável da porta (RF-01): `name`, `is_local`, `generate` devolve `GenerationResult` com registros, tokens de entrada, tokens de saída e custo (RF-13), `estimate_cost` devolve `CostEstimate`. Aplicar aos 2 adaptadores | T005 | - | `tests/providers/contract.py` | 🟡 | `[X]` |
| T007 | Escrever testes de custo e política: US$ 5,00 sem autorização; US$ 5,01 com autorização; modelo sem preço exige autorização; `pricing.json` sobrescreve o embutido (US$ 1,00); `SINTETICA_OPENAI_MODEL` muda o modelo; política ausente usa padrões; política inválida gera erro (RN-05, RN-08, RF-06, RF-07, D-16, D-23) | T005 | `[//]` | `tests/providers/test_cost_policy.py` | 🟡 | `[X]` |
| T008 | Escrever testes de seleção: harness com 50 registros; 1.000 registros com Ollama desligado e `OPENAI_API_KEY` → `external`/`openai`; 101 registros pulam o harness; nenhum provedor → mensagem com as 3 chaves e `OLLAMA_HOST`; motivo da escolha em texto (RN-01, RF-03, RF-12, D-08, D-09, D-10) | T005 | `[//]` | `tests/providers/test_selection.py` | 🟡 | `[X]` |
| T009 | Escrever testes de mascaramento: e-mail das instruções não chega ao servidor simulado em `openai` e em `ollama` local; valores de `seeds` (aninhados) e textos do schema mascarados; política de PII inválida → `MaskingUnavailable` com 0 chamadas; harness não mascara (RN-03, RN-04, RF-05, D-05, D-06, D-07) | T005 | `[//]` | `tests/providers/test_masking.py` | 🟢 | `[X]` |
| T010 | Escrever testes de retry e credencial: 503, 503, 200 → 3 chamadas e esperas 1 s e 2 s; 429 sempre → 3 chamadas e motivo "falha do provedor"; texto não JSON e depois válido → 2 chamadas; 401 → 1 chamada e mensagem com `OPENAI_API_KEY` sem o valor; valor da chave ausente de mensagens e `repr` (RF-09, RF-10, RN-07, D-19, D-20, R-05) | T005 | `[//]` | `tests/providers/test_retry.py` | 🟢 | `[X]` |
| T011 | Escrever testes de concorrência e teto: 100 pedidos nunca passam de 8 simultâneos; teto US$ 1,00 com US$ 0,40 por pedido → 3º pedido não sai e `stop_reason = "teto de custo"` com registros dos 2 primeiros; 8 pedidos simultâneos com teto baixo não estouram o autorizado (RF-08, RF-11, D-18, R-07) | T005 | `[//]` | `tests/providers/test_budget_concurrency.py` | 🟡 | `[X]` |
| T012 | Escrever testes dos 4 backends contra `interfaces/`: URL, cabeçalhos e corpo enviados; leitura de texto e tokens; chave do Gemini no cabeçalho e nunca na URL; `stop_reason = "max_tokens"` da Anthropic conta como malformada; 404 de modelo cita `SINTETICA_<BACKEND>_MODEL`; 404 do Ollama sugere `ollama pull` | T005 | `[//]` | `tests/providers/test_backends.py` | 🟡 | `[X]` |
| T013 | Escrever testes do `HarnessAgentProvider`: 101 registros → `HarnessLimitExceeded` sem gravar; sem resposta → grava pedido e levanta `HarnessResponsePending` com o comando; com resposta → resultado com custo US$ 0 e tokens `ceil(caracteres / 4)`; mesmo conteúdo → mesmo id (RN-02, RF-04, RF-14, D-12, D-13, D-15) | T005 | `[//]` | `tests/providers/test_harness.py` | 🟢 | `[X]` |
| T014 | Escrever testes da CLI `request`/`submit` contra `interfaces/harness-cli.md`: fluxo completo com 10 registros; id inexistente (saída 4); linha inválida, 0 linhas e linhas demais (saída 5); slug inexistente (saída 2); limite de 101 (saída 3); entrada > 10 MB; nada gravado nos casos de erro | T005 | `[//]` | `tests/cli/test_request_submit.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T015 | Implementar o domínio de `data-delta.md#1`: `GenerationRequest`, `GenerationResult`, `CostEstimate`, `ProviderChoice`, `ModelPrice` como `@dataclass(frozen=True, slots=True)`, com `Decimal` e validação `n_records ≥ 1` (D-02) | T004 | `[//]` | `src/sintetica/providers/domain.py` | 🟡 | `[X]` |
| T016 | Implementar a hierarquia de erros: `ProviderError` (base), `CredentialError(env_var)`, `ProviderUnavailable(checked)`, `HarnessLimitExceeded`, `HarnessResponsePending(request_id, command)`, `MaskingUnavailable`, `BudgetExceeded`, `MalformedResponse`, `ProviderPolicyError`. Nenhuma guarda valor de chave (D-20) | T004 | `[//]` | `src/sintetica/providers/errors.py` | 🟡 | `[X]` |
| T017 | Definir o protocolo `LLMProvider` (`name`, `is_local`, `generate`, `estimate_cost`) com `typing.Protocol` | T015 | - | `src/sintetica/providers/ports.py` | 🟡 | `[X]` |
| T018 | Implementar `ProviderPolicy` e `load_provider_policy(path)`: 3 chaves com padrões de `cli-installer` RF-06; arquivo ausente → padrões; JSON inválido ou tipo errado → `ProviderPolicyError` (D-23) | T016 | `[//]` | `src/sintetica/providers/policy.py` | 🟡 | `[X]` |
| T019 | Implementar `PriceTable`: carga de `defaults.json` por `importlib.resources`, sobrescrita por `.sintetica/pricing.json`, `estimate(model, n, avg_tokens)` pelo preço de saída, `real_cost(model, in, out)`, `price_known`; preços lidos como texto para `Decimal` (RN-05, D-16, D-17) | T002, T015 | `[//]` | `src/sintetica/providers/pricing.py` | 🟢 | `[X]` |
| T020 | Implementar `resolve_model(backend)`: `SINTETICA_<BACKEND>_MODEL` ou o padrão de `defaults.json` (RN-08) | T002 | `[//]` | `src/sintetica/providers/models.py` | 🟢 | `[X]` |
| T021 | Implementar o prompt comum (instruções de formato `{"records": [...]}`, schema, sementes, quantidade) e o parse da resposta: JSON inválido, sem `records` ou com item que não é objeto → `MalformedResponse` (D-21) | T015, T016 | - | `src/sintetica/providers/prompt.py` | 🟡 | `[X]` |
| T022 | Implementar `OpenAIBackend`, `AnthropicBackend`, `GeminiBackend` e `OllamaBackend`: montar requisição, ler texto e tokens, mapear 401/403 → `CredentialError`, 404 → `ProviderError` com dica, 429/5xx → erro temporário, conforme `interfaces/` | T021, T020 | - | `src/sintetica/providers/external/backends.py` | 🟡 | `[X]` |
| T023 | Implementar `ExternalAPIProvider`: `httpx.AsyncClient` com timeout de 60 s e transporte injetável; chave lida no momento da requisição; `is_local` verdadeiro só para `ollama`; custo real via `PriceTable` (US$ 0 no Ollama) (D-03, RN-07) | T022, T019, T017 | - | `src/sintetica/providers/external/provider.py` | 🟡 | `[X]` |
| T024 | Implementar `RequestStore`: id = 12 hex do SHA-256 do pedido canônico; gravação atômica de `<id>.json` sem sobrescrever; validação e gravação atômica de `<id>.response.jsonl`; leitura da resposta (RF-14, D-11, D-12, D-14) | T015, T016 | `[//]` | `src/sintetica/providers/harness/store.py` | 🟢 | `[X]` |
| T025 | Implementar `HarnessAgentProvider` sobre o `RequestStore`: limite de 100, resultado quando há resposta, `HarnessResponsePending` quando não há, tokens estimados e custo US$ 0 (RN-02, RF-04, D-13, D-15) | T024, T017 | - | `src/sintetica/providers/harness/provider.py` | 🟢 | `[X]` |
| T026 | Implementar `RetryingProvider`: 3 tentativas, esperas 1 s e 2 s, `sleep` injetável; repete erro temporário, timeout e `MalformedResponse`; não repete `CredentialError` nem `ProviderError` definitivo; ao esgotar, motivo "falha do provedor" (RF-09, RF-10, D-19) | T017, T016 | `[//]` | `src/sintetica/providers/decorators/retrying.py` | 🟢 | `[X]` |
| T027 | Implementar `ConcurrencyLimitedProvider` com `asyncio.Semaphore` (padrão 8, ajustável) (RF-11) | T017 | `[//]` | `src/sintetica/providers/decorators/concurrency.py` | 🟡 | `[X]` |
| T028 | Implementar `MaskingProvider` com `PiiGuard.for_dataset`: mascarar `instructions`, valores de texto de `seeds` (recursivo) e textos do schema (`description`, `examples`, `default`, `enum`); `PolicyError` ou allowlist indisponível → `MaskingUnavailable` sem envio (RN-03, RN-04, RF-05, D-06, D-07) | T017, T016 | `[//]` | `src/sintetica/providers/decorators/masking.py` | 🟢 | `[X]` |
| T029 | Implementar `BudgetedProvider`: reserva sob `asyncio.Lock` com previsão pela média do custo real (ou estimativa antes do 1º resultado); acumulado + previsão > autorizado → não envia e devolve `stop_reason = "teto de custo"` (RF-08, D-18) | T017, T016 | `[//]` | `src/sintetica/providers/decorators/budget.py` | 🟡 | `[X]` |
| T030 | Implementar `select_provider(priority, n_records, availability)` pura, com motivo em texto, e `probe_availability(...)`: flag de harness e `n_records ≤ 100`; `GET {OLLAMA_HOST}/api/tags` em 2 s só quando necessário; chaves presentes e `SINTETICA_EXTERNAL_BACKEND` (RN-01, RF-03, RF-12, D-08, D-09, D-10, R-09) | T015, T018 | `[//]` | `src/sintetica/providers/selection.py` | 🟡 | `[X]` |
| T031 | Implementar `build_provider(...)`: carregar política, selecionar, montar a pilha `Budgeted → ConcurrencyLimited → Masking → Retrying → adaptador` (sem `Masking` no harness; `Masking` só com `pii_premask` ativo) e devolver `(provider, ProviderChoice)` (D-04, D-05, D-24) | T023, T025, T026, T027, T028, T029, T030 | - | `src/sintetica/providers/factory.py` | 🟡 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T032 | Expor a API pública em `sintetica.providers` com `__all__`: `LLMProvider`, `GenerationRequest`, `GenerationResult`, `CostEstimate`, `ProviderChoice`, `build_provider` e os erros | T031 | - | `src/sintetica/providers/__init__.py` | 🟡 | `[X]` |
| T033 | Implementar `sintetica.cli:main` com `argparse` e os subcomandos `request` e `submit`, códigos de saída e mensagens de `interfaces/harness-cli.md` (D-22) | T024 | `[//]` | `src/sintetica/cli.py` | 🟢 | `[X]` |
| T034 | Completar os testes até: cobertura ≥ 80% em `sintetica.providers` e `sintetica.cli`; 20 cenários Gherkin cobertos; suíte de contrato aplicada aos 2 adaptadores; suíte padrão sem rede; os 92 testes da feature 001 verdes (critério de pronto) | T032, T033, T006, T007, T008, T009, T010, T011, T012, T013, T014 | - | `tests/providers/`, `tests/cli/` | 🟡 | `[X]` |
| T035 | Escrever testes de fumaça `@pytest.mark.live`, 1 por backend, com 3 registros; pulados quando a chave ou o Ollama não existem (R-02, `onboarding.md#4`) | T032 | `[//]` | `tests/providers/test_live.py` | 🟡 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T036 | Escrever a documentação curta do módulo, no padrão de `docs/pii-guard.md`: variáveis de ambiente, `pricing.json`, protocolo do harness, ordem dos decoradores, mascaramento de valores pedidos de propósito (R-06) e tabela de problemas comuns | T032, T033 | `[//]` | `docs/llm-provider.md` | 🟡 | `[X]` |

## Rastreabilidade dos cenários Gherkin

| Cenário (`requirements.md#7`) | Ação de teste |
|-------------------------------|---------------|
| Lote de teste usa o harness sem custo | T008 |
| Lote grande pula harness e Ollama indisponível | T008 |
| Harness recusa pedido acima do limite | T013, T014 |
| Protocolo do harness em 2 passos | T013, T014 |
| Submit com pedido inexistente | T014 |
| Ollama também recebe conteúdo mascarado | T009 |
| Preço do projeto sobrescreve o preço embutido | T007 |
| Nenhum provedor disponível | T008 |
| PII mascarada antes do envio externo | T009 |
| Mascaramento indisponível bloqueia o envio | T009 |
| Estimativa exata no teto não pede autorização | T007 |
| Estimativa acima do teto exige autorização | T007 |
| Modelo sem preço conhecido | T007 |
| Teto atingido no meio do lote | T011 |
| Retry em erro temporário | T010 |
| Esgotar tentativas | T010 |
| Chave inválida não repete | T010 |
| Resposta malformada conta como falha temporária | T010 |
| Concorrência limitada | T011 |
| Resultado traz tokens e custo | T006, T012 |

## Notas de execução

- 🟢 Execução de 2026-10-09: 36 de 36 ações concluídas. Q34 respondida: `anthropic` = `claude-haiku-5-5` (US$ 0,80 / US$ 4,00 por milhão de tokens, valores do revisor).
- 🟡 Desvios de forma, sem mudança de comportamento:
  - Suíte de contrato em `tests/providers/test_contract.py` (o nome `contract.py` não seria coletado pelo pytest). Apoio comum em `tests/providers/support.py`.
  - `BudgetExceeded` não foi criado: o teto devolve `GenerationResult` vazio com `stop_reason = "teto de custo"`, como em `data-delta.md#1`. Foram criados `TransientProviderError`, `ProviderExhausted` e `RequestStoreError`.
  - Chave ausente gera `CredentialError` ("ausente ou recusada") antes de qualquer chamada.
  - `build_provider` ganhou 3 parâmetros opcionais: `per_request_estimate`, `probe_transport` e `sleep` (injeção para testes e para o `batch-generator`).
- 🟡 Teste live: o backend `ollama` passou contra o servidor real com `SINTETICA_OLLAMA_MODEL=llama3.2:3b`. O padrão `llama3.2` não está baixado nesta máquina; o erro 404 com a dica `ollama pull llama3.2` foi confirmado. OpenAI, Anthropic e Gemini foram pulados por falta de chave.
- (histórico) 🔴 T002 dependia da Q34 (modelo da Anthropic). As outras 35 ações não dependem dela. O `/reversa-coding` pode executar T002 com os 3 valores confirmados e deixar a entrada `anthropic` para o fim, sem bloquear T019 e T020: os testes usam preços e modelos simulados.
- 🟢 Q33 confirmou D-13, D-16 e D-19. As ações T013, T019, T025 e T026 herdam 🟢.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-09 | Versão inicial gerada por `/reversa-to-do` | reversa |
