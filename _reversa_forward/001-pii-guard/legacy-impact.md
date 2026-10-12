# Legacy Impact: pii-guard

> Identificador: `001-pii-guard`
> Data: `2026-10-09`
> Feature greenfield, sem legado pré-existente. Âncora: prd.md + specs SDD.
> Política de edição no momento da execução: `allowLegacyEdits: true`, `allowedPaths: []` (projeto inteiro liberado, sem restrição de caminho).

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `pyproject.toml` | Esqueleto Python (`_reversa_sdd/prd.md#6. Restrições`) | componente-novo | MEDIUM | Define runtime, dependências e regras de qualidade de todo o projeto Python |
| `uv.lock` | Esqueleto Python | componente-novo | LOW | Gerado pelo `uv sync` |
| `.gitignore` | Esqueleto Python | componente-novo | LOW | Arquivo não existia; ignora caches, `.venv/` e `datasets/` |
| `src/sintetica/__init__.py`, `src/sintetica/py.typed` | Esqueleto Python | componente-novo | LOW | Pacote raiz tipado |
| `src/sintetica/pii/domain.py` | `pii-guard` (`_reversa_sdd/sdd/pii-guard.md#9. Modelo de Dados`) | componente-novo | MEDIUM | Tipos públicos consumidos por 5 componentes |
| `src/sintetica/pii/checksums.py` | `pii-guard` | componente-novo | LOW | Funções puras de dígito verificador e Luhn |
| `src/sintetica/pii/normalize.py` | `pii-guard` | componente-novo | MEDIUM | Define a forma canônica do hash; mudança invalida allowlists existentes |
| `src/sintetica/pii/ports.py` | `pii-guard` | componente-novo | LOW | Protocolos `Detector`, `SubstituteGenerator`, `AllowlistStore` |
| `src/sintetica/pii/detectors.py` | `pii-guard` (`#6. Requisitos Funcionais`, RF-01 a RF-04) | componente-novo | HIGH | Regras de detecção sustentam a métrica de 0 vazamentos do PRD |
| `src/sintetica/pii/substitutes.py` | `pii-guard` (RF-06, RF-09) | componente-novo | MEDIUM | Valores falsos inseridos nos datasets |
| `src/sintetica/pii/allowlist.py` | `pii-guard` (RF-07, RF-08) | componente-novo | HIGH | Critério de vazamento aprovado na Q23 |
| `src/sintetica/pii/policy.py` | `pii-guard` (EC-03) | componente-novo | MEDIUM | Lê `pii_custom_patterns` de `.sintetica/policy.json` |
| `src/sintetica/pii/guard.py`, `src/sintetica/pii/__init__.py` | `pii-guard` (contrato `PiiGuard`) | componente-novo | HIGH | API interna consumida por `intent-interview`, `sample-preview`, `llm-provider`, `batch-generator`, `quality-evaluator` |
| `tests/pii/*.py`, `tests/fixtures/pii_reference/*.json` | `pii-guard` | componente-novo | LOW | 92 testes, 1 teste de desempenho e 280 casos de referência |
| `docs/pii-guard.md` | `pii-guard` | componente-novo | LOW | Uso, política e limites conhecidos |

## Diff conceitual por componente

**Esqueleto Python.** O projeto passa a ter um pacote Python `sintetica` em layout `src`, gerido por `uv`, com Python ≥ 3.10, `mypy --strict`, `ruff` e `pytest-cov`. O `ruff` exclui as pastas do Reversa (`.agents`, `.claude`, `.reversa`, `_reversa_*`) e `docs`. Os testes de desempenho ficam fora da suíte padrão (`-m perf`).

**pii-guard.** Componente novo, conforme `_reversa_sdd/sdd/pii-guard.md`, com 2 desvios registrados:
- `MaskResult` ganhou `fallbacks` e `PiiGuard` ganhou `allowlist_available` (EC-04 e EC-06 da spec), previstos no `data-delta.md`.
- `mask` ignora achados que já estão na allowlist, para ser idempotente. A spec não definia esse caso.

O contrato `PiiGuard` (`scan`, `mask`, `leaks`, `coverage`, `for_dataset`) segue o roadmap, seção 7.

## Preservadas

Nenhuma. Feature greenfield, sem regras 🟢 extraídas de código anterior.

## Modificadas

Nenhuma. Feature greenfield, sem regras 🟢 extraídas de código anterior.
