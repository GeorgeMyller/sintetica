# Actions: quality-evaluator (avaliação de qualidade do dataset)

> Identificador: `007-quality-evaluator`
> Data: `2026-10-12`
> Roadmap: `_reversa_forward/007-quality-evaluator/roadmap.md`
> Fontes auxiliares: `data-delta.md`, `interfaces/eval-cli.md`, `requirements.md` (18 cenários Gherkin).

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 24 |
| Paralelizáveis (`[//]`) | 16 |
| Maior cadeia de dependência | 8 (T001 → T010 → T013 → T015 → T016 → T017 → T018 → T022) |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Criar o pacote `sintetica.quality` com `__init__.py` mínimo e a pasta `tests/quality/` | - | `[//]` | `src/sintetica/quality/__init__.py` | 🟡 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T002 | Criar os auxiliares de teste: projeto com intenção, contrato e amostra aprovados; gravação direta de `output/dataset.<ext>` e `run.json` em JSON, JSONL, CSV e conversa; valores falsos registrados na allowlist | T001 | `[//]` | `tests/quality/conftest.py` | 🟡 | `[X]` |
| T003 | Escrever testes da leitura: lista JSON, JSONL, CSV escrito pelo lote (ida e volta), linha corrompida e coluna a mais contadas como inválidas com o índice (D-03) | T002 | `[//]` | `tests/quality/test_reader.py` | 🟡 | `[X]` |
| T004 | Escrever testes do texto livre: campos `text` em listas e objetos, conversa (`messages[].content` e `labels`), normalização, texto com menos de 3 palavras como 1 trecho, `enum`, números e datas fora (D-06) | T002 | `[//]` | `tests/quality/test_text.py` | 🟢 | `[X]` |
| T005 | Escrever testes da unicidade semântica: pontuação e caixa, limiar 0,8, ordem (só o registro posterior conta), e resultado do filtro de prefixo igual ao par a par em conjuntos aleatórios com semente fixa (D-07, D-08) | T002 | `[//]` | `tests/quality/test_semantic.py` | 🟡 | `[X]` |
| T006 | Escrever testes das métricas: conformidade com o volume de `run.json` e da intenção (com aviso), unicidade estrutural, PII com e sem allowlist, duração, meta de tempo, duração não medida e ordem das métricas que falharam (D-04, D-05, D-09 a D-11) | T002 | `[//]` | `tests/quality/test_metrics.py` | 🟡 | `[X]` |
| T007 | Escrever testes do relatório: mesmos números em `report.json` e `report.md`, seção de escopo da PII, só a prévia dos achados, índices limitados a 20 no Markdown, determinismo entre 2 execuções (D-12, D-13) | T002 | `[//]` | `tests/quality/test_report.py` | 🟢 | `[X]` |
| T008 | Escrever os testes de ponta a ponta dos cenários Gherkin pela CLI, com os códigos 0, 2, 9, 10, 11, 16, 17 e 18 e a busca do valor de PII completo nos relatórios e na saída | T002 | `[//]` | `tests/quality/test_cli.py` | 🟡 | `[X]` |
| T009 | Escrever os testes da ligação com o lote: avaliação ao fim do `generate` em primeiro plano e em background, código do `generate` inalterado, erro da avaliação como aviso, veredito no `status` | T002 | `[//]` | `tests/batch/test_quality_chain.py` | 🟡 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T010 | Implementar a leitura em fluxo por formato: JSONL por linha, lista JSON com decimal exato, CSV com conversão de cada célula pelo `schema.json`; cada item traz o índice, a linha canônica ou bruta e o registro válido ou o motivo (D-03) | T001 | `[//]` | `src/sintetica/quality/reader.py` | 🟡 | `[X]` |
| T011 | Implementar o texto livre pelo `schema.json` (inclusive conversa), a normalização e os 3-gramas de palavras (D-06) | T001 | `[//]` | `src/sintetica/quality/text.py` | 🟢 | `[X]` |
| T012 | Implementar a busca exata de quase-duplicados: par a par até 1.000 registros, filtro de prefixo com filtro de tamanho acima disso, Jaccard ≥ 0,8 e a ordem da D-08 | T001 | `[//]` | `src/sintetica/quality/semantic.py` | 🟡 | `[X]` |
| T013 | Implementar as métricas: conformidade, unicidade estrutural, vazamentos de PII com índice, campo, tipo e prévia, duração, meta de tempo e veredito (D-04, D-05, D-09 a D-11) | T010, T011 | - | `src/sintetica/quality/metrics.py` | 🟡 | `[X]` |
| T014 | Implementar `Report` (Pydantic), a gravação atômica de `report.json` e a geração de `report.md` do mesmo objeto, com avisos, índices e escopo da PII (D-12, D-13) | T001 | `[//]` | `src/sintetica/quality/report.py` | 🟢 | `[X]` |
| T015 | Implementar `evaluate`: pré-condições e códigos 2, 9, 10, 11, 16 e 18, trava do lote, avaliação, relatório, bloco curto da saída e códigos 0 e 17 (D-02, D-14, D-15, D-18) | T012, T013, T014 | - | `src/sintetica/quality/service.py` | 🟢 | `[X]` |
| T016 | Implementar `evaluate_after_lot`: mesma avaliação sem a checagem da trava, devolvendo as linhas da saída ou o aviso de erro com o comando `sintetica eval` (D-16) | T015 | - | `src/sintetica/quality/service.py` | 🟢 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T017 | Chamar `evaluate_after_lot` em `_execute` depois do arquivo final, em todo status final; tirar a linha "Próximo passo: avaliação de qualidade"; manter o código do `generate`; ajustar as asserções antigas dos testes do lote (D-16) | T016 | - | `src/sintetica/batch/service.py` | 🟢 | `[X]` |
| T018 | Mostrar no `status` a linha "Avaliação: <veredito> (<caminho de report.md>)" quando `report.json` existe (D-17) | T017 | - | `src/sintetica/batch/service.py` | 🟡 | `[X]` |
| T019 | Acrescentar o comando `eval` ao `sintetica`, com importação tardia e os códigos 17 e 18 na docstring; demais comandos inalterados | T015 | - | `src/sintetica/cli.py` | 🟢 | `[X]` |
| T020 | Expor a API pública de `sintetica.quality`: `evaluate`, `evaluate_after_lot`, `Report`, `load_report`, com `__all__` | T016 | - | `src/sintetica/quality/__init__.py` | 🟡 | `[X]` |
| T021 | Escrever o teste `perf` de 10.000 registros de cerca de 1 KB: avaliação em ≤ 120 s, com textos parecidos para exercitar o filtro de prefixo (RNF de desempenho, R-01, R-02) | T015 | `[//]` | `tests/quality/test_perf.py` | 🟡 | `[X]` |
| T022 | Completar os testes até cobertura ≥ 80% em `sintetica.quality`, com os 18 cenários Gherkin cobertos, os 471 testes anteriores passando e `mypy --strict` e `ruff` sem erros (critério de pronto) | T017, T018, T019, T020, T021, T003, T004, T005, T006, T007, T008, T009 | - | `tests/quality/` | 🟡 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T023 | Escrever a documentação curta: fluxo da skill `sintetica-eval`, as 4 métricas e metas, veredito, duração, arquivos do relatório, escopo da PII e códigos de saída | T020 | `[//]` | `docs/quality-evaluator.md` | 🟡 | `[X]` |
| T024 | Atualizar a documentação do lote: avaliação ao fim do `generate`, veredito no `status` e os códigos 17 e 18 | T018 | `[//]` | `docs/batch-generator.md` | 🟢 | `[X]` |

## Notas de execução

<!--
Reservado para /reversa-coding registrar avisos ou observações que surgiram durante a execução.
Não use isso para corrigir ações, edits manuais ficam fora desse arquivo, vão direto no código.
-->

- O `SKILL.md` da skill `sintetica-eval` fica fora desta feature, como nas features 003 a 006; a T023 documenta o que a skill precisa instruir ao agente.
- As T017, T018 e T024 alteram arquivos da feature 006 (`batch/service.py`, `tests/batch/test_cli.py`, `tests/batch/test_engine.py`, `docs/batch-generator.md`). 2 asserções antigas que citavam a linha "Próximo passo: avaliação de qualidade" foram trocadas pela verificação da avaliação.
- 2026-10-12, T010: os testes da T003 acharam um defeito. Uma linha CSV com coluna a mais quebrava a leitura com `TypeError`, porque o `csv.DictReader` guarda o excesso sob a chave `None`. Correção: leitura com `csv.reader` e comparação do número de células com o cabeçalho.
- 2026-10-12, T013: decisão de execução. Linha inválida também passa pela busca de PII, com o texto bruto no campo `registro`; um dado pessoal numa linha inválida conta como vazamento.
- 2026-10-12, T015: decisão de execução. Lista JSON que não é lista, ou arquivo ilegível, gera o código 18 ("dataset final ilegível"), o mesmo do dataset ausente.
- 2026-10-12, T015: o `load_record_model` da feature 003 regera o `schema.py` quando o cabeçalho não bate com o `schema.json`; por isso a avaliação pode reescrever o `schema.py`, como os demais comandos já fazem.
- 2026-10-12, T016: a avaliação no fim do lote é importada dentro da função (`_execute`), para evitar o ciclo de importação `sintetica.batch` ↔ `sintetica.quality`.
- 2026-10-12, T021: teste `perf` com 10.000 registros de cerca de 2 KB, com trecho comum para exercitar o filtro de prefixo, terminou em 3,9 s (meta ≤ 120 s).
- 2026-10-12, T022: 516 testes passam (471 anteriores + 45 novos: 40 em `tests/quality/` e 5 em `tests/batch/test_quality_chain.py`), mais 3 testes `perf` fora da suíte padrão; cobertura de `sintetica.quality` em 97%; `mypy --strict` e `ruff` sem erros em 140 arquivos; os 18 cenários Gherkin têm teste correspondente. Os testes com processo real passaram em 5 execuções seguidas.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-12 | Versão inicial gerada por `/reversa-to-do` | reversa |
