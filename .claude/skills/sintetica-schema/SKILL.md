---
name: sintetica-schema
description: Traduz a intenção confirmada do sintetica num contrato de dados (Pydantic v2) e conduz a revisão com o usuário. Use depois da sintetica-start, quando o resumo indicar o comando schema build.
---

# sintetica-schema: contrato de dados

Você escreve um rascunho declarativo do contrato. O runtime valida o rascunho e gera o código de validação; nenhum código escrito por você é executado. Rode os comandos na raiz do projeto, pelo lançador `.sintetica/bin/sintetica`.

## Passos

1. Leia `datasets/<slug>/intent.json` e grave `datasets/<slug>/schema.draft.json`:
   ```json
   {
     "format": "csv | json | jsonl",
     "kind": "records | conversation",
     "fields": [
       {"name": "valor", "type": "decimal", "required": true, "description": "preço em reais",
        "constraints": {"ge": 5, "le": 50, "casas_decimais": 2}}
     ]
   }
   ```
   - Tipos: `text`, `int`, `decimal`, `bool`, `date`, `datetime`, `enum`, `list` (com `items`), `object` (com `fields`).
   - Restrições: `ge`/`le` (números e datas), `min_length`/`max_length` (texto e listas), `pattern` (texto, sem lookahead nem lookbehind), `choices` (enum), `casas_decimais` (decimal, 0 a 10).
   - O `format` precisa ser o mesmo da intenção. Conversas: `kind: "conversation"`; os campos são os rótulos.
   - CSV: listas de objetos não cabem; use JSON ou JSONL.
2. Gere e mostre a tabela do contrato ao usuário:
   ```bash
   .sintetica/bin/sintetica schema build <slug>
   ```
   - Código 6: corrija o rascunho pelas linhas `caminho: mensagem` e rode de novo.
3. Para ajustar, reescreva o rascunho e rode `schema build` de novo. A saída mostra as diferenças.
4. Com o "sim" do usuário, aprove:
   ```bash
   .sintetica/bin/sintetica schema approve <slug>
   ```
   No modo Expresso, o `build` já aprova.
5. Para rever: `.sintetica/bin/sintetica schema show <slug>`. Depois siga com a skill `sintetica-sample`.

## Códigos de saída

| Código | Significado |
|--------|-------------|
| 0 | Sucesso |
| 2 | Dataset, intenção ou rascunho ausente |
| 6 | Definição inválida |
| 7 | Código gerado inválido (detalhes em `errors.log`) ou `schema.py` desatualizado |
