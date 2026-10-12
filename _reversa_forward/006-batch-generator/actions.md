# Actions: batch-generator (geração do lote completo)

> Identificador: `006-batch-generator`
> Data: `2026-10-12`
> Roadmap: `_reversa_forward/006-batch-generator/roadmap.md`
> Fontes auxiliares: `data-delta.md`, `interfaces/generate-cli.md`, `requirements.md` (17 cenários Gherkin).

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 30 |
| Paralelizáveis (`[//]`) | 20 |
| Maior cadeia de dependência | 10 (T002 → T015 → T016 → T018 → T019 → T020 → T021 → T023 → T025 → T029) |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Criar o pacote `sintetica.batch` com `__init__.py` mínimo e a pasta `tests/batch/` | - | `[//]` | `src/sintetica/batch/__init__.py` | 🟡 | `[X]` |
| T002 | Tornar públicas `first_error` e `mask_value` em `sintetica.sample.review` (hoje `_first_error` e `_mask`), sem mudar `review_records` (D-10) | - | `[//]` | `src/sintetica/sample/review.py` | 🟡 | `[X]` |
| T003 | Extrair `intent_lines(intent)` de `build_instructions` em `sintetica.sample.request`, com a saída de `build_instructions` idêntica (D-11) | - | `[//]` | `src/sintetica/sample/request.py` | 🟡 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Criar os auxiliares de teste: projeto com intenção confirmada, contrato e amostra aprovados (JSON, CSV e Expresso); fábrica de provedor simulado com respostas por bloco, falha no bloco k e parada por teto; agente que responde pelo `sintetica submit` real; servidor HTTP local no formato do Ollama (D-23) | T001 | `[//]` | `tests/batch/conftest.py` | 🟡 | `[X]` |
| T005 | Escrever testes do plano de blocos: tamanho médio da amostra, bloco de 10 para registros curtos, de 4 para cerca de 1.000 tokens, mínimo 1, `--block-size` de 1 a 100, divisão dos faltantes por rodada (D-05) | T004 | `[//]` | `tests/batch/test_plan.py` | 🟢 | `[X]` |
| T006 | Escrever testes da revisão por bloco: inválido com motivo sem o valor, duplicado no bloco e contra o índice, CPF trocado, revalidação que reprova o valor falso, índice reconstruído a partir do arquivo parcial (D-09) | T004 | `[//]` | `tests/batch/test_review.py` | 🟡 | `[X]` |
| T007 | Escrever testes da saída: anexo por bloco com `fsync`, truncamento ao bloco anterior em erro de escrita, última linha incompleta descartada na leitura, conversão para lista JSON, JSONL e CSV pela RFC 4180 (D-12, D-13, D-19) | T004 | `[//]` | `tests/batch/test_output.py` | 🟢 | `[X]` |
| T008 | Escrever testes do motor: rodadas extras só com faltantes, status `concluido` (≥ 95%), `incompleto`, `interrompido_custo` e `falha_provedor`, parada da fila após falha, retomada sem pedir blocos gravados, teto restante na retomada, pedido único ao harness com id novo por rodada (D-04, D-06, D-08, D-14) | T004 | `[//]` | `tests/batch/test_engine.py` | 🟡 | `[X]` |
| T009 | Escrever testes da trava e do background: trava exclusiva por dataset, trava liberada quando o processo morre, argumentos do `Popen` em POSIX e Windows, processo real com o servidor local devolvendo o controle em ≤ 5 s, `status` com processo encerrado e `--resume` (D-15 a D-17) | T004 | `[//]` | `tests/batch/test_background.py` | 🟡 | `[X]` |
| T010 | Escrever os testes de ponta a ponta dos 17 cenários Gherkin pela CLI, com os códigos 0, 2, 9, 10, 11, 12, 14, 15 e 16 e a busca do CPF original em todos os arquivos e saídas | T004 | `[//]` | `tests/batch/test_cli.py` | 🟡 | `[X]` |
| T011 | Acrescentar testes das mudanças na amostra: `first_error` e `mask_value` públicos, `build_instructions` com a mesma saída após `intent_lines`, aprovação citando `sintetica generate` | T002, T003 | `[//]` | `tests/sample/test_shared.py` | 🟡 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T012 | Implementar `RunState` (Pydantic, `extra="forbid"`), os 7 status, leitura e gravação atômica com `sintetica.fsutil.write_atomic` (data-delta.md#1) | T001 | `[//]` | `src/sintetica/batch/state.py` | 🟡 | `[X]` |
| T013 | Implementar o plano de blocos: `avg_tokens(seeds)` com `estimate_tokens`, `block_size(avg, override)` e `split(faltantes, bloco)` (D-05) | T001 | `[//]` | `src/sintetica/batch/plan.py` | 🟢 | `[X]` |
| T014 | Implementar `build_batch_request(intent, schema_json, seeds, k, bloco, total_blocos, rodada)` com `intent_lines`, "bloco b de B, rodada r de 4" e "não repita os exemplos" (D-11) | T001, T003 | `[//]` | `src/sintetica/batch/request.py` | 🟡 | `[X]` |
| T015 | Implementar `DedupIndex` (SHA-256 das linhas mascaradas e das brutas, só em memória) e `review_block(raw, Record, index, masker, limit)` com `first_error` e `mask_value` (D-09) | T001, T002 | `[//]` | `src/sintetica/batch/review.py` | 🟡 | `[X]` |
| T016 | Implementar a saída: `PartialWriter` (anexo, `flush`, `os.fsync`, truncamento em erro), `load_partial` (descarta linha incompleta e reconstrói o índice) e `convert_final(formato)` em fluxo com arquivo temporário e `os.replace` (D-12, D-13, D-19) | T012, T015 | - | `src/sintetica/batch/output.py` | 🟢 | `[X]` |
| T017 | Implementar `DatasetLock` em `output/run.lock`: `fcntl.flock` em POSIX e `msvcrt.locking` no Windows, `try_acquire`, `is_held` e o descritor herdável (D-16) | T001 | `[//]` | `src/sintetica/batch/lock.py` | 🟡 | `[X]` |
| T018 | Implementar o motor para provedor automático: fila de blocos com N trabalhadores, evento de parada, rodadas extras, gravação por bloco, contagens e custo em `run.json`, callback de progresso e status final (D-08, D-12, D-14, D-21) | T012, T013, T014, T015, T016 | - | `src/sintetica/batch/engine.py` | 🟡 | `[X]` |
| T019 | Implementar o caminho do harness no motor: pedido único com o volume, `HarnessResponsePending` → `aguardando_agente` com o comando `submit`, leitura da resposta, remoção da resposta bruta e rodada seguinte (D-04) | T018 | - | `src/sintetica/batch/engine.py` | 🟢 | `[X]` |
| T020 | Implementar em `generate` as pré-condições (códigos 2, 11 e 14) e o tratamento do lote existente: em andamento, interrompido, aguardando o agente, status final, `--resume` e `--new` (D-02, D-18) | T017, T019 | - | `src/sintetica/batch/service.py` | 🟢 | `[X]` |
| T021 | Implementar em `generate` a escolha do provedor pelo volume total, a estimativa e a autorização (código 15), o teto restante na retomada, a estimativa por pedido, a execução em primeiro plano e a mensagem final com o próximo passo (D-03, D-06, D-07, D-22) | T020 | - | `src/sintetica/batch/service.py` | 🟢 | `[X]` |
| T022 | Implementar `start_background(project, slug, lock)`: `Popen` de `sys.executable -m sintetica.batch.worker` em sessão própria, entrada nula, saída em `output/worker.log`, trava herdada em POSIX, PID devolvido (D-15) | T012, T017 | `[//]` | `src/sintetica/batch/background.py` | 🟢 | `[X]` |
| T023 | Implementar o ponto de entrada do processo separado: pega ou herda a trava, roda o motor com o `run.json` gravado e registra o progresso em `worker.log` sem valores de registro; ligar o volume > 100 do `generate` a `start_background` | T021, T022 | - | `src/sintetica/batch/worker.py` | 🟡 | `[X]` |
| T024 | Implementar `status`: status, aceitos/volume, descartados, custo, provedor, bloco, rodada e caminhos; com `em_andamento` e a trava livre, "processo encerrado" e o comando `--resume` (D-17) | T021 | - | `src/sintetica/batch/service.py` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T025 | Acrescentar os comandos `generate` (`--resume`, `--new`, `--authorize-usd`, `--block-size`) e `status` ao `sintetica`, com importação tardia, progresso impresso por bloco e os códigos 14, 15 e 16; demais comandos inalterados | T023, T024 | - | `src/sintetica/cli.py` | 🟡 | `[X]` |
| T026 | Expor a API pública de `sintetica.batch`: `generate`, `status`, `RunState`, `load_run_state`, com `__all__` | T024 | - | `src/sintetica/batch/__init__.py` | 🟡 | `[X]` |
| T027 | Trocar o próximo passo da aprovação da amostra por `uv run sintetica generate <slug>` e ajustar a asserção do teste da amostra que cita o texto antigo (D-22) | - | `[//]` | `src/sintetica/sample/service.py` | 🟢 | `[X]` |
| T028 | Escrever o teste `perf` de 10.000 registros de cerca de 1 KB com provedor simulado: memória ≤ 500 MB por `tracemalloc` e 0 duplicados no arquivo final (RNF de memória, R-07) | T018 | `[//]` | `tests/batch/test_perf.py` | 🟡 | `[X]` |
| T029 | Completar os testes até cobertura ≥ 80% em `sintetica.batch`, com os 17 cenários Gherkin cobertos, os 412 testes anteriores passando e `mypy --strict` e `ruff` sem erros (critério de pronto) | T025, T026, T027, T028, T005, T006, T007, T008, T009, T010, T011 | - | `tests/batch/` | 🟡 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T030 | Escrever a documentação curta: fluxo da skill `sintetica-generate` (harness, primeiro plano, background), autorização de custo, `status`, `--resume`, `--new`, `--block-size`, arquivos de saída e códigos de saída | T026 | `[//]` | `docs/batch-generator.md` | 🟡 | `[X]` |

## Notas de execução

<!--
Reservado para /reversa-coding registrar avisos ou observações que surgiram durante a execução.
Não use isso para corrigir ações, edits manuais ficam fora desse arquivo, vão direto no código.
-->

- O `SKILL.md` da skill `sintetica-generate` fica fora desta feature, como nas features 003 a 005; a T030 documenta o que a skill precisa instruir ao agente.
- As T002, T003, T011 e T027 alteram arquivos da feature 005 (`sample/review.py`, `sample/request.py`, `sample/service.py`, `tests/sample/test_cli.py`). `review_records` e `build_instructions` mantêm a mesma saída; o texto do próximo passo da aprovação mudou e 1 asserção antiga foi ajustada.
- 2026-10-12, T023: o teste com processo real achou um defeito que os testes de unidade não pegaram. As sementes eram lidas com `Decimal`, e o prompt dos backends reais não serializa `Decimal`. Correção: sementes lidas com `json.loads` comum, como na amostra. O provedor simulado dos testes passou a montar o prompt real (`build_user_prompt`), para pegar esse tipo de erro.
- 2026-10-12, T023: decisão nova (fora do roadmap). Erro inesperado no processo em background grava só o nome da exceção no `worker.log`, sem traceback, porque a mensagem poderia citar um registro. O `status` detecta o processo encerrado e sugere `--resume`.
- 2026-10-12, T018: decisão de execução. A retomada zera o contador de rodadas: cada `--resume` tem de novo a 1ª rodada e as 3 extras. `--resume` também vale para `incompleto` e `interrompido_custo`; com `--authorize-usd`, o novo valor é o total autorizado, e o teto passado ao provedor desconta o já gasto.
- 2026-10-12, T015: limite documentado. Na retomada, o índice de duplicados é reconstruído só com as linhas mascaradas do arquivo parcial; os hashes das linhas brutas ficam só em memória e se perdem. Um registro com PII repetido depois de uma retomada pode passar como novo, porque os valores falsos diferem (mesmo limite da feature 005).
- 2026-10-12, T019: um registro igual a uma semente da amostra é aceito; a amostra não faz parte do lote.
- 2026-10-12, T009: o ramo Windows de `lock.py` e `background.py` não roda nesta máquina (macOS); só os argumentos do `Popen` têm teste de unidade (R-06).
- 2026-10-12, T028: teste `perf` com 10.000 registros de cerca de 1 KB passou em 5 s, abaixo de 500 MB de pico pelo `tracemalloc`, com 0 duplicados.
- 2026-10-12, T029: 471 testes passam (412 anteriores + 59 novos: 55 em `tests/batch/` e 4 em `tests/sample/test_shared.py`), mais 1 teste `perf` fora da suíte padrão; cobertura de `sintetica.batch` em 92%; `mypy --strict` e `ruff` sem erros em 123 arquivos; os 17 cenários Gherkin têm teste correspondente, com o `sintetica submit` real e processo real em background. Os testes com processo real passaram em 5 execuções seguidas.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-12 | Versão inicial gerada por `/reversa-to-do` | reversa |
