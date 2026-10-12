# Legacy Impact: schema-builder

> Identificador: `003-schema-builder`
> Data: `2026-10-12`
> Feature greenfield, sem legado pré-existente. Âncora: prd.md + specs SDD.
> Política de edição no momento da execução: `allowLegacyEdits: true`, `allowedPaths: []` (projeto inteiro liberado, sem restrição de caminho).

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `pyproject.toml` | Esqueleto Python (`_reversa_sdd/prd.md#6. Restrições`) | componente-novo | MEDIUM | Nova dependência de runtime `pydantic>=2.7`, plugin `pydantic.mypy`, marcador `codegen` |
| `uv.lock` | Esqueleto Python | componente-novo | LOW | Pydantic 2.14.1 e `pydantic-core` 2.50.1 |
| `src/sintetica/cli.py` | Comando `sintetica` (`_reversa_sdd/addenda/002-llm-provider.md`) | delta-de-contrato-externo | MEDIUM | Subcomando `schema` (`build`, `show`, `approve`) e códigos de saída 6 e 7; `request` e `submit` inalterados |
| `src/sintetica/schema/spec.py`, `walk.py` | `schema-builder` (`_reversa_sdd/sdd/schema-builder.md#9. Modelo de Dados`) | componente-novo | MEDIUM | Meta-modelo da definição, com `kind` e `casas_decimais` |
| `src/sintetica/schema/checks.py` | `schema-builder` (RF-09 a RF-11) | componente-novo | MEDIUM | Validação semântica, incluindo regex nos 2 motores |
| `src/sintetica/schema/names.py` | `schema-builder` (EC-01) | componente-novo | LOW | Normalização de nomes |
| `src/sintetica/schema/csvflat.py`, `validators.py` | `schema-builder` (RF-06, Q35) | componente-novo | MEDIUM | Regras de CSV |
| `src/sintetica/schema/codegen.py` | `schema-builder` (RF-02, RF-03, RF-05) | componente-novo | HIGH | Gera código que roda no processo do usuário; segurança depende de `py_str` (RN-02) |
| `src/sintetica/schema/loader.py` | `schema-builder` (RF-08, Q36) | componente-novo | HIGH | Importa `schema.py` só com versão conferida |
| `src/sintetica/schema/version.py`, `state.py`, `render.py`, `intent.py`, `service.py` | `schema-builder` (RF-07, RF-09, RF-10, EC-06) | componente-novo | MEDIUM | Versão, estado, tabela, diferenças, intenção e orquestração |
| `src/sintetica/schema/formats.py`, `__init__.py` | `schema-builder` (Q37) e consumidores `sample-preview`, `batch-generator`, `quality-evaluator` | componente-novo | HIGH | API pública de validação e serialização do dataset |
| `tests/schema/*.py`, `tests/fixtures/schema/*.json` | `schema-builder` | componente-novo | LOW | 121 testes e 7 definições de teste |
| `docs/schema-builder.md` | `schema-builder` | componente-novo | LOW | Formato do rascunho para a skill, regras de CSV e API |

## Diff conceitual por componente

**Comando `sintetica`.** Ganha o subcomando `schema`, importado de forma tardia para não carregar o Pydantic em `request` e `submit`. Os códigos 6 (definição inválida) e 7 (código gerado inválido ou desatualizado) somam-se aos 0, 2, 3, 4 e 5 da feature 002.

**schema-builder.** Componente novo, conforme `_reversa_sdd/sdd/schema-builder.md`, com estes desvios:
- A definição ganhou `kind` (`records` ou `conversation`) e a restrição `casas_decimais` (Q37). `schema_version` saiu da definição e foi para `schema.state.json` e para o cabeçalho de `schema.py`.
- O agente grava `schema.draft.json`; o runtime grava `schema.json` (D-03).
- A verificação estrita de tipos do código gerado roda na suíte de testes, não no runtime (Q36).
- Em CSV, `schema.json` guarda a definição já plana; listas simples viram 1 coluna com `|` (Q35).
- `csv_columns` recebe o modelo `Record`, e não a pasta do dataset.

## Preservadas

Nenhuma. Feature greenfield, sem regras 🟢 extraídas de código anterior.

## Modificadas

Nenhuma. Feature greenfield, sem regras 🟢 extraídas de código anterior.
