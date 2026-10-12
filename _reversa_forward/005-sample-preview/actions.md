# Actions: sample-preview (amostra de 3 a 5 registros para aprovação)

> Identificador: `005-sample-preview`
> Data: `2026-10-12`
> Roadmap: `_reversa_forward/005-sample-preview/roadmap.md`
> Fontes auxiliares: `data-delta.md`, `interfaces/sample-cli.md`, `requirements.md` (16 cenários Gherkin).

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 18 |
| Paralelizáveis (`[//]`) | 13 |
| Maior cadeia de dependência | 6 (T001 → T009 → T013 → T014 → T015 → T017) |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Criar o pacote `sintetica.sample` com `__init__.py` mínimo e a pasta `tests/sample/` | - | `[//]` | `src/sintetica/sample/__init__.py` | 🟡 | `[X]` |
| T002 | Acrescentar o parâmetro opcional `indent: int | None = None` a `to_json_text`, preservando a saída atual quando `None` (D-11) | - | `[//]` | `src/sintetica/schema/formats.py` | 🟡 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Criar os auxiliares de teste: projeto com intenção confirmada e contrato aprovado (JSON, CSV e Expresso), e função que faz o papel do agente lendo o pedido pendente e enviando JSONL pelo `sintetica submit` real | T001 | `[//]` | `tests/sample/conftest.py` | 🟡 | `[X]` |
| T004 | Escrever testes da revisão: válidos, inválidos com 1º erro e sem o valor, duplicados contra aceitos e no mesmo lote, mascaramento e revalidação que reprova o registro quando o valor falso quebra o `pattern` (D-07, D-08) | T003 | `[//]` | `tests/sample/test_review.py` | 🟡 | `[X]` |
| T005 | Escrever testes do pedido: instruções com objetivo, estrutura e regras definidos, ajuste, "tentativa k de 3", aceitos como sementes, e ids diferentes entre tentativas com o mesmo número de faltantes (D-03, R-01) | T003 | `[//]` | `tests/sample/test_request.py` | 🟢 | `[X]` |
| T006 | Escrever testes da exibição: tabela CSV com `|` escapado e decimais com casas fixas; blocos JSON formatados com decimal exato (D-10) | T003 | `[//]` | `tests/sample/test_render.py` | 🟡 | `[X]` |
| T007 | Escrever os testes de ponta a ponta dos 16 cenários Gherkin com o protocolo real do harness, os códigos 0, 2, 9, 10, 11, 12 e 13, e a busca do CPF original em todos os arquivos e saídas | T003 | `[//]` | `tests/sample/test_cli.py` | 🟡 | `[X]` |
| T008 | Acrescentar testes de `to_json_text(indent=2)` e de saída idêntica com `indent=None` (R-05) | T002 | `[//]` | `tests/schema/test_formats.py` | 🟡 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T009 | Implementar `SampleState` e `SampleMeta` (Pydantic), leitura, gravação atômica com `sintetica.fsutil.write_atomic` e os 4 estados (data-delta.md#1 e #2) | T001 | `[//]` | `src/sintetica/sample/state.py` | 🟡 | `[X]` |
| T010 | Implementar `build_request(intent, schema_json, accepted, k, attempt, adjustment)` com as instruções de D-03 | T001 | `[//]` | `src/sintetica/sample/request.py` | 🟢 | `[X]` |
| T011 | Implementar `review_records(raw, Record, accepted, masker)`: validação, descarte de duplicados pelo JSON canônico, mascaramento de cada texto com o caminho do campo e revalidação (D-07, D-08) | T001 | `[//]` | `src/sintetica/sample/review.py` | 🟡 | `[X]` |
| T012 | Implementar a exibição: tabela Markdown (CSV) com `csv_columns` e `to_csv_row`; blocos ```json com `to_json_text(..., indent=2)` (D-10) | T001, T002 | `[//]` | `src/sintetica/sample/render.py` | 🟡 | `[X]` |
| T013 | Implementar `run`: pré-condições do contrato e reinício por versão nova (D-02, D-15), N de 3 a 5 com padrão 3, pedido por `build_provider(..., harness_available=True)` com `asyncio.run`, `HarnessResponsePending` → `aguardando_agente` (D-05), `ProviderError` → 12 (D-06), revisão e próximo pedido até 3 tentativas, estados finais do Guiado e do Expresso (D-09) | T009, T010, T011, T012 | - | `src/sintetica/sample/service.py` | 🟡 | `[X]` |
| T014 | Implementar `approve` (D-13), aprovação automática do Expresso com N válidos (D-14), `adjust` com mascaramento e sugestão a partir da 4ª rodada (D-12) e `show` | T013 | - | `src/sintetica/sample/service.py` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T015 | Acrescentar o subcomando `sample` (`run --n`, `adjust`, `approve`, `show`) ao `sintetica`, com importação tardia e os códigos 11, 12 e 13; demais subcomandos inalterados (D-16) | T014 | - | `src/sintetica/cli.py` | 🟡 | `[X]` |
| T016 | Expor a API pública de `sintetica.sample`: `run`, `adjust`, `approve`, `show`, `SampleState`, `SampleMeta`, `load_sample_state`, com `__all__` | T014 | - | `src/sintetica/sample/__init__.py` | 🟡 | `[X]` |
| T017 | Completar os testes até cobertura ≥ 80% em `sintetica.sample`, com os 16 cenários Gherkin cobertos, os 381 testes anteriores passando e `mypy --strict` e `ruff` sem erros (critério de pronto) | T015, T016, T004, T005, T006, T007, T008 | - | `tests/sample/` | 🟡 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T018 | Escrever a documentação curta: fluxo da skill `sintetica-sample` (run, submit, run de novo), opções aprovar/ajustar/voltar ao contrato, amostra parcial, arquivos de semente e códigos de saída | T016 | `[//]` | `docs/sample-preview.md` | 🟡 | `[X]` |

## Notas de execução

<!--
Reservado para /reversa-coding registrar avisos ou observações que surgiram durante a execução.
Não use isso para corrigir ações, edits manuais ficam fora desse arquivo, vão direto no código.
-->

- O `SKILL.md` da skill `sintetica-sample` fica fora desta feature, como nas features 003 e 004; a T018 documenta o que a skill precisa instruir ao agente.
- A T002 e a T008 alteram arquivos entregues na feature 003 (`formats.py` e `test_formats.py`), só por acréscimo.
- 2026-10-12, T013: o teste de fumaça mostrou que a resposta bruta do agente (`requests/<id>.response.jsonl`, gravada pelo `sintetica submit` da feature 002) mantinha o CPF original. Decisão nova (fora do roadmap): depois de ler a resposta, a amostra apaga esse arquivo; só a versão mascarada fica no disco (RN-05). É seguro porque cada tentativa gera um pedido com id próprio (D-03).
- 2026-10-12, T013: `build_provider` levanta `ProviderUnavailable` já na escolha do provedor; a chamada estava fora do tratamento de erro e geraria traceback. Corrigido para o código 12, com teste.
- 2026-10-12, T007: uma asserção do teste de falha do provedor usava `or` e era sempre verdadeira; reescrita com 3 asserções.
- 2026-10-12, T011: duplicados são comparados pela linha antes do mascaramento (no mesmo lote) e pela linha mascarada (contra os aceitos); um registro com PII repetido entre tentativas pode passar como novo, porque os valores falsos diferem. Limite documentado.
- 2026-10-12, T017: 412 testes passam (381 anteriores + 31 novos); cobertura de `sintetica.sample` em 96%; `mypy --strict` e `ruff` sem erros em 102 arquivos; os 16 cenários Gherkin têm teste correspondente, com o `sintetica submit` real.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-12 | Versão inicial gerada por `/reversa-to-do` | reversa |
