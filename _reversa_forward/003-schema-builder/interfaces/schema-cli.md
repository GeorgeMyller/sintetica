# Interface: `sintetica schema` (contrato de dados do dataset)

> Tipo: arquivo + CLI. Origem: RN-01, RF-01 a RF-20, D-03, D-19. Confidência: 🟡.

## 1. `sintetica schema build`

```
uv run sintetica schema build <slug> [--project-dir <dir>]
```

| Situação | Resultado | Código de saída |
|----------|-----------|-----------------|
| `datasets/<slug>/` ou `intent.json` ausente | Erro que cita `/sintetica-start`; nada gravado | 2 |
| Sem `schema.draft.json` e estrutura `definido` | Erro: o agente precisa gravar o rascunho | 2 |
| Sem `schema.draft.json` e estrutura `indefinido` | Usa a definição padrão de 1 campo `descricao` e avisa (RN-07) | 0 |
| Rascunho com erros estruturais ou semânticos | Lista todos os erros, 1 por linha: `<caminho>: <mensagem>`; nada gravado | 6 |
| Código gerado não importa, sem `Record` ou sem JSON Schema | Grava `errors.log`; nada mostrado; artefatos anteriores preservados | 7 |
| Sucesso | Grava `schema.json`, `schema.py`, `record.schema.json`, `schema.state.json`; mostra avisos, tabela, diferenças e versão | 0 |

Saída padrão em sucesso:

```
Contrato do dataset <slug>: versão <hash12>, <N> campos, status <em_revisao|aprovado>
Avisos:
  - <aviso>
| campo | tipo | obrigatório | restrições | descrição |
|-------|------|-------------|------------|-----------|
| ...   | ...  | ...         | ...        | ...       |
Diferenças em relação à versão <hash12 anterior>: +<novos> -<removidos> ~<alterados>
  + <caminho>
  - <caminho>
  ~ <caminho>: <atributo> <antes> → <depois>
Rodada de ajuste <k> de 5.
Para aprovar: uv run sintetica schema approve <slug>
```

- 🟡 Modo Expresso (`intent.json#mode = "expresso"`): o status já sai `aprovado` e a linha "Para aprovar" não aparece.
- 🟡 Na 5ª rodada sem aprovação, a saída inclui: "5 rodadas sem aprovação. Considere reiniciar a entrevista com /sintetica-start."
- 🟡 Escrita atômica de cada arquivo (temporário + `os.replace`).

## 2. `sintetica schema show`

```
uv run sintetica schema show <slug> [--project-dir <dir>]
```

Mostra a tabela, a versão e o status do `schema.json` atual. Sem `schema.json`: erro, código 2.

## 3. `sintetica schema approve`

```
uv run sintetica schema approve <slug> [--project-dir <dir>]
```

| Situação | Resultado | Código de saída |
|----------|-----------|-----------------|
| Sem `schema.json` | Erro | 2 |
| `schema.py` desatualizado em relação a `schema.json` | Erro: rode `build` | 7 |
| Sucesso | `status = aprovado`, `approved_at` preenchido | 0 |

## 4. Códigos de saída do comando `sintetica`

| Código | Significado | Origem |
|--------|-------------|--------|
| 0 | Sucesso | 002, 003 |
| 2 | Dataset, intenção ou argumento inválido | 002, 003 |
| 3 | Limite do harness | 002 |
| 4 | Pedido inexistente | 002 |
| 5 | Resposta inválida | 002 |
| 6 | Definição de schema inválida | 003 |
| 7 | Código de schema gerado inválido ou desatualizado | 003 |

## 5. Segurança

- 🟡 O comando nunca executa o rascunho. Só executa `schema.py` produzido pelo próprio gerador, com versão conferida (D-13).
- 🟡 Os arquivos ficam em `datasets/`, que está no `.gitignore`.
