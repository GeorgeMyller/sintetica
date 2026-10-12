# schema-builder

Contrato de dados de cada dataset do sintetica. O agente do harness escreve um rascunho declarativo; o comando `sintetica schema build` valida o rascunho e gera o código de validação. O runtime nunca executa código escrito pelo modelo.

> No projeto do usuário, instalado por `npx sintetica install`, os comandos rodam pelo lançador `.sintetica/bin/sintetica` no lugar de `uv run sintetica` (`docs/cli-installer.md`).

## Fluxo

1. O `intent-interview` grava `datasets/<slug>/intent.json`.
2. O agente grava `datasets/<slug>/schema.draft.json` a partir da intenção.
3. `uv run sintetica schema build <slug>` gera:
   - `schema.json`: definição canônica, com nomes normalizados (e plana, em CSV);
   - `schema.py`: classe `Record` (Pydantic v2), com a versão no cabeçalho;
   - `record.schema.json`: JSON Schema de `Record`, aceito por `sintetica request --schema`;
   - `schema.state.json`: status, rodadas de ajuste e versão.
4. O usuário revisa a tabela. Ajuste: o agente reescreve o rascunho e roda `build` de novo; a saída mostra as diferenças.
5. `uv run sintetica schema approve <slug>`. No modo Expresso, o `build` já aprova.

## Formato do rascunho (para a skill `sintetica-schema`)

```json
{
  "format": "csv | json | jsonl",
  "kind": "records | conversation",
  "fields": [
    {
      "name": "idade",
      "type": "text | int | decimal | bool | date | datetime | enum | list | object",
      "required": true,
      "description": "idade do cliente",
      "constraints": {
        "ge": 18, "le": 90,
        "min_length": 1, "max_length": 50,
        "pattern": "^[A-Z]+$",
        "choices": ["SP", "RJ"],
        "casas_decimais": 2
      },
      "items": { "type": "text" },
      "fields": [ { "name": "cidade", "type": "text" } ]
    }
  ]
}
```

| Restrição | Tipos |
|-----------|-------|
| `ge`, `le` | `int`, `decimal` (número), `date`, `datetime` (texto ISO 8601) |
| `min_length`, `max_length` | `text` (caracteres), `list` (itens) |
| `pattern` | `text`; precisa ser aceito pelo `re` do Python e pelo validador do Pydantic (sem lookbehind ou lookahead) |
| `choices` | `enum` (obrigatório, sem repetidos) |
| `casas_decimais` | `decimal` (0 a 10) |

- `items` é obrigatório em `list`; `fields` é obrigatório em `object`.
- `kind: "conversation"` (JSON ou JSONL): os campos são os rótulos. O `Record` fica com `messages` (papel `system`, `user` ou `assistant`, conteúdo não vazio, mínimo 1) e `labels`.
- Limite: 100 campos, contando os aninhados.
- Nomes viram snake_case ASCII; palavras reservadas ganham `_` (`class_`); repetidos ganham `_2`.

## Regras de CSV

- Objeto aninhado vira colunas com prefixo: `endereco.cidade` → `endereco_cidade`. Se o objeto for opcional, as colunas também são.
- Lista de valores simples vira 1 coluna com os itens separados por `|`. Itens de texto não podem conter `|`.
- Lista de objetos ou de listas é recusada: use JSON ou JSONL.

## Códigos de saída

| Código | Significado |
|--------|-------------|
| 0 | Sucesso |
| 2 | Dataset, intenção ou rascunho ausente |
| 6 | Definição inválida (1 problema por linha: `caminho: mensagem`) |
| 7 | Código gerado inválido (detalhes em `errors.log`) ou `schema.py` desatualizado |

## API para os próximos componentes

```python
from sintetica.schema import load_record_model, to_csv_row, to_jsonl_line, csv_columns

Record = load_record_model(Path("datasets/pedidos"))  # confere a versão; gera de novo se preciso
record = Record.model_validate(obj)                  # ValidationError se não conforme
to_jsonl_line(record)  # decimal como número exato: {"preco":19.90}
to_csv_row(record)     # {"preco": "19.90", "tags": "a|b", "pago": "false"}
csv_columns(Record)    # colunas na ordem da definição
```

## Garantias

- O gerador é determinístico: a mesma definição gera o mesmo `schema.py`, byte a byte.
- Todo texto da definição entra no código como literal escapado.
- A suíte de testes roda `mypy --strict`, `ruff check` e `ruff format --check` sobre o código gerado de cada definição de teste (`pytest -m codegen`).
