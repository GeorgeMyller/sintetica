# Investigation: schema-builder

> Identificador: `003-schema-builder`
> Data: `2026-10-12`
> Fonte: `_reversa_forward/003-schema-builder/roadmap.md`

## 1. Pesquisa de fundo

### 1.1 Pydantic v2
- 🟢 `Annotated[T, Field(...)]` aceita `ge`, `le`, `min_length`, `max_length`, `pattern` e `decimal_places`. Em `list`, `min_length` e `max_length` limitam o número de itens.
- 🟢 `ConfigDict(extra="forbid")` rejeita chaves não declaradas.
- 🟢 O modo padrão (lax) aceita `"19.9"` para `Decimal` e `"42"` para `int`. Isso atende a Q37 para decimal.
- 🟢 No modo JSON, `Decimal` é serializado como texto. Por isso a serialização do dataset fica em `formats.py` (D-15), e não no `model_dump`.
- 🟡 Nomes de campo iniciados em `model_` geram aviso do espaço protegido. A normalização acrescenta `_` (D-06).
- 🟢 `Literal["a", "b"]` produz `enum` no JSON Schema exportado.
- 🟢 `pattern` usa o motor de regex do Pydantic (Rust). Algumas construções do `re` do Python, como lookbehind, não são aceitas por esse motor. A validação semântica precisa compilar o padrão nos 2 motores, ou o erro só aparece na importação. Ação: D-05 tenta criar um `TypeAdapter` com o padrão e converte a falha em `SchemaIssue`.

### 1.2 Geração de código segura
- 🟢 `repr()` de `str` produz um literal Python válido para qualquer texto, inclusive aspas, barras e quebras de linha.
- 🟡 `ast.unparse` muda a formatação entre versões do Python. Montar linhas em ordem fixa garante saída idêntica byte a byte (RF-05).

### 1.3 Importação dinâmica
- 🟢 `importlib.util.spec_from_file_location(nome, caminho)` com `module_from_spec` e `loader.exec_module` importa um arquivo fora do `sys.path`.
- 🟡 Nome de módulo único por versão (`sintetica_dataset_<slug>_<hash8>`) evita reaproveitar um módulo antigo em `sys.modules`.

### 1.4 CSV
- 🟢 O módulo `csv` da biblioteca padrão aplica as aspas da RFC 4180. O separador `|` dentro da célula não conflita com a vírgula.

## 2. Alternativas avaliadas

| Alternativa | Prós | Contras | Veredito |
|-------------|------|---------|----------|
| `datamodel-code-generator` (JSON Schema → Pydantic) | Gerador maduro | Dependência pesada; saída varia por versão; sem controle de `repr` e de nomes | Descartada |
| `pydantic.create_model` em memória, sem `schema.py` | Sem código gerado | A spec exige `schema.py` legível e versionado; sem verificação estática | Descartada |
| Templates Jinja | Legível | Dependência extra; risco de interpolar texto cru | Descartada |
| Montagem de linhas + `repr()` | Determinístico, seguro, sem dependência | Código do gerador mais longo | **Escolhida** |

## 3. Padrões aplicáveis

- 🟡 **Protocolo por arquivo** (Q29): o agente escreve o rascunho; o runtime valida e materializa.
- 🟡 **Pipeline de validação em 2 etapas:** estrutura (Pydantic) e semântica (regras entre atributos).
- 🟡 **Artefato com selo de versão:** o cabeçalho do código gerado amarra o código à definição.

## 4. Fontes externas

- Documentação Pydantic v2: Fields, Annotated, ConfigDict, JSON Schema, plugin do mypy.
- Documentação Python: `importlib.util`, `keyword`, `unicodedata`, `csv`, `decimal`.
- RFC 4180 (CSV).
