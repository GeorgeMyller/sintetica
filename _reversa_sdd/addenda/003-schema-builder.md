# Adendo: schema-builder (contrato de dados do dataset)

> Identificador: `003-schema-builder`
> Data: `2026-10-12`
> Cenário: greenfield

## Vigência

Vigente desde 2026-10-12.
Superado pela re-extração de 2026-10-12.

## Resumo da entrega

O pacote `sintetica.schema` transforma a intenção do usuário no contrato de dados do dataset. O agente do harness grava um rascunho declarativo (`schema.draft.json`); o comando `sintetica schema build` valida o rascunho em 2 etapas (estrutura e semântica), normaliza nomes, aplica as regras de CSV e gera, por um gerador determinístico, `schema.json`, `schema.py` (classe `Record` em Pydantic v2), `record.schema.json` e `schema.state.json`. O runtime nunca executa código escrito pelo modelo. Os comandos `show` e `approve` completam a revisão. A API pública (`load_record_model`, `to_jsonl_line`, `to_csv_row`, `to_json_obj`, `csv_columns`) valida e serializa registros para os próximos componentes.

A entrega adicionou Pydantic v2 como dependência de runtime e o subcomando `schema` ao comando `sintetica`.

Ações concluídas: 29 de 29 (`progress.jsonl` com 29 registros). Verificação: 326 testes (205 das features 001 e 002 + 121 novos), cobertura de 99% em `sintetica.schema`, `mypy --strict` e `ruff` sem erros em 74 arquivos, verificação estática do código gerado (`pytest -m codegen`). Auditoria do revisor Antigravity: aprovada.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/prd.md` | 6. Restrições (Técnica) | componente-novo | Pydantic v2 (`pydantic>=2.7`) agora é dependência de runtime, com o plugin `pydantic.mypy`; a suíte padrão inclui o marcador `codegen`. |
| `_reversa_sdd/prd.md` | 3. Métricas de sucesso (conformidade ≥ 95%) | componente-novo | A conformidade passa a ser medida por `Record.model_validate`, com `extra="forbid"`: chave não declarada conta como não conforme. |
| `_reversa_sdd/sdd/schema-builder.md` | 6. Requisitos Funcionais (RF-01, RF-02) | componente-novo | Leia RF-01 como protocolo por arquivo: o agente grava `schema.draft.json` e `sintetica schema build` grava `schema.json`. O gerador é determinístico e todo texto entra como literal escapado. |
| `_reversa_sdd/sdd/schema-builder.md` | 6. Requisitos Funcionais (RF-03, RF-04) | componente-novo | Implementados os 9 tipos e as 7 restrições, mais `casas_decimais` (Q37). `pattern` precisa ser aceito pelo `re` do Python e pelo validador do Pydantic (sem lookbehind ou lookahead). |
| `_reversa_sdd/sdd/schema-builder.md` | 6. Requisitos Funcionais (RF-05) | componente-novo | O formato conversacional é marcado por `kind: "conversation"`; os campos da definição viram os rótulos de `labels`. |
| `_reversa_sdd/sdd/schema-builder.md` | 6. Requisitos Funcionais (RF-06) | componente-novo | Leia RF-06 com a Q35: lista de valores simples vira 1 coluna com `|` (itens de texto não podem conter `|`); só lista de objetos ou de listas é recusada. Objeto opcional gera colunas opcionais. |
| `_reversa_sdd/sdd/schema-builder.md` | 6. Requisitos Funcionais (RF-08) | componente-novo | Leia RF-08 com a Q36: o runtime valida por importação, presença de `Record` e exportação do JSON Schema; `mypy --strict` e `ruff` sobre o código gerado rodam na suíte de testes. Falha gera código de saída 7 e `errors.log`. |
| `_reversa_sdd/sdd/schema-builder.md` | 6. Requisitos Funcionais (RF-10) | componente-novo | `schema_version` é o SHA-256 do JSON canônico de `schema.json` e fica em `schema.state.json` e no cabeçalho de `schema.py`, não dentro da definição. |
| `_reversa_sdd/sdd/schema-builder.md` | 9. Modelo de Dados | componente-novo | Leia `SchemaSpec` com os campos novos `kind` e `casas_decimais` e sem `schema_version`; em CSV, `schema.json` guarda a definição já plana. Arquivos por dataset em `_reversa_forward/003-schema-builder/data-delta.md#2`. |
| `_reversa_sdd/sdd/schema-builder.md` | 14. Open Questions (OQ-01, OQ-02) | componente-novo | Mantidos os limites da spec: 100 campos contando aninhados e sugestão de `/sintetica-start` na 5ª rodada sem aprovação. |
| `_reversa_sdd/addenda/002-llm-provider.md` | Comando `sintetica` | delta-de-contrato-externo | O comando ganhou `schema build | show | approve` e os códigos de saída 6 e 7; `request` e `submit` estão inalterados e aceitam o `record.schema.json` gerado em `--schema`. |
| `_reversa_sdd/sdd/sample-preview.md`, `batch-generator.md`, `quality-evaluator.md` | 10. Integrações e Dependências (`schema-builder`) | componente-novo | A dependência existe: carregue o contrato com `sintetica.schema.load_record_model(dataset_dir)` e serialize com `to_jsonl_line` ou `to_csv_row` (decimal exato no JSON, casas fixas no CSV). |

## Regras sob vigilância

W001, W002, W003, W004, W005, W006, W007, W008, W009, W010. Todos em "Observações", sem peso de regressão (cenário greenfield). Detalhes em `_reversa_forward/003-schema-builder/regression-watch.md`.

## Fontes

- `_reversa_forward/003-schema-builder/legacy-impact.md`
- `_reversa_forward/003-schema-builder/regression-watch.md`
- `_reversa_forward/003-schema-builder/requirements.md`
- `_reversa_forward/003-schema-builder/data-delta.md`
- `_reversa_forward/003-schema-builder/interfaces/schema-cli.md`
- `_reversa_forward/003-schema-builder/progress.jsonl`
- `_reversa_forward/003-schema-builder/actions.md`
