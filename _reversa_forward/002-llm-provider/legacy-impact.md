# Legacy Impact: llm-provider

> Identificador: `002-llm-provider`
> Data: `2026-10-09`
> Feature greenfield, sem legado pré-existente. Âncora: prd.md + specs SDD.
> Política de edição no momento da execução: `allowLegacyEdits: true`, `allowedPaths: []` (projeto inteiro liberado, sem restrição de caminho).

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `pyproject.toml` | Esqueleto Python (adendo `001-pii-guard`) | regra-alterada | MEDIUM | Arquivo da feature 001 alterado de forma aditiva: dependência `httpx`, `[project.scripts]` com `sintetica`, marcador `live` excluído por padrão |
| `uv.lock` | Esqueleto Python | regra-alterada | LOW | `httpx` e dependências transitivas |
| `src/sintetica/providers/data/defaults.json` | `llm-provider` (`_reversa_sdd/sdd/llm-provider.md#14`, OQ-01, OQ-02) | componente-novo | MEDIUM | Modelos padrão e preços (Q32, Q34); valores desatualizados geram 404 ou estimativa errada |
| `src/sintetica/providers/domain.py`, `ports.py`, `errors.py`, `__init__.py` | `llm-provider` (`#9. Modelo de Dados`, RF-01) | componente-novo | HIGH | Contrato `LLMProvider` consumido por `sample-preview` e `batch-generator` |
| `src/sintetica/providers/policy.py` | `llm-provider` + `cli-installer` (`cli-installer.md#6`, RF-06) | componente-novo | MEDIUM | Lê `pii_premask`, `cost_ceiling_usd` e `provider_priority` antes de o instalador existir |
| `src/sintetica/providers/pricing.py`, `models.py` | `llm-provider` (RF-06, RN-08) | componente-novo | HIGH | Estimativa de custo e teto de US$ 5,00 (Q17) |
| `src/sintetica/providers/prompt.py` | `llm-provider` (EC-06) | componente-novo | LOW | Prompt comum e parse de `{"records": [...]}` |
| `src/sintetica/providers/external/backends.py`, `external/provider.py` | `llm-provider` (RF-02, RF-09, RF-10) | componente-novo | HIGH | Primeiras chamadas de rede do pacote; chaves lidas só na requisição |
| `src/sintetica/providers/harness/store.py`, `harness/provider.py` | `llm-provider` (RF-04, RF-14) + `sample-preview` (`sample-preview.md#14`, OQ-02) | componente-novo | MEDIUM | Protocolo `request`/`submit` aprovado na Q29 |
| `src/sintetica/providers/decorators/masking.py` | `llm-provider` (RF-05) + `pii-guard` | componente-novo | HIGH | Garante 0 envios externos sem mascaramento (G-02), inclusive Ollama (Q30) |
| `src/sintetica/providers/decorators/budget.py` | `llm-provider` (RF-08) | componente-novo | HIGH | Teto de custo durante a geração |
| `src/sintetica/providers/decorators/retrying.py`, `decorators/concurrency.py` | `llm-provider` (RF-09, RF-11) | componente-novo | MEDIUM | 3 tentativas; até 8 pedidos simultâneos |
| `src/sintetica/providers/selection.py`, `factory.py` | `llm-provider` (RN-01, RF-03, RF-12) | componente-novo | MEDIUM | Escolha do provedor e ordem dos decoradores |
| `src/sintetica/cli.py` | `llm-provider` + `sample-preview` | componente-novo | MEDIUM | Primeiro ponto de entrada de linha de comando do pacote |
| `tests/providers/*.py`, `tests/cli/*.py` | `llm-provider` | componente-novo | LOW | 113 testes na suíte padrão + 4 testes `live` |
| `docs/llm-provider.md` | `llm-provider` | componente-novo | LOW | Documentação curta do módulo |

## Diff conceitual por componente

**Esqueleto Python.** O projeto passa a depender de `httpx` e a expor o comando `sintetica`. A suíte padrão exclui os marcadores `perf` e `live`. Nada da configuração da feature 001 foi removido.

**`llm-provider` (novo).** A porta `LLMProvider` tem 2 adaptadores. O `ExternalAPIProvider` atende OpenAI, Anthropic, Gemini e Ollama por 1 cliente `httpx`. O `HarnessAgentProvider` lê respostas enviadas pelo agente por arquivo. Quatro decoradores aplicam teto, concorrência, mascaramento e retry, nessa ordem. A fábrica `build_provider` lê a política, escolhe o provedor e devolve o motivo da escolha.

**`pii-guard` (sem mudança).** É consumido só pela fachada `PiiGuard.for_dataset` e `mask`. `PolicyError` e falha de escrita viram `MaskingUnavailable`, como manda o adendo 001.

**`sample-preview` e `batch-generator` (futuros).** Devem chamar `build_provider`, tratar `HarnessResponsePending` (mostrar o comando ao agente) e pedir autorização quando `estimate_cost(...).requires_authorization` for verdadeiro.

## Preservadas

Feature greenfield: não há regras 🟢 de legado. Os 92 testes da feature 001 continuam verdes.

## Modificadas

Feature greenfield: nenhuma regra 🟢 alterada ou removida.
