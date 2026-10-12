## Módulo `schema` (`src/sintetica/schema/`)

🟢 **Propósito:** contrato de dados de cada dataset. O agente grava um rascunho declarativo (`schema.draft.json`); o `build` valida, normaliza nomes, achata para CSV, gera o código Pydantic v2 (`schema.py`) de forma determinística, exporta o JSON Schema e controla a revisão (rodadas e aprovação). Também serializa registros válidos para JSON, JSONL e CSV.

### Arquivos

| Arquivo | Papel |
|---------|-------|
| `spec.py` | Meta-modelo: `SchemaSpecModel`, `FieldSpecModel`, `Constraints`, `SchemaIssue`; `parse_spec`, `dump_spec` |
| `checks.py` | Validação semântica (`check_spec`), `parse_bound`, `pattern_error` |
| `names.py` | `normalize_name`, `normalize_names` (snake_case ASCII, reservados, repetidos) |
| `csvflat.py` | `flatten_for_csv`, `LIST_SEPARATOR = "|"` |
| `codegen.py` | `generate_code`, `py_str` (literal seguro) |
| `version.py` | `schema_version` (SHA-256 do JSON canônico), `canonical_json`, `pretty_json` |
| `loader.py` | `read_spec`, `load_record_model`, `import_record`, `export_json_schema`, `header_version` |
| `state.py` | `SchemaState`, `next_state`, `approved`, `load_state`, `save_state`, `write_atomic` |
| `intent.py` | Leitura tolerante de `intent.json` (`Intent`) e `default_spec` |
| `render.py` | Tabela Markdown do contrato e `diff_specs` |
| `formats.py` | `to_json_obj`, `to_json_text`, `to_jsonl_line`, `to_csv_row`, `csv_columns` |
| `walk.py` | `walk`, `count_fields` |
| `validators.py` | `no_pipe` (usado pelo código gerado) |
| `service.py` | `build`, `show`, `approve` |

### Funções e métodos principais

| Função | Assinatura | Retorno | Local |
|--------|-----------|---------|-------|
| `build` | `(project_dir, slug)` | `CommandResult` (0, 2, 6, 7) | `service.py:133` |
| `approve` | `(project_dir, slug)` | `CommandResult` (0, 2, 7) | `service.py:207` |
| `show` | `(project_dir, slug)` | `CommandResult` | `service.py:193` |
| `check_spec` | `(spec)` | `list[SchemaIssue]` | `checks.py:138` |
| `normalize_names` | `(spec)` | `(spec, avisos)` | `names.py:72` |
| `flatten_for_csv` | `(spec)` | `(spec plano, avisos)` ou `list[SchemaIssue]` | `csvflat.py:52` |
| `generate_code` | `(spec, version)` | código-fonte | `codegen.py:262` |
| `schema_version` | `(spec)` | SHA-256 hex (64) | `version.py:20` |
| `load_record_model` | `(dataset_dir)` | `type[BaseModel]` | `loader.py:83` |
| `to_jsonl_line` | `(record)` | JSON compacto com decimal exato | `formats.py` |
| `to_csv_row` | `(record)` | `dict[str, str]` | `formats.py:120` |

### Algoritmos e regras

1. 🟢 **Pipeline do `build`** (`service.py:90-190`): lê a intenção (`intent.py`); sem rascunho e com estrutura indefinida, usa o contrato padrão de 1 campo `descricao` (`intent.py:51`); valida o meta-modelo; recusa formato diferente do da intenção; aplica `check_spec`; normaliza nomes; em CSV, achata e normaliza de novo; calcula a versão; gera o código num arquivo de preparo `.schema.staged.py`, importa e exporta o JSON Schema; só então grava `schema.json`, `schema.py`, `record.schema.json` e `schema.state.json`. Falha do código gerado grava o traceback em `errors.log` (código 7).
2. 🟢 **Validação semântica** (`checks.py`): limite de 100 campos (sem contar itens de lista); conversa só em JSON ou JSONL; restrições permitidas por tipo (`ALLOWED`); `list` exige `items`, `object` exige `fields`; `enum` exige `choices` não vazias e sem repetidos; `ge`/`le` convertidos ao tipo e sem contradição; `min_length ≤ max_length`; `pattern` precisa compilar no `re` e no validador do Pydantic; `casas_decimais` de 0 a 10.
3. 🟢 **Normalização de nomes** (`names.py`): NFKD → ASCII → minúsculas → `[^a-z0-9]+` vira `_`; vazio vira `campo`; começa com dígito vira `campo_…`; palavras-chave, nomes do `BaseModel`, nomes usados no código gerado e prefixo `model_` ganham `_`; repetidos no mesmo nível ganham `_2`, `_3`. Cada renomeação gera um aviso.
4. 🟢 **CSV plano** (`csvflat.py`): objeto vira colunas com prefixo (`endereco_cidade`); campo de objeto opcional fica opcional; lista de valores simples vira 1 coluna com `|`; lista de objetos ou de listas é recusada; `enum` de lista com `|` é recusado; itens de texto ganham o validador `no_pipe`.
5. 🟢 **Versão** (`version.py`): SHA-256 do JSON canônico (`sort_keys`, separadores compactos, sem valores ausentes). Mesma definição, mesma versão.
6. 🟢 **Geração de código segura** (`codegen.py`): nenhum texto da definição vira código; textos entram por `py_str` (escapa barra, aspas, controle e não imprimíveis); nomes já normalizados; tipos auxiliares (`…Choices`, `…Type`) com nomes únicos; tudo expandido com vírgula final (estável sob `ruff format`); linhas acima de 100 caracteres ganham `# noqa: E501`; cabeçalho com `# schema_version: <sha>`.
7. 🟢 **Carga com regeneração** (`loader.py:83-90`): se a versão do cabeçalho do `schema.py` não bate com a do `schema.json`, regera o arquivo antes de importar; importa com nome de módulo único e sem gerar `__pycache__`.
8. 🟢 **Rodadas de revisão** (`state.py:67-82`): versão nova sobre contrato existente soma 1 rodada; no Expresso, o `build` já aprova; a partir de 5 rodadas sem aprovação, a saída sugere reiniciar a entrevista.
9. 🟢 **Serialização** (`formats.py`): `to_json_text` troca cada `Decimal` por um marcador com nonce aleatório e devolve o número exato (`19.90`), nunca texto; casas decimais vêm das anotações (inclusive de itens de lista); CSV com decimais em casas fixas, listas unidas por `|`, booleanos `true`/`false`, datas ISO.
10. 🟢 **Conversa** (`codegen.py:200-234`): `Record(messages: list[Message] ≥ 1, labels: Labels)`, `Message.role ∈ {system, user, assistant}`, `content` com ao menos 1 caractere.

### Tratamento de erros

🟢 `SchemaIssue(path, message)` por problema (código 6); `GeneratedCodeError` (código 7, com `errors.log`); `SchemaNotFoundError`; `IntentError` local (código 2).

### Observações para as próximas fases

- 🟡 `schema/intent.py` lê a intenção por conta própria, sem usar `sintetica.intent`: não confere `confirmed_at` (lacuna conhecida desde a feature 003).
- 🟡 `write_atomic` existe em 3 cópias: `fsutil.py`, `schema/state.py` e `providers/harness/store.py` (`_write_atomic`).

### Constantes

| Constante | Valor | Local |
|-----------|-------|-------|
| `MAX_FIELDS` | 100 | `checks.py:15` |
| `MAX_DECIMAL_PLACES` | 10 | `checks.py:16` |
| `MAX_ROUNDS` | 5 | `state.py:14` |
| `LIST_SEPARATOR` | `|` | `csvflat.py:8` |
| `MAX_LINE` | 100 | `codegen.py:20` |
| Arquivos | `schema.draft.json`, `schema.json`, `schema.py`, `record.schema.json`, `schema.state.json`, `errors.log` | `service.py`, `loader.py`, `state.py` |

### Dependências

🟢 Pydantic. Usado por `sample`, `batch` e `quality`.
