# Actions: intent-interview (entrevista de intenção e pasta do dataset)

> Identificador: `004-intent-interview`
> Data: `2026-10-12`
> Roadmap: `_reversa_forward/004-intent-interview/roadmap.md`
> Fontes auxiliares: `data-delta.md`, `interfaces/intent-cli.md`, `requirements.md` (14 cenários Gherkin).

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 19 |
| Paralelizáveis (`[//]`) | 11 |
| Maior cadeia de dependência | 7 (T002 → T008 → T011 → T012 → T015 → T016 → T018) |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Criar `write_atomic(path, text)`: temporário na mesma pasta, `os.replace`, remoção do temporário em falha (D-15) | - | `[//]` | `src/sintetica/fsutil.py` | 🟡 | `[X]` |
| T002 | Criar o pacote `sintetica.intent` com `__init__.py` mínimo e a pasta `tests/intent/` | - | `[//]` | `src/sintetica/intent/__init__.py` | 🟡 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Escrever testes do slug: acentos, símbolos, limite de 60 caracteres, nome vazio com data UTC, colisão com `-2` e `-3` (RN-02) | T002 | `[//]` | `tests/intent/test_slug.py` | 🟡 | `[X]` |
| T004 | Escrever testes das respostas: itens um a um e vários numa chamada, `--unknown`, padrões JSONL e 10, formato fora da lista, volume fora do intervalo com contador e 3ª recusa, conflito item e `--unknown`, tudo ou nada, mascaramento com aviso sem o valor original, falha de política sem gravação (RF-04 a RF-11) | T002 | `[//]` | `tests/intent/test_answers.py` | 🟡 | `[X]` |
| T005 | Escrever testes do resumo: estados incompleta, precisa de confirmação (Guiado e Expresso crítico), pronta, marcações definido/indefinido/pendente/padrão, truncamento em 80 caracteres (RF-12 a RF-14) | T002 | `[//]` | `tests/intent/test_summary.py` | 🟢 | `[X]` |
| T006 | Escrever testes da CLI: `start` (pasta, `seeds/`, `started_at`, caminho absoluto, falha de escrita com código 10), `intent questions`, `set`, `show`, `confirm` com os códigos 0, 2, 8, 9 e 10, e busca do valor original de PII em todos os arquivos e saídas | T002 | `[//]` | `tests/intent/test_cli.py` | 🟡 | `[X]` |
| T007 | Escrever o teste de contrato: intenção completa gravada pela entrevista é lida por `sintetica.schema.intent.load_intent` e aceita por `sintetica schema build`, com rascunho e com estrutura indefinida (D-16, RF-17) | T002 | `[//]` | `tests/intent/test_contract_schema.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Implementar `IntentModel` (Pydantic, `extra="allow"`), `Item` com `pendente`/`definido`/`indefinido`, nomes dos 5 itens, constantes de padrão (JSONL, 10) e limites de volume; leitura e gravação de `intent.json` via `write_atomic` (D-02, D-03, D-10) | T002 | - | `src/sintetica/intent/model.py` | 🟡 | `[X]` |
| T009 | Implementar `resolve_slug(nome, datasets_dir, agora)` e a criação da pasta com `mkdir(exist_ok=False)` em laço para colisões (D-04, R-05) | T002 | `[//]` | `src/sintetica/intent/slug.py` | 🟡 | `[X]` |
| T010 | Implementar o texto das 5 perguntas sem jargão, com 1 exemplo por persona, e a forma em bloco único para o Expresso (D-13) | T002 | `[//]` | `src/sintetica/intent/questions.py` | 🟡 | `[X]` |
| T011 | Implementar a validação das respostas: formato sem diferenciar maiúsculas, volume de 1 a 10.000 com `volume_rejections` e padrão na 3ª recusa, `--unknown` com padrões, conflito entre item e `--unknown`, aplicação tudo ou nada (D-06, D-08, D-09, D-10) | T008 | - | `src/sintetica/intent/answers.py` | 🟡 | `[X]` |
| T012 | Acrescentar o mascaramento: `PiiGuard.for_dataset(...).mask` em objetivo, estrutura e regras antes de qualquer gravação; aviso com item e tipos; `PolicyError` ou erro de escrita da allowlist viram falha de mascaramento sem gravar (D-07) | T011 | - | `src/sintetica/intent/answers.py` | 🟢 | `[X]` |
| T013 | Implementar o resumo: linhas por item, truncamento em 80 caracteres, estados completa, crítica, precisa de confirmação e pronta, e a linha final com o próximo comando (D-11, D-12, D-17, data-delta.md#2) | T008 | `[//]` | `src/sintetica/intent/summary.py` | 🟢 | `[X]` |
| T014 | Implementar `start(project_dir, nome, modo)`: slug, `datasets/<slug>/seeds/`, `intent.json` inicial com `started_at` UTC, saída com caminho absoluto; falha de escrita vira código 10 (D-05) | T001, T008, T009 | - | `src/sintetica/intent/service.py` | 🟢 | `[X]` |
| T015 | Implementar `set_answers`, `show` e `confirm`: dataset ou intenção ausente (código 2), resposta inválida (8), mascaramento indisponível (9), falha de escrita (10); `confirm` com intenção incompleta devolve 8 e lista os itens que faltam | T012, T013, T014 | - | `src/sintetica/intent/service.py` | 🟡 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T016 | Acrescentar os subcomandos `start` e `intent` (`questions`, `set`, `show`, `confirm`) ao `sintetica`, com importação tardia e os códigos 8, 9 e 10; demais subcomandos inalterados (D-14) | T010, T015 | - | `src/sintetica/cli.py` | 🟡 | `[X]` |
| T017 | Expor a API pública de `sintetica.intent`: `IntentModel`, `load_intent_model`, `start`, `set_answers`, `show`, `confirm`, com `__all__` | T015 | - | `src/sintetica/intent/__init__.py` | 🟡 | `[X]` |
| T018 | Completar os testes até cobertura ≥ 80% em `sintetica.intent`, com os 14 cenários Gherkin cobertos, os 326 testes anteriores passando e `mypy --strict` e `ruff` sem erros (critério de pronto) | T016, T017, T003, T004, T005, T006, T007 | - | `tests/intent/` | 🟡 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T019 | Escrever a documentação curta: fluxo Guiado e Expresso para a skill `sintetica-start`, comandos, citação de textos com aspas simples no shell (R-02), códigos de saída e estados do resumo | T017 | `[//]` | `docs/intent-interview.md` | 🟡 | `[X]` |

## Notas de execução

<!--
Reservado para /reversa-coding registrar avisos ou observações que surgiram durante a execução.
Não use isso para corrigir ações, edits manuais ficam fora desse arquivo, vão direto no código.
-->

- O `SKILL.md` da skill `sintetica-start` fica fora desta feature, como na feature 003; a T019 documenta o que a skill precisa instruir ao agente.
- A verificação de confirmação dentro do `sintetica schema build` (feature 003) não faz parte desta feature; ficou registrada como ponto de atenção no relatório do `/reversa-plan`.
- 2026-10-12, T012: o mascaramento usa a interface `Masker` (Protocol) com o adaptador `PiiGuardMasker`; `set_answers` aceita uma fábrica injetada, usada nos testes. O mascaramento só é criado quando há texto na chamada.
- 2026-10-12, T011: uma resposta nova em item já confirmado zera `confirmed_at` (nova confirmação exigida). Volume aceita separadores de milhar (`2.000`, `2 000`).
- 2026-10-12, T015: com resposta inválida, só o contador `volume_rejections` é gravado; se essa gravação falhar, o código é 10.
- 2026-10-12, T018: 381 testes passam (326 anteriores + 55 novos); cobertura de `sintetica.intent` em 99% e de `sintetica.fsutil` em 100%; `mypy --strict` e `ruff` sem erros em 90 arquivos; os 14 cenários Gherkin têm teste correspondente. A suíte nova passou na 1ª execução; reforcei 1 asserção fraca (falha de política) e acrescentei `test_failures.py` para os caminhos de escrita.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-12 | Versão inicial gerada por `/reversa-to-do` | reversa |
