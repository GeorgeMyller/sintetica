# Actions: schema-builder (contrato de dados do dataset)

> Identificador: `003-schema-builder`
> Data: `2026-10-12`
> Roadmap: `_reversa_forward/003-schema-builder/roadmap.md`
> Fontes auxiliares: `data-delta.md`, `interfaces/schema-cli.md`, `requirements.md` (22 cenários Gherkin).

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 29 |
| Paralelizáveis (`[//]`) | 17 |
| Maior cadeia de dependência | 11 (T001 → T002 → T012 → T016 → T017 → T018 → T019 → T024 → T025 → T026 → T028) |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Acrescentar `pydantic>=2.7` às dependências de runtime, `plugins = ["pydantic.mypy"]` em `[tool.mypy]` e o marcador `codegen` (incluído na suíte padrão) em `[tool.pytest.ini_options]` (D-01, D-20) | - | `[//]` | `pyproject.toml` | 🟢 | `[X]` |
| T002 | Executar `uv sync` para instalar o Pydantic e atualizar o `uv.lock` | T001 | - | `uv.lock` | 🟢 | `[X]` |
| T003 | Criar o pacote `sintetica.schema` com `__init__.py` mínimo (docstring) e a pasta `tests/schema/` | - | `[//]` | `src/sintetica/schema/__init__.py` | 🟡 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Criar as definições de teste: `all_types.json` (9 tipos), `constraints.json` (7 restrições + `casas_decimais`), `conversation.json`, `csv_nested.json` (objeto + lista simples), `hostile_text.json` (aspas, quebra de linha, `import os`), `csv_list_objects.json` e `contradictions.json` (inválidas) | - | `[//]` | `tests/fixtures/schema/*.json` | 🟡 | `[X]` |
| T005 | Escrever testes de estrutura e semântica: erros com caminho (RF-02), contradições (RF-09), regex inválida nos 2 motores e enum vazio (RF-10), 101 campos contando aninhados (RF-11), restrição incompatível com o tipo | T003, T004 | `[//]` | `tests/schema/test_spec_checks.py` | 🟡 | `[X]` |
| T006 | Escrever testes de normalização de nomes: acentos, espaços, palavras reservadas, prefixo `model_`, dígito inicial, repetidos `_2` (RF-08) | T003 | `[//]` | `tests/schema/test_names.py` | 🟡 | `[X]` |
| T007 | Escrever testes da transformação CSV: achatamento com prefixo, lista simples mantida com item sem `|`, lista de objetos recusada com orientação para JSON ou JSONL, avisos (RN-04, RF-07) | T003, T004 | `[//]` | `tests/schema/test_csvflat.py` | 🟢 | `[X]` |
| T008 | Escrever testes do gerador: determinismo byte a byte (RF-05), 1 registro válido por tipo (RF-03), 1 violação por restrição (RF-04), conversa com papel `bot` rejeitado (RF-06), texto hostil intacto e sem execução, cabeçalho com versão | T003, T004 | `[//]` | `tests/schema/test_codegen.py` | 🟡 | `[X]` |
| T009 | Escrever a verificação estática do código gerado: gerar todos os `schema.py` das definições válidas numa pasta temporária e rodar `mypy --strict`, `ruff check` e `ruff format --check` numa chamada cada, marcado `codegen` (RF-20, D-20) | T003, T004 | `[//]` | `tests/schema/test_codegen_static.py` | 🟢 | `[X]` |
| T010 | Escrever testes de serialização: decimal `"19.9"` com 2 casas vira número `19.90` no JSON e texto `19.90` no CSV, lista `["a","b"]` vira `a|b`, ordem das colunas (RF-19) | T003 | `[//]` | `tests/schema/test_formats.py` | 🟢 | `[X]` |
| T011 | Escrever testes de serviço e CLI: `build` com sucesso, códigos 2, 6 e 7, `errors.log`, modo Expresso aprovado, rodadas e sugestão na 5ª, estrutura indefinida, diferenças, `show`, `approve`, e aceitação de `record.schema.json` por `sintetica request --schema` | T003 | `[//]` | `tests/schema/test_service_cli.py` | 🟡 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T012 | Implementar o meta-modelo Pydantic `SchemaSpecModel` e `FieldSpecModel` com `extra="forbid"`, padrões (`kind="records"`, `required=true`, `description=""`) e `parse_spec(dict) -> SchemaSpecModel | list[SchemaIssue]` com caminhos legíveis (D-04, data-delta.md#1) | T002, T003 | - | `src/sintetica/schema/spec.py` | 🟡 | `[X]` |
| T013 | Implementar `check_spec(spec) -> list[SchemaIssue]`: restrição compatível com o tipo, mínimo ≤ máximo, regex compilável no `re` e no motor do Pydantic (`TypeAdapter`), enum com valores únicos e não vazios, `items` e `fields` obrigatórios, `casas_decimais` de 0 a 10, até 100 campos contando aninhados (D-05) | T012 | - | `src/sintetica/schema/checks.py` | 🟡 | `[X]` |
| T014 | Implementar `normalize_names(spec) -> (spec, avisos)` por nível de objeto, conforme D-06 | T003 | `[//]` | `src/sintetica/schema/names.py` | 🟡 | `[X]` |
| T015 | Implementar `flatten_for_csv(spec) -> (spec, avisos) | list[SchemaIssue]`: objetos com prefixo (recursivo), lista simples com `pattern` de item que exclui `|`, lista de objetos recusada (D-08) | T012 | - | `src/sintetica/schema/csvflat.py` | 🟢 | `[X]` |
| T016 | Implementar `schema_version(spec) -> str` (SHA-256 do JSON canônico) e `canonical_json(spec) -> str` (D-12) | T012 | `[//]` | `src/sintetica/schema/version.py` | 🟢 | `[X]` |
| T017 | Implementar o gerador para registros: mapeamento dos 9 tipos, `Annotated[T, Field(...)]` com as restrições e `decimal_places`, opcionais `T | None = None`, classes aninhadas PascalCase sem colisão, `ConfigDict(extra="forbid")`, todo texto por `repr()` (D-09, D-10, D-11) | T012, T016 | - | `src/sintetica/schema/codegen.py` | 🟡 | `[X]` |
| T018 | Completar o gerador: modelo de conversa `Message`, `Labels`, `Record` (D-07), cabeçalho com versão, imports mínimos em ordem fixa e saída no estilo `ruff format` | T017 | - | `src/sintetica/schema/codegen.py` | 🟡 | `[X]` |
| T019 | Implementar o carregador: ler a versão do cabeçalho, comparar com `schema.json`, importar por `spec_from_file_location` com nome único por versão, conferir `Record`, exportar `model_json_schema()`; falha vira `GeneratedCodeError` (D-13, D-14) | T018 | - | `src/sintetica/schema/loader.py` | 🟢 | `[X]` |
| T020 | Implementar `to_json_obj`, `to_jsonl_line`, `to_csv_row` e `csv_columns`, com decimal exato como número no JSON, decimal com casas fixas no CSV e listas unidas por `|` (D-15) | T012 | `[//]` | `src/sintetica/schema/formats.py` | 🟢 | `[X]` |
| T021 | Implementar a tabela Markdown (campo, tipo, obrigatório, restrições, descrição, notação de ponto) e `diff_specs(antes, depois)` com novos, removidos e alterados por atributo (RF-14, RF-15) | T012 | `[//]` | `src/sintetica/schema/render.py` | 🟡 | `[X]` |
| T022 | Implementar `SchemaState` com leitura, gravação atômica e regra de rodadas (D-16) | T016 | `[//]` | `src/sintetica/schema/state.py` | 🟡 | `[X]` |
| T023 | Implementar o leitor tolerante de `intent.json` (`slug`, `mode`, `format`, `structure.status`) e a definição padrão de estrutura indefinida (D-17, D-18) | T003 | `[//]` | `src/sintetica/schema/intent.py` | 🟡 | `[X]` |
| T024 | Implementar `build(project_dir, slug)`: intenção → rascunho ou padrão → `parse_spec` → `check_spec` → nomes → CSV → `schema.json` → gerador → carregador → `record.schema.json` → estado (rodadas, Expresso) → saída formatada; gravação atômica e `errors.log` em falha, sem apagar artefatos anteriores | T013, T014, T015, T019, T021, T022, T023 | - | `src/sintetica/schema/service.py` | 🟡 | `[X]` |
| T025 | Implementar `show(project_dir, slug)` e `approve(project_dir, slug)` com as regras de `interfaces/schema-cli.md#2` e `#3` | T024 | - | `src/sintetica/schema/service.py` | 🟡 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T026 | Acrescentar o subcomando `schema` (`build`, `show`, `approve`, `--project-dir`) ao `sintetica`, com importação tardia de `sintetica.schema` e códigos 0, 2, 6 e 7; `request` e `submit` inalterados (D-19, R-07) | T025 | - | `src/sintetica/cli.py` | 🟡 | `[X]` |
| T027 | Expor a API pública de `sintetica.schema`: `load_record_model`, `to_json_obj`, `to_jsonl_line`, `to_csv_row`, `csv_columns`, `SchemaIssue`, `GeneratedCodeError`, com `__all__` (roadmap.md#7) | T020, T025 | - | `src/sintetica/schema/__init__.py` | 🟡 | `[X]` |
| T028 | Completar os testes até cobertura ≥ 80% em `sintetica.schema`, com os 22 cenários Gherkin cobertos, os 205 testes anteriores passando e `mypy --strict` e `ruff` sem erros no projeto (critério de pronto) | T026, T027, T005, T006, T007, T008, T009, T010, T011 | - | `tests/schema/` | 🟡 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T029 | Escrever a documentação curta: formato do rascunho para o agente (tipos, restrições, `kind`, `casas_decimais`), regras de CSV, comandos `build`, `show`, `approve`, códigos de saída e API para os próximos componentes | T027 | `[//]` | `docs/schema-builder.md` | 🟡 | `[X]` |

## Notas de execução

<!--
Reservado para /reversa-coding registrar avisos ou observações que surgiram durante a execução.
Não use isso para corrigir ações, edits manuais ficam fora desse arquivo, vão direto no código.
-->

- O `SKILL.md` da skill `sintetica-schema` fica fora desta feature. A pasta e o formato das skills do sintetica serão definidos com o `cli-installer`. A T029 documenta o que a skill precisa instruir ao agente.
- 2026-10-12, T002: Pydantic instalado na versão 2.14.1 (`pydantic-core` 2.50.1).
- 2026-10-12, T017/T018: o código gerado inicial falhou em `ruff`: `noqa` de cabeçalho sem uso, 2 linhas em branco após os imports antes de atribuição e `AfterValidator` sem import. Corrigido; linhas acima de 100 caracteres (só textos da definição) recebem `# noqa: E501` individual.
- 2026-10-12, T024: o arquivo de staging `.schema.py.tmp` não era importável (o `importlib` exige sufixo `.py`); renomeado para `.schema.staged.py`. A importação passou a desligar `__pycache__` para não sujar a pasta do dataset.
- 2026-10-12, T020: casas decimais declaradas no item de uma lista eram ignoradas na serialização; a leitura passou a percorrer a anotação do item. Corrigido também `casas_decimais = 0`, que era tratado como ausente.
- 2026-10-12, T012: `ge`/`le` com `true` eram convertidos em `1` pelo Pydantic antes da validação; o tipo `Bound` passou a aceitar `bool` primeiro, e a validação semântica o recusa.
- 2026-10-12, T009: acrescentado um controle negativo (arquivo com erro deve falhar em `mypy` e `ruff`), porque a verificação estática roda em 0,1 s com o cache do `mypy`.
- 2026-10-12, T027: `csv_columns` recebe o modelo `Record` (não a pasta do dataset, como no roadmap#7) e a API ganhou `to_jsonl_line`; módulos auxiliares novos: `walk.py` e `validators.py`.
- 2026-10-12, T028: 326 testes passam (205 anteriores + 121 novos); cobertura de `sintetica.schema` em 99%; `mypy --strict` e `ruff` sem erros; os 22 cenários Gherkin têm teste correspondente.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-12 | Versão inicial gerada por `/reversa-to-do` | reversa |
