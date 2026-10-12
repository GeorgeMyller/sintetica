# Data Delta: schema-builder

> Identificador: `003-schema-builder`
> Data: `2026-10-12`
> Base: `_reversa_sdd/sdd/schema-builder.md#9. Modelo de Dados`. Não há modelo extraído de legado (greenfield).

## 1. Definição (`schema.draft.json` e `schema.json`)

```
SchemaSpec {
  model_name: "Record"                  // fixo
  format: "csv" | "json" | "jsonl"
  kind: "records" | "conversation"      // NOVO (D-07); padrão "records"
  fields: list<FieldSpec>               // 1 a 100, contando aninhados
}

FieldSpec {
  name: string                          // normalizado em schema.json (D-06)
  type: "text" | "int" | "decimal" | "bool" | "date" | "datetime" | "enum" | "list" | "object"
  required: boolean                     // padrão true
  description: string                   // padrão ""
  constraints: {
    ge?: number, le?: number,           // int, decimal, date, datetime
    min_length?: int, max_length?: int, // text, list
    pattern?: string,                   // text
    choices?: list<string>,             // enum (obrigatório, ≥ 1, sem repetidos)
    casas_decimais?: int                // NOVO (Q37); decimal; 0 a 10
  }
  items?: FieldSpec                     // obrigatório para "list"
  fields?: list<FieldSpec>              // obrigatório para "object"
}
```

🟡 Diferenças em relação à spec:
- `schema_version` sai da definição e vai para `schema.state.json` e para o cabeçalho de `schema.py`. Dentro do arquivo, o hash mudaria o próprio hash.
- `kind` e `casas_decimais` são novos.
- Em CSV, `schema.json` guarda a definição já transformada (plana, D-08). O rascunho guarda a forma original.

## 2. Arquivos por dataset

| Arquivo | Quem grava | Conteúdo |
|---------|------------|----------|
| `datasets/<slug>/schema.draft.json` | Agente do harness | Rascunho da definição |
| `datasets/<slug>/schema.json` | `sintetica schema build` | Definição canônica, normalizada |
| `datasets/<slug>/schema.py` | `sintetica schema build` | Código gerado, classe `Record`, cabeçalho com versão |
| `datasets/<slug>/record.schema.json` | `sintetica schema build` | JSON Schema de `Record`, aceito por `sintetica request --schema` |
| `datasets/<slug>/schema.state.json` | `build` e `approve` | Estado da revisão |
| `datasets/<slug>/errors.log` | `build`, só em falha | Acréscimo: data, versão, mensagem, traceback |

```
SchemaState {
  status: "em_revisao" | "aprovado"
  rounds: int                           // ajustes com versão nova enquanto em revisão
  schema_version: string                // SHA-256 do JSON canônico de schema.json
  approved_at: string | null            // ISO 8601 UTC
  warnings: list<string>                // avisos da última geração (CSV, estrutura indefinida, nomes)
}
```

## 3. Entrada lida

`datasets/<slug>/intent.json` (gravado pelo `intent-interview`, feature futura). Campos usados: `slug`, `mode`, `format`, `structure.status`. Campos extras são ignorados (D-18).

## 4. Migrações necessárias

Nenhuma. Arquivos novos.
