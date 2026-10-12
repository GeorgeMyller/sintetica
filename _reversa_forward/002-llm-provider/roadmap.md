# Roadmap: llm-provider (porta de geração por LLM, custo e mascaramento)

> Identificador: `002-llm-provider`
> Data: `2026-10-09`
> Requirements: `_reversa_forward/002-llm-provider/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA
> Cenário: greenfield. Não há `architecture.md`, `c4-context.md`, `state-machines.md`, `dependencies.md` nem `code-analysis.md`. O delta é sobre o desenho planejado em `_reversa_sdd/sdd/llm-provider.md` e sobre o código entregue na feature 001, registrado em `_reversa_sdd/addenda/001-pii-guard.md`.

## 1. Resumo da abordagem

🟡 A feature cria o pacote `sintetica.providers` e o primeiro ponto de entrada de linha de comando, `sintetica` (subcomandos `request` e `submit`).
🟡 O pacote segue as 3 camadas da feature 001: domínio (tipos imutáveis e cálculo de custo), portas (protocolo `LLMProvider`) e adaptadores (`ExternalAPIProvider` com 4 backends HTTP e `HarnessAgentProvider` por arquivo).
🟡 As regras transversais ficam em decoradores que envolvem qualquer `LLMProvider`: `MaskingProvider` (RN-03, RN-04), `RetryingProvider` (RF-09, RF-10), `ConcurrencyLimitedProvider` (RF-11) e `BudgetedProvider` (RF-08). Cada regra tem 1 teste isolado, e os adaptadores ficam simples.
🟡 Uma fábrica, `build_provider(...)`, aplica a RN-01: lê a política, escolhe o provedor, monta a pilha de decoradores e devolve o provedor pronto, com o motivo da escolha.
🟡 Os 4 backends usam 1 cliente HTTP assíncrono (`httpx`), sem SDK oficial de cada fornecedor. A suíte de testes troca o transporte por servidores simulados (`httpx.MockTransport`), sem rede.
🟡 O provedor do harness não bloqueia à espera do agente. `generate` devolve o resultado se a resposta já foi enviada por `submit`; senão, grava o pedido e levanta `HarnessResponsePending` com o comando que o agente deve executar.
🟡 Modelos padrão e preços vêm de um arquivo de dados embutido no pacote. Variáveis `SINTETICA_*_MODEL` e `.sintetica/pricing.json` sobrescrevem esses valores (RN-08, Q31).

## 2. Princípios aplicados

🟡 `.reversa/principles.md` continua ausente. A recomendação da feature 001 (rodar `/reversa-principles`) não foi executada.

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| n/a | Arquivo de princípios ausente | n/a |

🟡 Restrições do PRD tratadas como princípios de fato:
- Sem chamadas não autorizadas e sem telemetria (Q15): a suíte roda sem rede; o pacote não envia nada além do pedido de geração. **Respeita.**
- Privacidade por design (Q21): mascaramento antes de qualquer backend externo, inclusive Ollama (Q30). **Respeita.**
- Tipagem estrita e cobertura ≥ 80% (Q19): **respeita**, com a ressalva de tipagem da R-04.
- Teto de orçamento (Q17): autorização acima de US$ 5,00 e parada no valor autorizado. **Respeita.**

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Pacote `src/sintetica/providers/` com domínio, portas, decoradores, adaptadores e fábrica | Mesmo padrão em camadas da feature 001 | Módulo único `providers.py` | 🟡 |
| D-02 | Tipos de domínio como `@dataclass(frozen=True, slots=True)`; valores monetários em `decimal.Decimal` | Consistência com a feature 001; `float` gera erro de arredondamento no teste de US$ 5,00 vs. US$ 5,01 | Pydantic no domínio; `float` | 🟡 |
| D-03 | Cliente HTTP único `httpx.AsyncClient`, 1 adaptador fino por backend (montar corpo, ler texto e tokens) | 1 dependência nova em vez de 4 SDKs; retry e timeout centralizados; transporte simulável sem rede | SDKs oficiais `openai`, `anthropic`, `google-genai`, `ollama` | 🟡 |
| D-04 | Regras transversais como decoradores do `LLMProvider`, nesta ordem de fora para dentro: `BudgetedProvider` → `ConcurrencyLimitedProvider` → `MaskingProvider` → `RetryingProvider` → adaptador | O teto conta o pedido antes de ocupar vaga; o mascaramento acontece 1 vez, fora do retry | Lógica dentro de cada adaptador | 🟡 |
| D-05 | `MaskingProvider` envolve os 4 backends externos (inclusive Ollama) e nunca o harness | Q30: mascarar sempre; o harness não é externo | Mascarar Ollama só com host remoto | 🟢 |
| D-06 | Mascaramento do pedido inteiro: `instructions`, cada valor de texto em `seeds` (recursivo) e os textos de `schema_json` (`description`, `examples`, `default`, `enum`), via `PiiGuard.mask` | RF-05; os hashes dos substitutos vão para a allowlist e não viram vazamento no `quality-evaluator` | Mascarar só `instructions` | 🟡 |
| D-07 | `PolicyError` ou allowlist indisponível no `PiiGuard` com `pii_premask` ativo: o pedido é recusado com `MaskingUnavailable`, sem envio | RN-03; falha segura do adendo 001 | Enviar sem mascarar com aviso | 🟢 |
| D-08 | Seleção (RN-01) por função pura `select_provider(priority, n_records, availability)`; a disponibilidade é sondada à parte | Teste da RF-03 sem rede; motivo da escolha em texto | Seleção dentro da fábrica, com efeitos | 🟡 |
| D-09 | Disponibilidade: `harness` quando o chamador declara contexto de harness (`harness_available=True`, ligado pela flag `--harness` das skills) e `n_records ≤ 100`; `ollama` quando `GET {OLLAMA_HOST}/api/tags` responde em 2 s; `external` quando existe ao menos 1 chave | O runtime Python não sabe sozinho se roda dentro de um agente | Variável de ambiente implícita do harness | 🟡 |
| D-10 | Backend externo: `SINTETICA_EXTERNAL_BACKEND` quando definido; senão o primeiro com chave, na ordem `openai`, `anthropic`, `gemini` | Cenário da RF-03 (só `OPENAI_API_KEY` → `openai`); ordem previsível | Escolha pelo menor preço (NG-01 da spec) | 🟡 |
| D-11 | Protocolo do harness em 2 passos por arquivo (RN-02): `request` grava `datasets/<slug>/requests/<id>.json`; `submit` lê JSONL da entrada padrão e grava `<id>.response.jsonl` | Q29 | Só entrada padrão; tirar o harness da porta | 🟢 |
| D-12 | `<id>` do pedido = 12 primeiros caracteres hex do SHA-256 do pedido canônico (JSON com chaves ordenadas) | `request` repetido com o mesmo conteúdo reaproveita o mesmo pedido (idempotência) | UUID aleatório | 🟡 |
| D-13 | `HarnessAgentProvider.generate` não bloqueia: com resposta presente devolve o resultado; sem resposta grava o pedido e levanta `HarnessResponsePending(request_id, command)` | O agente executa comandos em sequência; um `request` bloqueante impediria o `submit` | Espera com polling no arquivo | 🟡 |
| D-14 | `submit` aceita de 1 a `n_records` linhas, cada uma um objeto JSON; fora disso, erro sem gravar resposta | RF-04; resposta parcial não fica escondida | Exigir exatamente `n_records` | 🟡 |
| D-15 | Tokens do harness estimados por `ceil(caracteres / 4)`, com custo US$ 0 | RF-13 exige tokens; a amostra do harness alimenta o `avg_tokens` da estimativa do lote externo | Tokens zerados | 🟡 |
| D-16 | Preço por modelo com 2 valores: `input_usd_per_token` e `output_usd_per_token`. Estimativa = `n_records × avg_tokens × output_usd_per_token`. Custo real = entrada × preço de entrada + saída × preço de saída | As APIs cobram entrada e saída com preços diferentes; usar o preço de saída na estimativa superestima (falha segura para o teto) e mantém o exemplo da RF-06 | Preço único misturado | 🟡 |
| D-17 | Modelos padrão e preços em `src/sintetica/providers/data/defaults.json`, lido por `importlib.resources`; sobrescrita entrada a entrada por `.sintetica/pricing.json` e modelo por `SINTETICA_*_MODEL` | Q31; atualizar a cada versão exige editar só 1 arquivo de dados | Constantes em Python | 🟢 |
| D-18 | `BudgetedProvider` reserva o custo previsto do próximo pedido antes de enviá-lo, sob `asyncio.Lock`; previsão = média do custo real já observado, ou a estimativa por pedido antes do 1º resultado. Se acumulado + previsão > autorizado, o pedido não sai e o lote para com motivo `teto de custo` | RF-08: com US$ 1,00 e US$ 0,40 por pedido, o 3º pedido (US$ 1,20) não sai; a reserva evita estouro com 8 pedidos simultâneos | Conferir só o acumulado depois do envio | 🟡 |
| D-19 | Retry com 3 tentativas no total e esperas de 1 s e 2 s (a espera de 4 s da RF-09 não ocorre com 3 tentativas). Função `sleep` injetável nos testes | Cenários do requirements: 503, 503, 200 → 3 chamadas; 429 sempre → 3 chamadas | 3 retries + 1 tentativa (4 chamadas) | 🟡 |
| D-20 | 401 e 403 levantam `CredentialError` com o nome da variável e sem o valor; nenhuma exceção ou `repr` carrega a chave | RF-10, RN-07 | Mensagem genérica | 🟡 |
| D-21 | Resposta pedida como JSON `{"records": [...]}` usando o modo JSON de cada backend; parse comum; JSON inválido ou sem `records` conta como falha temporária | RF-09, EC-06 | Parse de texto livre | 🟡 |
| D-22 | Ponto de entrada `sintetica = "sintetica.cli:main"` em `[project.scripts]`, com `argparse` e subcomandos `request` e `submit` | Q29 cita `uv run sintetica`; sem dependência extra de CLI | `click`; `typer` | 🟡 |
| D-23 | Leitura de política em `sintetica.providers.policy`: `pii_premask` (padrão `true`), `cost_ceiling_usd` (padrão `5.00`), `provider_priority` (padrão `["harness","ollama","external"]`). Arquivo ausente usa os padrões; arquivo inválido levanta `PolicyError` | Valores padrão de `cli-installer` RF-06; o instalador ainda não existe | Esperar o `cli-installer` | 🟡 |
| D-24 | Autorização de custo fora do provedor: `estimate_cost` devolve `CostEstimate.requires_authorization`; o chamador pergunta e cria `BudgetedProvider(authorized_usd=...)` | O provedor não faz E/S com o usuário; `batch-generator` RF-02 é quem pergunta | Pergunta dentro do provedor | 🟡 |

> D-05, D-07, D-11 e D-17 recebem 🟢 porque vêm de decisão confirmada pelo revisor (Q29, Q30, Q31) ou de código entregue (adendo 001).

## 4. Premissas

🟡 Nenhuma premissa vinda de `[DÚVIDA]`: o `requirements.md` está com 0 marcadores após o clarify de 2026-10-09.

| Premissa | Origem (`requirements.md` seção) | Risco se errada |
|----------|----------------------------------|-----------------|
| Os identificadores de modelo indicados na Q31 serão confirmados ou trocados antes do coding (Q32) | 4. RN-08; 10. Lacunas | Modelo descontinuado gera 404 no 1º uso real; só afeta `defaults.json` |
| Os 5 harnesses permitem que o agente execute `uv run sintetica submit` com entrada padrão | `sample-preview.md#14` (OQ-02) | Em harness sem execução de comando, o provedor do harness fica indisponível e a seleção pula para o próximo |
| As skills chamam o runtime com `--harness` quando rodam dentro de um agente | D-09 | Sem a flag, o harness nunca é escolhido; custo sobe para o usuário. Mitigação: as skills da feature `sample-preview` passam a flag |
| Os formatos de requisição e resposta das 4 APIs descritos em `interfaces/` estão vigentes | 7. Delta de contratos | Diferença quebra 1 backend; o teste de contrato com servidor simulado não detecta. Mitigação: teste de fumaça manual no `onboarding.md` |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `sintetica.providers` | `_reversa_sdd/sdd/llm-provider.md` | componente-novo | Porta, 2 adaptadores, 4 decoradores, seleção, custo e política |
| Contrato Python `LLMProvider` | `_reversa_sdd/sdd/llm-provider.md#6` (RF-01) | contrato-novo | API interna usada por `sample-preview` e `batch-generator` |
| CLI `sintetica request` / `submit` | `_reversa_sdd/sdd/sample-preview.md#8`, `questions.md#Q29` | contrato-novo | Primeiro ponto de entrada de linha de comando do pacote |
| `sintetica.pii.PiiGuard` | `_reversa_sdd/addenda/001-pii-guard.md` | sem mudança | Consumido pelo `MaskingProvider` só pela fachada |
| `pyproject.toml` | `_reversa_sdd/addenda/001-pii-guard.md` | regra-alterada | Nova dependência `httpx`; nova seção `[project.scripts]` |

Estrutura de arquivos prevista:

```
src/sintetica/cli.py                          # main(): subcomandos request e submit
src/sintetica/providers/__init__.py           # exporta LLMProvider, GenerationRequest, GenerationResult, CostEstimate, build_provider, erros
src/sintetica/providers/domain.py             # GenerationRequest, GenerationResult, CostEstimate, ProviderChoice, ModelPrice
src/sintetica/providers/errors.py             # ProviderError, CredentialError, ProviderUnavailable, HarnessLimitExceeded,
                                              # HarnessResponsePending, MaskingUnavailable, BudgetExceeded, MalformedResponse
src/sintetica/providers/ports.py              # Protocol LLMProvider
src/sintetica/providers/policy.py             # ProviderPolicy + load_provider_policy(.sintetica/policy.json)
src/sintetica/providers/pricing.py            # PriceTable: defaults.json + .sintetica/pricing.json; estimate(), real_cost()
src/sintetica/providers/models.py             # resolve_model(backend): SINTETICA_*_MODEL ou padrão
src/sintetica/providers/data/defaults.json    # modelos padrão e preços embutidos
src/sintetica/providers/selection.py          # select_provider() pura + probe_availability()
src/sintetica/providers/prompt.py             # monta o prompt comum e faz o parse de {"records": [...]}
src/sintetica/providers/decorators/masking.py
src/sintetica/providers/decorators/retrying.py
src/sintetica/providers/decorators/concurrency.py
src/sintetica/providers/decorators/budget.py
src/sintetica/providers/external/provider.py  # ExternalAPIProvider (httpx.AsyncClient, timeout 60 s)
src/sintetica/providers/external/backends.py  # OpenAIBackend, AnthropicBackend, GeminiBackend, OllamaBackend
src/sintetica/providers/harness/store.py      # RequestStore: datasets/<slug>/requests/
src/sintetica/providers/harness/provider.py   # HarnessAgentProvider
src/sintetica/providers/factory.py            # build_provider()
tests/providers/test_*.py
tests/providers/contract.py                   # suíte de contrato comum aos 2 adaptadores
tests/cli/test_request_submit.py
```

## 6. Delta no modelo de dados

- Resumo das mudanças: 🟡 5 tipos de domínio em memória, 1 arquivo de dados embutido (`defaults.json`), 1 arquivo opcional do projeto (`.sintetica/pricing.json`), 2 arquivos por pedido do harness em `datasets/<slug>/requests/` e leitura de 3 chaves de `.sintetica/policy.json`. Nenhuma migração.
- Detalhe completo em: `_reversa_forward/002-llm-provider/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| OpenAI Chat Completions | HTTP | `_reversa_forward/002-llm-provider/interfaces/openai.md` |
| Anthropic Messages | HTTP | `_reversa_forward/002-llm-provider/interfaces/anthropic.md` |
| Gemini generateContent | HTTP | `_reversa_forward/002-llm-provider/interfaces/gemini.md` |
| Ollama `/api/chat` e `/api/tags` | HTTP | `_reversa_forward/002-llm-provider/interfaces/ollama.md` |
| `sintetica request` / `submit` | arquivo + CLI | `_reversa_forward/002-llm-provider/interfaces/harness-cli.md` |

🟡 Contrato interno da porta, usado por `sample-preview` e `batch-generator`:

```
class LLMProvider(Protocol):
    @property
    def name(self) -> str                      # "harness", "openai", "anthropic", "gemini", "ollama"
    @property
    def is_local(self) -> bool                 # True para harness e ollama
    async def generate(self, request: GenerationRequest) -> GenerationResult
    def estimate_cost(self, n_records: int, avg_tokens: int) -> CostEstimate

def build_provider(
    n_records: int,
    *,
    dataset_dir: Path,
    project_dir: Path,
    harness_available: bool = False,
    authorized_usd: Decimal | None = None,     # None: o BudgetedProvider usa o teto da política
    concurrency: int = 8,
    transport: httpx.AsyncBaseTransport | None = None,   # injeção para testes
) -> tuple[LLMProvider, ProviderChoice]       # ProviderChoice traz nome, backend e motivo (RF-03)
```

## 8. Plano de migração

n/a. Não há dados nem provedores anteriores. A única mudança em arquivo existente é aditiva em `pyproject.toml` (dependência `httpx` e `[project.scripts]`).

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| R-01: Identificadores de modelo da Q31 desatualizados (ex.: `claude-3-5-haiku-latest` descontinuado) | médio | alto | Q32 antes do coding; valores só em `defaults.json`; erro 404 vira `ProviderError` com o nome da variável `SINTETICA_*_MODEL` para troca imediata |
| R-02: Formato de API muda e o servidor simulado não percebe | médio | médio | Contratos isolados em `backends.py`; teste de fumaça manual por backend no `onboarding.md`; marcador `@pytest.mark.live` fora da suíte padrão |
| R-03: Estimativa pelo preço de saída superestima mais de 25% (meta G-04) | baixo | médio | A meta é de 3 meses (Should); o `run.json` do `batch-generator` compara estimado e real; ajuste de fórmula em feature futura |
| R-04: `httpx` e `mypy --strict` | baixo | baixo | `httpx` é tipado; sem override de `ignore_missing_imports` |
| R-05: Chave de API vazar por `repr` de exceção ou de cabeçalho em log | alto | baixo | Chave lida só no momento da requisição; exceções carregam o nome da variável; teste que varre mensagens e `repr` atrás do valor simulado |
| R-06: Mascaramento troca um valor que o usuário pediu de propósito nas instruções | médio | médio | Comportamento esperado (Q21); o substituto é do mesmo tipo e formato; documentado no `onboarding.md` |
| R-07: Corrida no teto com 8 pedidos simultâneos | médio | médio | Reserva sob `asyncio.Lock` (D-18); teste com 8 pedidos concorrentes e teto baixo |
| R-08: Pedido do harness fica órfão (agente não executa `submit`) | baixo | médio | O pedido é idempotente (D-12); `request` repetido mostra o mesmo id; nada fica bloqueado (D-13) |
| R-09: Sonda do Ollama atrasa a seleção | baixo | médio | Timeout de 2 s e sonda só quando `ollama` vem antes do provedor escolhido na prioridade |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Re-extração reversa executada e sem regressão vermelha (recomendado, não obrigatório)
- [ ] `uv run mypy` e `uv run ruff check` sem erros
- [ ] `uv run pytest --cov=sintetica` com cobertura ≥ 80% em `sintetica.providers` e `sintetica.cli`
- [ ] Suíte padrão roda sem rede (nenhum teste fora de `@pytest.mark.live` abre conexão)
- [ ] Os 20 cenários Gherkin do `requirements.md` cobertos por testes
- [ ] Os 2 adaptadores passam na mesma suíte de contrato (RF-01)
- [ ] Suíte da feature 001 continua verde (92 testes)
- [ ] Q32 respondida e `defaults.json` com identificadores confirmados

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-09 | Versão inicial gerada por `/reversa-plan` | reversa |
