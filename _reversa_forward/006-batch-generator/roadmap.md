# Roadmap: batch-generator (geração do lote completo)

> Identificador: `006-batch-generator`
> Data: `2026-10-12`
> Requirements: `_reversa_forward/006-batch-generator/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA
> Cenário: greenfield. Sem `architecture.md`, `c4-context.md`, `state-machines.md`, `dependencies.md` nem `code-analysis.md`. Adendos vigentes lidos: `addenda/001-pii-guard.md` a `addenda/005-sample-preview.md`.

## 1. Resumo da abordagem

🟡 A feature cria o pacote `sintetica.batch` e 2 comandos: `sintetica generate <slug>` e `sintetica status <slug>`. Ela não cria provedor, validador nem mascarador novos: escolhe o provedor por `build_provider` (002) com o volume total, valida com `load_record_model` (003), lê a intenção (004) e as sementes de `seeds/sample.jsonl` (005), e mascara com o `PiiGuard` (001).
🟡 O motor é o mesmo nos 3 modos de execução:
- **Harness (volume ≤ 100, Q44):** 1 pedido único com todo o volume; o protocolo em 2 passos da Q29 se repete a cada rodada, como na amostra.
- **Provedor automático em primeiro plano (volume ≤ 100):** blocos adaptativos (Q46) enviados com a concorrência do provedor.
- **Background (volume > 100, Q45):** o `generate` grava `run.json`, inicia um processo separado em sessão própria e devolve o controle; o processo roda o mesmo motor.
🟡 O arquivo `output/records.partial.jsonl` é a fonte da verdade do progresso: cada bloco aceito é anexado com `fsync` antes de `run.json` ser atualizado. A retomada (`--resume`) reconta o arquivo e pede só o restante.
🟡 No fim, o motor converte o arquivo parcial em `output/dataset.<ext>` e indica a avaliação de qualidade como próximo passo (Q40).

## 2. Princípios aplicados

🟡 `.reversa/principles.md` não existe. Sem princípios formais para verificar.

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| n/a | Arquivo de princípios ausente | n/a |

🟡 Restrições do PRD tratadas como princípios de fato:
- privacidade por design (Q21): mascaramento antes do disco, sem resposta bruta no disco;
- custo controlado (Q17): autorização acima do teto, teto respeitado;
- tipagem estrita e cobertura ≥ 80% (Q19);
- portabilidade macOS, Linux e Windows (`cli-installer.md`, RNF-04).

Todas são respeitadas.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Novo pacote `sintetica.batch` (`state.py`, `plan.py`, `request.py`, `review.py`, `engine.py`, `output.py`, `lock.py`, `background.py`, `worker.py`, `service.py`) | Mesma organização por componente das features 001 a 005 | Estender `sintetica.sample` | 🟡 |
| D-02 | Pré-condições na ordem: dataset e intenção (código 2), contrato aprovado e atual (11, mesmas mensagens da amostra), `seeds/sample.meta.json` com `schema_version` igual à do contrato (14, cita `sintetica sample run`), volume e formato definidos na intenção (2) | RN-01, RF-01, RF-02 | Aceitar amostra de versão antiga | 🟢 |
| D-03 | Provedor por `build_provider(volume_total, harness_available=True, authorized_usd=…, per_request_estimate=…)`. O volume total decide; nunca o tamanho do bloco | RN-02, RF-03; `select_provider` decide por `n_records` (adendo 002) | Escolher por bloco (lote de 10.000 iria inteiro para o harness em blocos de 10) | 🟢 |
| D-04 | Harness: 1 pedido com o volume inteiro (≤ 100) e as sementes; cada rodada extra pede só os faltantes; as instruções levam "rodada r de 4" para o id ser novo; `HarnessResponsePending` vira o estado `aguardando_agente` com o comando `submit` (código 0); a resposta bruta é apagada depois de lida | RN-03 (Q44), padrão da amostra (adendo 005, W006) | Blocos de 10 no harness (10 voltas para 100 registros) | 🟢 |
| D-05 | Bloco adaptativo para provedor automático: `avg = média de estimate_tokens(linha)` sobre `seeds/sample.jsonl`; `bloco = min(10, max(1, 4000 // avg))`; `--block-size N` (1 a 100) substitui o cálculo; o bloco escolhido fica em `run.json` e vale na retomada | RN-06 (Q46); `estimate_tokens` já existe (002, 4 caracteres por token) | Bloco fixo de 10 | 🟢 |
| D-06 | Custo: `estimate_cost(restante, avg)` antes do 1º pedido. Com `requires_authorization` e sem `--authorize-usd`: código 15, 0 pedidos, saída com valor (ou "preço desconhecido") e o comando com `--authorize-usd <valor>`. O valor autorizado fica em `run.json`; na retomada, o teto passado ao `build_provider` é `autorizado − custo já gasto` | RN-04, RF-04, RF-05, D-24 da feature 002 | Perguntar dentro do comando (o agente é quem pergunta ao usuário) | 🟢 |
| D-07 | `per_request_estimate = estimativa / número de pedidos da 1ª rodada` quando o preço é conhecido; senão `None` (o `BudgetedProvider` mede o 1º pedido sozinho) | Evita estourar o teto com 8 pedidos simultâneos antes do 1º custo real | Sempre `None` | 🟡 |
| D-08 | Motor assíncrono com fila de blocos e N trabalhadores (N = concorrência do provedor, 8); um evento de parada interrompe a fila em falha do provedor, teto atingido ou falha de mascaramento; blocos já em voo terminam e são gravados | RF-15, EC-01, EC-02; Python 3.10 não tem `TaskGroup` | `asyncio.gather` de todos os blocos (não para de enviar após uma falha) | 🟡 |
| D-09 | Revisão por bloco em `sintetica.batch.review`, com a mesma ordem da amostra: validar, descartar duplicado, mascarar, revalidar, descartar duplicado mascarado. Duplicados por SHA-256 do JSON canônico (RF-05 da spec): índice em memória de hashes das linhas mascaradas (reconstruído do arquivo parcial na retomada) e de hashes das linhas brutas (só em memória, nunca no disco) | RN-07, RN-08; memória de 10.000 registros ≈ 1 MB de hashes | Guardar as linhas inteiras no índice; reusar `review_records` (copia `existing` a cada chamada) | 🟡 |
| D-10 | Expor em `sintetica.sample.review` as funções `first_error` e `mask_value` (hoje `_first_error` e `_mask`), sem mudar `review_records` | D-09 reusa a mesma lógica de mascaramento por caminho de campo | Duplicar o código | 🟡 |
| D-11 | Instruções do lote: as linhas de objetivo, estrutura e regras vêm de uma função comum extraída de `sintetica.sample.request` (`intent_lines`); somam "bloco b de B, rodada r de 4" e "não repita os exemplos"; sementes = `seeds/sample.jsonl` (≤ 5 registros) | RF-06; o número do bloco varia o pedido e reduz respostas iguais | Mandar os aceitos como sementes (prompt cresce sem limite) | 🟡 |
| D-12 | Gravação por bloco: anexar as linhas aceitas a `records.partial.jsonl`, `flush` e `os.fsync`; depois, `run.json` por `write_atomic`. Erro de escrita trunca o parcial para o tamanho anterior ao bloco e termina com código 10 | RN-09, RF-09, RNF-05, EC-05 | Gravar só no fim | 🟢 |
| D-13 | Retomada: o arquivo parcial é a fonte da verdade; uma última linha incompleta é descartada; os aceitos são recontados e o índice de duplicados é reconstruído; os blocos restantes são recalculados com o bloco salvo | RN-09, RF-10; queda entre o `fsync` e o `run.json` não duplica nada | Confiar nas contagens de `run.json` | 🟡 |
| D-14 | Rodadas: 1ª rodada + até 3 rodadas extras, cada uma pedindo os faltantes. Status final: `concluido` com aceitos ≥ 95% do volume; `incompleto` abaixo disso após as rodadas; `interrompido_custo` com `stop_reason = "teto de custo"`; `falha_provedor` com `ProviderError`. Em todos, o arquivo final é gerado | RN-07, RN-10, RF-08 | Rodadas ilimitadas | 🟢 |
| D-15 | Background para volume > 100: o `generate` grava `run.json` (`em_andamento`) e inicia `sys.executable -m sintetica.batch.worker <projeto> <slug>` com `start_new_session=True` (POSIX) ou `DETACHED_PROCESS \| CREATE_NEW_PROCESS_GROUP` (Windows), entrada nula e saída em `output/worker.log`; grava o PID e devolve o controle em ≤ 5 s com o comando de status | RN-05, RF-11 (Q45) | Fatias curtas a cada chamada do agente | 🟢 |
| D-16 | Trava por dataset em `output/run.lock` (`fcntl.flock` em POSIX, `msvcrt.locking` no Windows). Em POSIX, o processo pai abre a trava e o filho a herda por `pass_fds`; o pai fecha a sua cópia. No Windows, o filho pega a trava em até 10 s, e o estado `iniciando` cobre essa janela | RN-11, RF-12, EC-04, EC-06; a trava some com o processo, sem risco de PID reutilizado | Só checar o PID (PID pode ser reutilizado) | 🟡 |
| D-17 | `sintetica status <slug>`: mostra status, aceitos/volume, descartados (inválidos e duplicados), custo, provedor, bloco, rodada e caminhos; com `em_andamento` e a trava livre, informa "processo encerrado" e sugere `--resume` | RF-09, RF-11, EC-04 | Status só pelo PID | 🟢 |
| D-18 | `generate` com lote existente: `em_andamento` com trava ocupada → código 16 com o status; `aguardando_agente` → continua o pedido do harness; `em_andamento` sem trava ou `falha_provedor` → código 16 sugerindo `--resume`; status final → código 16 sugerindo `--new` (que apaga `output/` e começa de novo) | RN-11; evita sobrescrever um dataset pronto sem pedido explícito | Sobrescrever sempre | 🟡 |
| D-19 | Conversão final por fluxo, sem carregar o lote na memória: JSONL é copiado; JSON vira lista `[\n…\n]` com as linhas já canônicas; CSV relê cada linha (`parse_line` + `Record`) e grava com `csv.writer` (`lineterminator="\r\n"`, UTF-8, cabeçalho `csv_columns`). Grava em arquivo temporário e troca por `os.replace` | RF-13, RNF-06, Q35, Q37 | Montar a lista em memória | 🟢 |
| D-20 | Códigos de saída novos: 14 (amostra ausente ou de outra versão), 15 (custo exige autorização), 16 (lote em andamento ou existente). Reuso: 0, 2, 9 (mascaramento indisponível), 10 (escrita), 11 (contrato), 12 (falha do provedor, também no status final `falha_provedor`) | Sem colisão com 3 a 13 | Reusar o 13 da amostra | 🟡 |
| D-21 | Primeiro plano imprime 1 linha por bloco por um callback (`Bloco 7/10, 68 válidos, 2 descartados, US$ 0,00`); o background grava a mesma linha em `worker.log`, sem valores de registro | Spec §8; o log nunca contém PII | Silêncio até o fim | 🟡 |
| D-22 | A saída de `sample approve` passa a indicar `uv run sintetica generate <slug>` como próximo passo; a saída final do `generate` indica a avaliação de qualidade (feature `quality-evaluator`), sem comando | RN-12, RF-14, RF-16, Q40 | Comando fictício para a avaliação | 🟢 |
| D-23 | Testes do background com processo real: um servidor HTTP local no formato do Ollama (`OLLAMA_HOST` apontado para ele) responde aos pedidos; nenhum gancho de teste no código de produção | RNF de testabilidade sem rede externa | Variável de ambiente que troca o provedor | 🟡 |

> 🟢 nas decisões confirmadas por respostas do revisor (Q17, Q35, Q37, Q40, Q44, Q45, Q46) ou por código entregue (adendos 001 a 005).

## 4. Premissas

🟡 Nenhuma premissa vinda de `[DÚVIDA]`: o `requirements.md` está com 0 marcadores após o clarify.

| Premissa | Origem (`requirements.md` seção) | Risco se errada |
|----------|----------------------------------|-----------------|
| A heurística de 4 caracteres por token basta para dimensionar o bloco | 4. RN-06 | Bloco grande demais trunca a resposta; o `MalformedResponse` aciona o retry e as rodadas extras repõem os faltantes |
| O harness não encerra um processo filho em sessão própria ao fim do comando | 4. RN-05 (Q45) | O lote para; `status` detecta e `--resume` continua (D-16, D-17) |
| O volume da intenção fica entre 1 e 10.000 (`MAX_VOLUME` da feature 004) | 5. RF-02 | Volume fora disso já é recusado pela intenção |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `sintetica.batch` | `_reversa_sdd/sdd/batch-generator.md` | componente-novo | Estado, plano de blocos, pedido, revisão, motor, saída, trava, background e serviço |
| `sintetica.sample.review` | `_reversa_sdd/addenda/005-sample-preview.md` | contrato-alterado | `first_error` e `mask_value` públicos; `review_records` inalterado (D-10) |
| `sintetica.sample.request` | `_reversa_sdd/addenda/005-sample-preview.md` | contrato-alterado | `intent_lines` extraída; `build_instructions` com a mesma saída (D-11) |
| `sintetica.sample.service` | `_reversa_sdd/addenda/005-sample-preview.md` | contrato-alterado | Texto do próximo passo na aprovação (D-22) |
| `sintetica.cli` | `_reversa_sdd/addenda/004-intent-interview.md` (comando `sintetica`) | contrato-alterado | Comandos `generate` e `status`; demais inalterados |
| `sintetica.providers`, `sintetica.pii`, `sintetica.intent`, `sintetica.schema` | adendos 001 a 004 | sem mudança | Consumidos pelas APIs públicas |

Estrutura de arquivos prevista:

```
src/sintetica/batch/__init__.py
src/sintetica/batch/state.py       # RunState, leitura e gravação atômica
src/sintetica/batch/plan.py        # tamanho médio, bloco adaptativo, divisão em blocos (D-05)
src/sintetica/batch/request.py     # instruções e GenerationRequest do lote (D-11)
src/sintetica/batch/review.py      # revisão por bloco e índice de duplicados (D-09)
src/sintetica/batch/engine.py      # fila, trabalhadores, rodadas, gravação por bloco (D-08, D-12 a D-14)
src/sintetica/batch/output.py      # parcial, retomada e conversão final (D-12, D-13, D-19)
src/sintetica/batch/lock.py        # trava por dataset (D-16)
src/sintetica/batch/background.py  # início do processo separado (D-15)
src/sintetica/batch/worker.py      # ponto de entrada do processo separado
src/sintetica/batch/service.py     # generate e status (D-02 a D-07, D-17, D-18, D-20 a D-22)
src/sintetica/sample/review.py     # first_error e mask_value públicos
src/sintetica/sample/request.py    # intent_lines
src/sintetica/sample/service.py    # próximo passo na aprovação
src/sintetica/cli.py               # comandos generate e status
tests/batch/…
docs/batch-generator.md
```

## 6. Delta no modelo de dados

- Resumo das mudanças: 🟡 `datasets/<slug>/output/` novo, com `run.json`, `records.partial.jsonl`, `dataset.<ext>`, `run.lock` e `worker.log`; pedidos do harness em `requests/` (formato da feature 002).
- Detalhe completo em: `_reversa_forward/006-batch-generator/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| `sintetica generate` e `sintetica status` | arquivo + CLI | `_reversa_forward/006-batch-generator/interfaces/generate-cli.md` |

## 8. Plano de migração

n/a. Arquivos novos. As mudanças em `sintetica.sample` só expõem funções e trocam 1 linha de texto; `sintetica.cli` só ganha 2 comandos.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| R-01: Pedidos iguais geram muitos duplicados exatos | médio | médio | Número do bloco e da rodada nas instruções (D-11); duplicados repostos nas rodadas extras; diversidade semântica fica com o `quality-evaluator` |
| R-02: Custo real acima do estimado (a estimativa só conta a saída) | médio | médio | `BudgetedProvider` com o valor autorizado; status `interrompido_custo` com o arquivo final (D-06, D-14) |
| R-03: Queda entre a gravação do bloco e o `run.json` | alto | baixo | Arquivo parcial como fonte da verdade e linha incompleta descartada (D-13); teste com queda simulada |
| R-04: 2 lotes no mesmo dataset | alto | baixo | Trava herdada pelo processo filho (D-16); teste com 2 chamadas |
| R-05: PII no disco (resposta bruta, log, índice de duplicados) | alto | médio | Mascarar antes de anexar; apagar a resposta do harness; log só com contagens; hashes brutos só em memória; teste que busca o CPF original em todos os arquivos |
| R-06: Processo em background difere entre sistemas | médio | médio | D-15 e D-16 com ramos POSIX e Windows; testes reais em POSIX; ramo Windows coberto por teste de unidade dos argumentos |
| R-07: Memória acima de 500 MB em 10.000 registros | médio | baixo | Escrita e conversão em fluxo; índice só de hashes (D-09, D-19); teste `perf` com `tracemalloc` |
| R-08: Bloco adaptativo pequeno demais encarece o lote (mais entrada repetida) | baixo | baixo | Teto de 10 e mínimo de 1; `--block-size` para ajuste manual |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Re-extração reversa executada e sem regressão vermelha (recomendado, não obrigatório)
- [ ] `mypy --strict` e `ruff` sem erros no projeto
- [ ] Cobertura ≥ 80% em `sintetica.batch`
- [ ] Os 17 cenários Gherkin do `requirements.md` cobertos por testes, com o protocolo real do harness e um processo real em background
- [ ] Os 412 testes das features 001 a 005 continuam passando

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-12 | Versão inicial gerada por `/reversa-plan` | reversa |
