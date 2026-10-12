# Roadmap: quality-evaluator (avaliação de qualidade do dataset)

> Identificador: `007-quality-evaluator`
> Data: `2026-10-12`
> Requirements: `_reversa_forward/007-quality-evaluator/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA
> Cenário: greenfield. Sem `architecture.md`, `c4-context.md`, `state-machines.md`, `dependencies.md` nem `code-analysis.md`. Adendos vigentes lidos: `addenda/001-pii-guard.md` a `addenda/006-batch-generator.md`.

## 1. Resumo da abordagem

🟡 A feature cria o pacote `sintetica.quality` e o comando `sintetica eval <slug>`. Ela não cria validador nem detector novos: valida com `load_record_model` (003), detecta PII com `PiiGuard.leaks` e `coverage()` (001), lê `started_at` da intenção (004) e lê `output/dataset.<ext>` e `output/run.json` do lote (006).
🟡 A avaliação lê o dataset em fluxo, 1 registro por vez, e acumula:
- conformidade (válidos sobre o volume pedido);
- unicidade estrutural (hashes do JSON canônico);
- texto livre normalizado para a unicidade semântica;
- vazamentos de PII.
🟡 A unicidade semântica é calculada no fim, por 3-gramas de palavras e Jaccard ≥ 0,8 (Q47). A busca de pares é exata e sem dependência nova: até 1.000 registros, par a par; acima disso, filtro de prefixo sobre um índice invertido, que dá o mesmo resultado que o par a par (D-07).
🟡 O relatório sai em `report.json` e `report.md`, com os mesmos números. O fim do `sintetica generate` roda a mesma avaliação (Q49), sem mudar o código de saída do lote.

## 2. Princípios aplicados

🟡 `.reversa/principles.md` não existe. Sem princípios formais para verificar.

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| n/a | Arquivo de princípios ausente | n/a |

🟡 Restrições do PRD tratadas como princípios de fato:
- privacidade por design (Q21): o relatório só mostra a prévia mascarada;
- operação local (Q15): 0 chamadas de rede;
- tipagem estrita e cobertura ≥ 80% (Q19).

Todas são respeitadas.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Novo pacote `sintetica.quality` (`reader.py`, `text.py`, `semantic.py`, `metrics.py`, `report.py`, `service.py`) | Mesma organização por componente das features 001 a 006 | Estender `sintetica.batch` | 🟡 |
| D-02 | Pré-condições na ordem: dataset e intenção (2), contrato legível pelo `schema.json` e `load_record_model` (11), lote em andamento com a trava ocupada (16, salvo chamada interna do lote), dataset final `output/dataset.<ext>` (18, cita `sintetica generate` e `--resume`), mascaramento disponível pelo `PiiGuard.for_dataset` (9) | RF-12, RF-13; a avaliação não emite veredito sem as fontes | Avaliar sem contrato | 🟢 |
| D-03 | Leitura em fluxo por formato. JSONL: 1 linha por registro. JSON: lista lida com `json.load(..., parse_float=Decimal)`. CSV: `csv.DictReader`, com cada célula convertida pelo `schema.json` (vazio → `None` em campo opcional e `[]` em lista; lista dividida por `\|`). Linha ilegível ou coluna a mais conta como inválida | RF-01, EC-02, Q35 | Validar só o JSON | 🟡 |
| D-04 | Conformidade = `min(válidos, volume) / volume`. O volume é `volume_requested` de `run.json`; sem `run.json`, o volume da intenção. Volume diferente entre os 2 gera aviso | RN-01; `run.json` guarda o volume que o lote realmente pediu | Sempre o volume da intenção (muda se a intenção for editada depois) | 🟡 |
| D-05 | Unicidade estrutural = hashes SHA-256 distintos / registros lidos. Registro válido usa `to_jsonl_line`; registro inválido usa a linha bruta | RN-02, RF-03 | Só registros válidos | 🟡 |
| D-06 | Texto livre pelo `schema.json`: campos `text`, inclusive em `list` de `text` e em `object`; contrato `conversation` usa `messages[].content` mais os campos `text` de `labels`. Normalização: minúsculas, pontuação Unicode (categoria P) trocada por espaço, espaços únicos. 3-gramas de palavras; texto com menos de 3 palavras vira 1 trecho. `enum`, números e datas ficam fora | RN-03 (Q47) | Texto de todos os campos | 🟢 |
| D-07 | Busca de quase-duplicados exata, sem dependência: até 1.000 registros, par a par; acima disso, filtro de prefixo (os trechos de cada registro ordenados pela raridade global, com desempate pelo texto; candidatos são os que compartilham um trecho do prefixo de tamanho `n − ⌈0,8·n⌉ + 1`), com filtro de tamanho e Jaccard exato nos candidatos. O resultado é o mesmo do par a par | RN-04, RNF de determinismo; MinHash em Python puro (128 permutações × 10.000 × ~170 trechos) passaria de 120 s, e a `datasketch` traria `numpy` como dependência | MinHash com LSH (aproximado, exige dependência para ser rápido) | 🟡 |
| D-08 | Ordem: o registro i é quase-duplicado se existe j < i com Jaccard ≥ 0,8. Unicidade semântica = 1 − quase-duplicados / registros com texto. Sem campo de texto no contrato: "não aplicável" | RN-03, RN-07, EC-03 | Contar os 2 lados do par | 🟢 |
| D-09 | PII: cada valor de texto do registro (texto livre e `enum`) passa por `PiiGuard.leaks(texto, field=<caminho>)`. Cada vazamento entra em `pii_findings` com índice, campo, tipo e `preview` (2 caracteres + `***`). Sem allowlist (`allowlist_available = False`), o relatório traz o aviso | RN-05, RF-05, EC-04 | Só texto livre (PII em `enum` passaria) | 🟢 |
| D-10 | Duração: `finished_at` (UTC, hora da emissão) − `started_at` da intenção, em minutos com 1 casa decimal (`ROUND_HALF_UP`). Meta de tempo só para volume ≤ 100: `time_target_met = duração < 10`. A intenção não é alterada; `finished_at` fica no relatório | RN-06, Q20; RF-15 pede o resto do relatório idêntico entre execuções | Gravar `finished_at` no `intent.json` | 🟡 |
| D-11 | Veredito pela RN-07; `failed_metrics` em ordem fixa (`conformidade`, `unicidade_estrutural`, `unicidade_semantica`, `pii`) | RF-07, RF-15 | Ordem por gravidade | 🟢 |
| D-12 | `report.json` pelo modelo `Report` (Pydantic, `extra="forbid"`), com percentuais como decimal de 1 casa; `report.md` gerado do mesmo objeto, com as seções métricas, avisos, registros com problema (até 20 índices por tipo, com o total) e "Escopo e limites da detecção de PII". Os 2 gravados com `write_atomic` | RF-08, RF-09, RF-15 | Gerar o Markdown separado (números podem divergir) | 🟢 |
| D-13 | Avisos no relatório: status do lote diferente de `concluido`, `schema_version` de `run.json` diferente do contrato atual (avalia com o atual), volume divergente, allowlist ausente | RN-09, EC-05 | Recusar a avaliação | 🟢 |
| D-14 | Saída curta no chat: veredito, conformidade, unicidade estrutural, unicidade semântica, vazamentos, duração e caminho absoluto de `report.md` | RF-10 | Relatório inteiro no chat | 🟢 |
| D-15 | Códigos: 0 `APROVADO`, 17 `REPROVADO`, 18 dataset final ausente (Q48); erros: 2, 9, 10, 11 e 16 (lote em andamento) | RN-10 | Código 2 para reprovado | 🟢 |
| D-16 | Fim do lote: `sintetica.batch.service._execute` chama `quality.service.evaluate_after_lot(...)` depois de gerar o arquivo final, em todo status final, dentro da trava do lote. As linhas da avaliação entram na saída (e no `worker.log`, só com números e prévias). O código do `generate` não muda; erro da avaliação vira aviso com o comando `sintetica eval` | RN-11 (Q49) | Processo separado para a avaliação | 🟢 |
| D-17 | `sintetica status` mostra o veredito quando `report.json` existe; a linha "Próximo passo: avaliação de qualidade" do lote sai | RN-11; o elo agora existe | Manter a linha | 🟡 |
| D-18 | Avaliação avulsa (`sintetica eval`) com a trava do lote ocupada: código 16, para não avaliar um dataset que o lote ainda vai reescrever | Coerente com a RN-11 da feature 006 | Avaliar o arquivo antigo | 🟡 |

> 🟢 nas decisões confirmadas por respostas do revisor (Q9, Q20, Q27, Q35, Q47, Q48, Q49) ou por código entregue (adendos 001 a 006).

## 4. Premissas

🟡 Nenhuma premissa vinda de `[DÚVIDA]`: o `requirements.md` está com 0 marcadores após o clarify.

| Premissa | Origem (`requirements.md` seção) | Risco se errada |
|----------|----------------------------------|-----------------|
| A troca de MinHash por busca exata com filtro de prefixo atende a RN-04, porque mede a mesma coisa sem aproximação e cabe no tempo | 4. RN-04 | Se o revisor exigir MinHash literal, o módulo `semantic.py` troca de algoritmo sem mudar a interface |
| O `schema.json` gravado pelo `schema build` já é a versão achatada para CSV, com os nomes das colunas | 4. RN-03 | Texto livre de CSV ficaria sem caminho; teste com contrato CSV aninhado |
| `started_at` está em UTC no formato `AAAA-MM-DDTHH:MM:SSZ` (adendo 004) | 4. RN-06 | Duração "não medida" com aviso |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `sintetica.quality` | `_reversa_sdd/sdd/quality-evaluator.md` | componente-novo | Leitura, texto, unicidade semântica, métricas, relatório e serviço |
| `sintetica.batch.service` | `_reversa_sdd/addenda/006-batch-generator.md` | contrato-alterado | Avaliação ao fim do lote; veredito no `status`; linha de próximo passo removida |
| `sintetica.cli` | `_reversa_sdd/addenda/004-intent-interview.md` (comando `sintetica`) | contrato-alterado | Comando `eval` e códigos 17 e 18 |
| `sintetica.pii`, `sintetica.schema`, `sintetica.intent` | adendos 001, 003 e 004 | sem mudança | Consumidos pelas APIs públicas |

Estrutura de arquivos prevista:

```
src/sintetica/quality/__init__.py
src/sintetica/quality/reader.py     # leitura em fluxo de JSON, JSONL e CSV (D-03)
src/sintetica/quality/text.py       # texto livre, normalização e 3-gramas (D-06)
src/sintetica/quality/semantic.py   # quase-duplicados exatos com filtro de prefixo (D-07, D-08)
src/sintetica/quality/metrics.py    # conformidade, estrutural, PII, duração, veredito (D-04, D-05, D-09 a D-11)
src/sintetica/quality/report.py     # Report, report.json e report.md (D-12, D-13)
src/sintetica/quality/service.py    # evaluate, evaluate_after_lot (D-02, D-14 a D-18)
src/sintetica/batch/service.py      # avaliação ao fim do lote e veredito no status (D-16, D-17)
src/sintetica/cli.py                # comando eval
tests/quality/…
docs/quality-evaluator.md
```

## 6. Delta no modelo de dados

- Resumo das mudanças: 🟡 `datasets/<slug>/report.json` e `report.md` novos; nenhum arquivo de outra feature muda.
- Detalhe completo em: `_reversa_forward/007-quality-evaluator/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| `sintetica eval` e mudanças em `sintetica generate` e `sintetica status` | arquivo + CLI | `_reversa_forward/007-quality-evaluator/interfaces/eval-cli.md` |

## 8. Plano de migração

n/a. Arquivos novos. O `generate` ganha a avaliação no fim, sem mudar os códigos de saída; o `status` ganha 1 linha.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| R-01: Avaliação de 10.000 registros passa de 120 s | médio | baixo | Busca com filtro de prefixo e filtro de tamanho (D-07); teste `perf` com 10.000 registros de 1 KB |
| R-02: Muitos textos parecidos geram muitos candidatos e o tempo cresce | médio | baixo | Filtro de tamanho antes do Jaccard; o pior caso (todos iguais) é linear após o 1º par, porque o registro para no 1º par ≥ 0,8 |
| R-03: Valor de PII completo aparece no relatório ou no `worker.log` | alto | baixo | Só a `preview` do `PiiFinding`; teste que busca o valor original nos 2 relatórios e na saída |
| R-04: Leitura de CSV diverge da escrita do lote | médio | médio | Conversão pelo `schema.json` (D-03); teste de ida e volta com o CSV do lote |
| R-05: A avaliação dentro do lote falha e muda o código do `generate` | médio | baixo | Erro vira aviso; código do `generate` inalterado (D-16); teste |
| R-06: Relatório muda entre execuções e quebra o determinismo | baixo | baixo | Sem `set` na saída; índices ordenados; ordem fixa das métricas; teste com 2 execuções |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Re-extração reversa executada e sem regressão vermelha (recomendado, não obrigatório)
- [ ] `mypy --strict` e `ruff` sem erros no projeto
- [ ] Cobertura ≥ 80% em `sintetica.quality`
- [ ] Os 18 cenários Gherkin do `requirements.md` cobertos por testes
- [ ] Os 471 testes das features 001 a 006 continuam passando

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-12 | Versão inicial gerada por `/reversa-plan` | reversa |
