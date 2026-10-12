# Roadmap: schema-builder (contrato de dados do dataset)

> Identificador: `003-schema-builder`
> Data: `2026-10-12`
> Requirements: `_reversa_forward/003-schema-builder/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA
> Cenário: greenfield. Não há `architecture.md`, `c4-context.md`, `state-machines.md`, `dependencies.md` nem `code-analysis.md`. Adendos vigentes lidos: `addenda/001-pii-guard.md` e `addenda/002-llm-provider.md`.

## 1. Resumo da abordagem

🟡 A feature cria o pacote `sintetica.schema` e o subcomando `sintetica schema`, e adiciona Pydantic v2 como dependência de runtime.
🟡 O fluxo é o mesmo padrão do protocolo do harness (Q29): o agente escreve um rascunho declarativo `datasets/<slug>/schema.draft.json`; o comando `sintetica schema build <slug>` valida o rascunho, normaliza nomes, aplica as regras de CSV, grava a definição canônica `schema.json`, gera `schema.py` por um gerador determinístico, valida o código por importação e exporta `record.schema.json`.
🟡 O gerador nunca interpola texto da definição como código: todo texto entra por `repr()` (RN-02). O cabeçalho do `schema.py` traz a versão; o carregador recusa um `schema.py` cuja versão não bate com a de `schema.json`.
🟡 A serialização para JSON, JSONL e CSV (decimal como número ou texto com casas fixas, listas com `|`) fica em `sintetica.schema.formats`, para o `batch-generator` reutilizar.
🟡 Um arquivo de estado `schema.state.json` guarda status (`em_revisao` ou `aprovado`), rodadas de ajuste e versão. O modo Expresso aprova sem pergunta.
🟡 A verificação estrita de tipos e o lint do código gerado rodam na suíte de testes (Q36), sobre um conjunto de definições que cobre os 9 tipos, as 7 restrições, conversa, CSV e textos hostis.

## 2. Princípios aplicados

🟡 `.reversa/principles.md` não existe. Sem princípios formais para verificar.

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| n/a | Arquivo de princípios ausente | n/a |

🟡 Restrições do PRD tratadas como princípios de fato: operação local (Q15), tipagem estrita (PRD, seção 6), cobertura ≥ 80% (Q19), falha segura herdada do `pii-guard`. Todas são respeitadas.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Adicionar `pydantic>=2.7` às dependências de runtime e o plugin `pydantic.mypy` à configuração do `mypy` | PRD exige Pydantic v2 para os contratos; o plugin dá tipagem estrita aos modelos gerados | Dataclasses com validação própria | 🟢 |
| D-02 | Novo pacote `sintetica.schema`, separado de `sintetica.providers` e `sintetica.pii` | Mesma organização por componente das features 001 e 002 | Módulo dentro de `providers` | 🟡 |
| D-03 | Protocolo por arquivo: o agente grava `schema.draft.json`; `sintetica schema build` consome o rascunho e grava os artefatos canônicos | Mesmo padrão aprovado na Q29; o runtime não chama o agente | Agente grava `schema.json` direto | 🟡 |
| D-04 | Meta-modelo da definição em Pydantic (`SchemaSpecModel`, `FieldSpecModel`), com `extra="forbid"`; erros convertidos para `SchemaIssue(path, message)` | Pydantic devolve todos os erros com o caminho (RF-02) | Validação manual campo a campo | 🟡 |
| D-05 | Validação semântica em 2ª etapa: restrição incompatível com o tipo, contradições (mínimo > máximo), regex que não compila, enum sem valores, lista sem `items`, objeto sem `fields`, limite de 100 campos contando aninhados | RF-09, RF-10, RF-11; Pydantic sozinho não cobre regras entre atributos | Tudo em validadores Pydantic | 🟡 |
| D-06 | Normalização de nomes: NFKD → ASCII, minúsculas, não alfanumérico → `_`, `_` repetido colapsado, sem `_` nas pontas, dígito inicial → prefixo `campo_`, vazio → `campo`; sufixo `_` para `keyword.kwlist`, `keyword.softkwlist`, atributos de `BaseModel` e nomes iniciados em `model_`; repetidos → `_2`, `_3` | RN-03; nomes iniciados em `model_` conflitam com o espaço protegido do Pydantic | Recusar nomes inválidos | 🟡 |
| D-07 | Campo `kind` na definição: `records` (padrão) ou `conversation`. Em `conversation`, os campos da definição são os rótulos; o gerador cria `Message` (papel `Literal["system","user","assistant"]`, conteúdo com tamanho mínimo 1), `Labels` e `Record(messages: list[Message] com mínimo 1, labels: Labels)` | RF-06; a spec não dizia como marcar o formato conversacional | Detectar pelo formato JSONL | 🟡 |
| D-08 | Transformação CSV no nível da definição, antes da geração: objetos viram campos com prefixo; lista simples continua `list` com item restrito a não conter `|`; lista de objetos gera erro | RN-04, Q35; o `Record` de CSV fica plano e valida exatamente o que vira coluna | Achatar só na escrita do CSV | 🟢 |
| D-09 | Mapeamento de tipos: `text→str`, `int→int`, `decimal→Decimal`, `bool→bool`, `date→datetime.date`, `datetime→datetime.datetime`, `enum→Literal[...]`, `list→list[...]`, `object→` classe aninhada com nome PascalCase do caminho e sufixo numérico em colisão | RF-03 | `Enum` do Python para enums (mais código, mesmo efeito) | 🟡 |
| D-10 | Restrições via `Annotated[T, Field(...)]`: `ge`, `le`, `min_length`, `max_length`, `pattern`, `decimal_places` (`casas_decimais`), `description`; campo não obrigatório vira `T | None = None`; todos os modelos com `ConfigDict(extra="forbid")` | RF-04, RN-09; `extra="forbid"` mede conformidade de verdade | Validação estrita de tipo (`strict=True`), que recusaria `"19.9"` para decimal | 🟡 |
| D-11 | Gerador por montagem de linhas com ordem fixa e todo texto via `repr()`; cabeçalho `# Gerado por sintetica.schema; não edite.` e `# schema_version: <hash>`; saída já no estilo do `ruff format` | RF-05, RN-02 | Templates Jinja (dependência extra); `ast.unparse` (formatação diferente entre versões do Python) | 🟡 |
| D-12 | Versão = SHA-256 do JSON canônico de `schema.json` (`sort_keys`, separadores compactos, `ensure_ascii=False`) | RN-05 | Hash do arquivo bruto | 🟢 |
| D-13 | Carregador: confere a versão do cabeçalho de `schema.py` contra `schema.json`; com divergência, gera de novo antes de importar; importa por `importlib.util.spec_from_file_location` com nome de módulo único por versão | Evita executar um `schema.py` editado à mão ou desatualizado | Importar sempre | 🟡 |
| D-14 | Validação do código no runtime (Q36): importar, conferir `Record` subclasse de `BaseModel`, chamar `model_json_schema()`; falha grava `errors.log` com data, versão e traceback, e nada é mostrado | RF-12 | Rodar `mypy` no runtime | 🟢 |
| D-15 | `formats.py`: `to_json_obj(record)` com decimal como número exato (`Decimal` → literal numérico) e `to_csv_row(record)` com decimal em texto com as casas definidas e listas unidas por `|` | RF-19, Q37 | Serializador padrão do Pydantic (decimal sai como texto no JSON) | 🟢 |
| D-16 | Estado em `schema.state.json`: `status`, `rounds`, `schema_version`, `approved_at`; cada `build` com versão nova sobre um estado `em_revisao` soma 1 rodada; na 5ª, a saída sugere `/sintetica-start` | RF-16, RF-17 | Contar rodadas no agente | 🟡 |
| D-17 | Estrutura indefinida sem rascunho: `build` gera a definição padrão de 1 campo `descricao` (texto, obrigatório, "a definir") e avisa | RN-07, RF-18 | Exigir rascunho sempre | 🟡 |
| D-18 | Leitor de `intent.json` tolerante: exige `slug`, `mode`, `format` e `structure.status`; ignora campos extras | O `intent-interview` ainda não existe; o formato vem da spec dele | Modelo estrito com todos os campos | 🟡 |
| D-19 | Subcomando `sintetica schema` com `build`, `show` e `approve`, códigos de saída 0 (sucesso), 2 (dataset ou intenção ausente), 6 (definição inválida), 7 (código gerado inválido); 3, 4 e 5 continuam reservados ao protocolo do harness | Mesma CLI da feature 002 (D-22 da 002), sem colisão de códigos | Novo executável | 🟡 |
| D-20 | Suíte de verificação do gerador: cada definição de teste gera `schema.py` em pasta temporária e roda `mypy --strict` e `ruff check`/`ruff format --check` por subprocesso, marcada `codegen` e incluída na suíte padrão | RF-20, Q36 | Verificar só 1 schema exemplo | 🟢 |

> 🟢 nas decisões confirmadas por respostas do revisor (Q35, Q36, Q37) ou pelo PRD (Pydantic v2).

## 4. Premissas

🟡 Nenhuma premissa vinda de `[DÚVIDA]`: o `requirements.md` está com 0 marcadores após o clarify.

| Premissa | Origem (`requirements.md` seção) | Risco se errada |
|----------|----------------------------------|-----------------|
| O `intent-interview` vai gravar `intent.json` no formato da spec dele (seção 9) | 2. Contexto | O leitor tolerante (D-18) isola a mudança; ajuste pequeno |
| O agente consegue produzir `schema.draft.json` válido na maior parte das vezes, guiado pela mensagem de erro com caminho | 4. RN-01 | Mais rodadas; o limite de 5 (RN-06) contém o custo |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `sintetica.schema` | `_reversa_sdd/sdd/schema-builder.md` | componente-novo | Validação, normalização, CSV, gerador, carregador, formatos, estado, tabela e diferenças |
| `sintetica.cli` | `_reversa_sdd/addenda/002-llm-provider.md` (comando `sintetica`) | contrato-alterado | Novo subcomando `schema` (`build`, `show`, `approve`); `request` e `submit` inalterados |
| `pyproject.toml` | `_reversa_sdd/prd.md#6. Restrições` | regra-alterada | Dependência `pydantic`, plugin `pydantic.mypy`, marcador `codegen` |

Estrutura de arquivos prevista:

```
src/sintetica/schema/__init__.py     # API pública
src/sintetica/schema/spec.py         # SchemaSpecModel, FieldSpecModel, SchemaIssue, parse
src/sintetica/schema/checks.py       # validação semântica (D-05)
src/sintetica/schema/names.py        # normalização de nomes (D-06)
src/sintetica/schema/csvflat.py      # transformação CSV (D-08)
src/sintetica/schema/codegen.py      # gerador determinístico (D-09 a D-11)
src/sintetica/schema/version.py      # versão canônica (D-12)
src/sintetica/schema/loader.py       # carregador e validação no runtime (D-13, D-14)
src/sintetica/schema/formats.py      # serialização JSON/JSONL/CSV (D-15)
src/sintetica/schema/render.py       # tabela Markdown e diferenças
src/sintetica/schema/state.py        # schema.state.json (D-16)
src/sintetica/schema/intent.py       # leitor de intent.json (D-18)
src/sintetica/schema/service.py      # orquestra build, show, approve
src/sintetica/cli.py                 # subcomando schema (alterado)
tests/schema/…                       # testes por módulo + verificação do código gerado (D-20)
tests/fixtures/schema/*.json         # definições de teste
docs/schema-builder.md
```

## 6. Delta no modelo de dados

- Resumo das mudanças: 🟡 6 arquivos novos por dataset (`schema.draft.json`, `schema.json`, `schema.py`, `record.schema.json`, `schema.state.json`, `errors.log`), definição com o campo novo `kind` e a restrição nova `casas_decimais`.
- Detalhe completo em: `_reversa_forward/003-schema-builder/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| `sintetica schema build | show | approve` | arquivo + CLI | `_reversa_forward/003-schema-builder/interfaces/schema-cli.md` |

🟡 Contrato interno para os próximos componentes:

```
from sintetica.schema import load_record_model, to_json_obj, to_csv_row, csv_columns
Record = load_record_model(dataset_dir)          # valida versão e importa
record = Record.model_validate(obj)              # ValidationError se não conforme
to_json_obj(record) -> dict                      # decimal como número
to_csv_row(record) -> dict[str, str]             # decimal com casas fixas, listas com "|"
csv_columns(dataset_dir) -> list[str]            # ordem da definição
```

## 8. Plano de migração

n/a. Os arquivos são novos. A alteração em `sintetica.cli` só acrescenta o subcomando `schema`.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| R-01: Texto da definição escapa para código e executa no processo do usuário | alto | baixo | `repr()` em todo texto (D-11); teste com aspas, quebra de linha e `import os` (cenário Gherkin) |
| R-02: `schema.py` editado à mão ou desatualizado é importado | médio | médio | Conferência de versão antes de importar (D-13) |
| R-03: Código gerado deixa de passar em `mypy --strict` após mudança no gerador | médio | médio | Suíte `codegen` na suíte padrão (D-20) |
| R-04: Decimal em JSON perde precisão ao virar `float` | médio | médio | Serializador próprio que emite o literal do `Decimal` (D-15) |
| R-05: Formato de `intent.json` muda quando o `intent-interview` for implementado | baixo | médio | Leitor tolerante (D-18) |
| R-06: Suíte `codegen` lenta (subprocesso por definição) | baixo | médio | Uma única chamada de `mypy` e de `ruff` sobre a pasta com todos os `schema.py` de teste |
| R-07: Pydantic novo aumenta o tempo de importação do comando `sintetica` | baixo | baixo | Importação tardia de `sintetica.schema` só no subcomando `schema` |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Re-extração reversa executada e sem regressão vermelha (recomendado, não obrigatório)
- [ ] `mypy --strict` e `ruff` sem erros no projeto
- [ ] Cobertura ≥ 80% em `sintetica.schema`
- [ ] Os 22 cenários Gherkin do `requirements.md` cobertos por testes
- [ ] Suíte `codegen`: todos os `schema.py` de teste passam em `mypy --strict`, `ruff check` e `ruff format --check`
- [ ] Os 205 testes das features 001 e 002 continuam passando

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-12 | Versão inicial gerada por `/reversa-plan` | reversa |
