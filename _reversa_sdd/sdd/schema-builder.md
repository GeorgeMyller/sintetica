# Spec: schema-builder

> Selo 🟢 CONFORME CÓDIGO em todos os itens, salvo marcação. Fonte: `src/sintetica/schema/`, testes `tests/schema/` (inclui `-m codegen`).
> Consolida os adendos `003-schema-builder.md` e `005-sample-preview.md` (parâmetro `indent`). Versão planejada em `sdd/_planejado/schema-builder.md`.

**Versão:** 2.0 (extraída do código)
**Status:** Implementado
**Autor:** reversa-writer
**Data:** 2026-10-12

---

## 1. Resumo

🟢 O `schema-builder` é o pacote `sintetica.schema` e a skill `sintetica-schema`. O agente grava um rascunho declarativo (`schema.draft.json`); `sintetica schema build` valida, normaliza nomes, achata para CSV, gera de forma determinística o `schema.py` (Pydantic v2, classe `Record`), exporta o JSON Schema e controla a revisão até `schema approve`. O pacote também serializa registros para JSON, JSONL e CSV com decimal exato.

## 2. Contexto

🟢 O contrato precisa ser Pydantic v2 e verificável, mas o runtime não pode executar código escrito pelo modelo (ADR 006). Formatos tabulares não têm aninhamento (Q35); decimais não podem perder precisão (Q37).

## 3. Goals

- 🟢 G-01: Nenhum texto do modelo vira código.
- 🟢 G-02: Mesma definição, mesmo código e mesma versão, byte a byte.
- 🟢 G-03: Código gerado aprovado por `mypy --strict`, `ruff check` e `ruff format --check` (Q36).

## 4. Non-Goals

- 🟢 NG-01: Sem validadores personalizados além das restrições declarativas e de `no_pipe`.
- 🟢 NG-02: Sem listas de objetos ou de listas em CSV.

## 5. Usuários

🟢 Agente do harness (rascunho), usuário (revisão), `sample`, `batch` e `quality` (`Record`, `formats`, `schema_version`).

## 6. Requisitos Funcionais

| ID | Requisito | Critério de aceite | Fonte |
|----|-----------|--------------------|-------|
| RF-01 | 🟢 Ler `intent.json` (formato, modo, estrutura definida) de forma tolerante | Intenção ausente ou sem formato = código 2 | `intent.py:28-48` |
| RF-02 | 🟢 Sem rascunho e com estrutura indefinida, usar o contrato padrão de 1 campo `descricao` (texto, "a definir") com aviso; sem rascunho e com estrutura definida = código 2 | — | `intent.py:51-54`, `service.py:97-113` |
| RF-03 | 🟢 Validar o meta-modelo (`format`, `kind`, `fields` ≥ 1, chaves desconhecidas recusadas); cada problema com o caminho (`fields[2].name`) | Código 6 com 1 linha por problema | `spec.py`, `service.py:67-70` |
| RF-04 | 🟢 Recusar formato diferente do da intenção | Código 6 | `service.py:114-117` |
| RF-05 | 🟢 Validação semântica: até 100 campos (itens de lista não contam); conversa só em JSON/JSONL; restrições só nos tipos permitidos; `list` exige `items`, `object` exige `fields`; `enum` com `choices` não vazias e sem repetidos; `ge`/`le` do tipo do campo e sem contradição; `min_length ≤ max_length`; `pattern` aceito pelo `re` e pelo validador do Pydantic; `casas_decimais` de 0 a 10 | Código 6 | `checks.py` |
| RF-06 | 🟢 Normalizar nomes por nível: NFKD → ASCII → snake_case; vazio → `campo`; começo com dígito → `campo_…`; reservados (palavras-chave, nomes do `BaseModel`, nomes do código gerado, prefixo `model_`) ganham `_`; repetidos ganham `_2`, `_3`; cada mudança gera aviso | `Nome Completo` → `nome_completo` | `names.py` |
| RF-07 | 🟢 CSV: objeto vira colunas `pai_filho` (opcional se o pai é opcional); lista de tipo simples vira 1 coluna com `|` e aviso; lista de objetos ou de listas e `choices` com `|` em lista são recusados; itens de texto ganham `no_pipe` | Código 6 na recusa (Q35) | `csvflat.py`, `validators.py` |
| RF-08 | 🟢 Versão = SHA-256 do JSON canônico (`sort_keys`, separadores compactos, sem nulos) | — | `version.py` |
| RF-09 | 🟢 Gerar `schema.py` com cabeçalho `# Gerado por sintetica.schema; não edite.` e `# schema_version: <sha>`; textos por `py_str` (escapa barra, aspas, controle, não imprimíveis); tipos auxiliares `…Choices`/`…Type` com nomes únicos; construções expandidas com vírgula final; linhas > 100 com `# noqa: E501` | Saída estável sob `ruff format` | `codegen.py` |
| RF-10 | 🟢 Tipos: `text→str`, `int→int`, `decimal→Decimal` (com `decimal_places`), `bool→bool`, `date`/`datetime`, `enum→Literal[...]`, `list→list[...]`, `object→` classe; opcional = `X | None` com `default=None`; `extra="forbid"` | — | `codegen.py:22-198` |
| RF-11 | 🟢 Conversa: `Record(messages: list[Message] (≥ 1), labels: Labels)`, `Message.role ∈ {system, user, assistant}`, `content` com ≥ 1 caractere | — | `codegen.py:200-234` |
| RF-12 | 🟢 Validar o código antes de gravar: gera `.schema.staged.py`, importa e exporta o JSON Schema; falha = traceback em `errors.log` e código 7 | Nada é gravado na falha | `service.py:143-153` |
| RF-13 | 🟢 Gravar `schema.json` (indentado), `schema.py`, `record.schema.json` e `schema.state.json`; mostrar tabela Markdown, avisos e diferenças (+ - ~) contra a versão anterior | — | `service.py:155-190`, `render.py` |
| RF-14 | 🟢 Revisão: versão nova sobre contrato existente soma 1 rodada; Guiado fica `em_revisao`; Expresso já sai `aprovado`; mesma versão mantém o estado; a partir de 5 rodadas sugere reiniciar a entrevista | — | `state.py:67-82` |
| RF-15 | 🟢 `schema approve` exige `schema.py` com a versão do `schema.json` (senão código 7) e grava `aprovado` com `approved_at` | — | `service.py:207-225` |
| RF-16 | 🟢 `load_record_model(dataset)` regera `schema.py` se o cabeçalho não bate com o `schema.json` e importa com nome de módulo único, sem `__pycache__` | — | `loader.py:43-90` |
| RF-17 | 🟢 Serialização: `to_json_obj`; `to_json_text(obj, indent=None)` com decimal como número exato (marcador com nonce); `to_jsonl_line`; `to_csv_row` (decimais com casas fixas, listas com `|`, `true`/`false`, ISO 8601); `csv_columns` na ordem do contrato | `{"valor":19.90}`; CSV `19.90` (Q37) | `formats.py` |

## 7. Requisitos Não-Funcionais

| ID | Requisito | Evidência |
|----|-----------|-----------|
| RNF-01 | 🟢 Determinismo do gerador | `codegen.py:262-276`, testes de igualdade byte a byte |
| RNF-02 | 🟢 Código gerado passa por `mypy --strict` e `ruff` | `tests/schema/test_codegen_static.py` (Q36) |
| RNF-03 | 🟢 Escrita atômica | `state.py:19-28` |

## 8. Interface

```
uv run sintetica schema build <slug>
uv run sintetica schema show <slug>
uv run sintetica schema approve <slug>
```

| Código | Significado |
|--------|-------------|
| 0 | Sucesso |
| 2 | Dataset, intenção ou rascunho ausente; `schema.json` ausente no `show`/`approve` |
| 6 | Definição inválida |
| 7 | Código gerado inválido ou `schema.py` desatualizado |

## 9. Modelo de Dados

🟢 `SchemaSpecModel`, `FieldSpecModel`, `Constraints`, `SchemaIssue`, `SchemaState`; arquivos `schema.draft.json`, `schema.json`, `schema.py`, `record.schema.json`, `schema.state.json`, `errors.log`. Detalhe em `data-dictionary.md#módulo-schema`.

## 10. Integrações

🟢 Pydantic v2 (meta-modelo, `TypeAdapter` para `pattern`, `Record` gerado). Consumidores: `sample`, `batch`, `quality`.

## 11. Edge Cases

| Cenário | Comportamento |
|---------|---------------|
| 🟢 Texto da definição com aspas, barras ou caracteres de controle | Escapado por `py_str`; nunca vira código |
| 🟢 Nome igual a palavra reservada | Sufixo `_` (`class_`) com aviso |
| 🟢 `pattern` com lookahead | Recusado (o validador do Pydantic não aceita) |
| 🟢 `schema.py` editado à mão | Regerado na próxima carga se a versão não bater |
| 🟢 Lista de objetos em CSV | Código 6 sugerindo JSON ou JSONL |

## 12. Segurança

- 🟢 Nenhum texto da definição é interpolado como código; nomes chegam normalizados (identificadores ASCII).

## 13. Decisões (consolidadas)

| Decisão | Fonte |
|---------|-------|
| 🟢 Contrato declarativo e código gerado | ADR 006 |
| 🟢 Listas CSV com `|`; decimal exato | Q35, Q37, ADR 007 |
| 🟢 `mypy --strict` no código gerado | Q36 |
| 🟢 `to_json_text` com `indent` opcional (feature 005) | Adendo 005 |

## 14. Lacunas

- 🟡 `schema build` não confere `confirmed_at` da intenção (`intent.py` próprio, sem `IntentModel`). Decisão (Q56): validar `confirmed_at` no `build` e orientar a confirmação prévia no modo Guiado. Correção pendente.
- 🟡 `write_atomic` local duplica `sintetica.fsutil.write_atomic`.

## Histórico

| Versão | Data | Mudança |
|--------|------|---------|
| 1.0 | 2026-10-09 | Spec planejada (`_planejado/`) |
| 2.0 | 2026-10-12 | Reescrita conforme o código; adendos 003 e 005 consolidados |
