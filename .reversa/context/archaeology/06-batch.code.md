## Módulo `batch` (`src/sintetica/batch/`)

🟢 **Propósito:** geração do lote completo (1 a 10.000 registros), skill `sintetica-generate`. Escolhe o provedor pelo volume total, estima e autoriza o custo, pede os registros em blocos, revisa cada bloco, grava por bloco com durabilidade, retoma sem perda, roda em background acima de 100 registros, gera o arquivo final e chama a avaliação de qualidade.

### Arquivos

| Arquivo | Papel |
|---------|-------|
| `state.py` | `RunState` (7 status), caminhos de `output/`, `load_run_state`, `save_run_state`, constantes |
| `plan.py` | `avg_tokens`, `block_size` (adaptativo), `split` |
| `request.py` | `build_instructions`, `build_batch_request` (bloco b de B, rodada r de 4) |
| `review.py` | `DedupIndex` (SHA-256 em memória), `review_block`, `BlockReview` |
| `output.py` | `append_block` (fsync, truncamento), `load_partial` (linha incompleta), `convert_final` |
| `engine.py` | `BatchEngine`: rodadas, fila com N trabalhadores, caminho do harness, `finish`, `usd` |
| `lock.py` | `DatasetLock` (`fcntl.flock`/`msvcrt.locking`), `is_locked` |
| `background.py` | `start_background`, `worker_command`, `popen_options` |
| `worker.py` | Ponto de entrada `python -m sintetica.batch.worker` |
| `service.py` | `generate`, `status`, `run_worker`; pré-condições, custo, lote existente |

### Funções e métodos principais

| Função | Assinatura | Retorno | Local |
|--------|-----------|---------|-------|
| `generate` | `(project, slug, *, resume=False, new=False, authorize_usd=None, block_size_override=None, provider_factory=None, spawner=None, progress=None)` | `CommandResult` (0, 2, 9, 10, 11, 12, 14, 15, 16) | `service.py:509` |
| `status` | `(project, slug)` | `CommandResult` (0, 2, 16) | `service.py:609` |
| `run_worker` | `(project, slug, *, provider_factory=None, progress=None)` | `CommandResult` | `service.py:582` |
| `BatchEngine.run_automatic` | `(state, provider)` | `RunState` final | `engine.py:121` |
| `BatchEngine.run_harness` | `(state, provider, store)` | `RunState` (final ou `aguardando_agente`) | `engine.py:185` |
| `review_block` | `(raw, model, index, masker, limit)` | `BlockReview` | `review.py:56` |
| `block_size` | `(avg, override=None)` | `int` | `plan.py:23` |
| `append_block` | `(path, lines)` | — | `output.py:22` |
| `load_partial` | `(path, index)` | registros gravados | `output.py:44` |
| `convert_final` | `(src, dest, fmt, model)` | caminho do dataset | `output.py:82` |
| `start_background` | `(project, dataset_dir, slug, lock)` | PID | `background.py:36` |

### Algoritmos e regras

1. 🟢 **Pré-condições** (`service.py:112-176`): dataset e intenção (2); contrato aprovado e atual (11); `seeds/sample.meta.json` com a versão do contrato e `sample.jsonl` não vazio (14, cita `sample run`); volume definido na intenção (2).
2. 🟢 **Provedor pelo volume total** (`service.py:210-217`): a fábrica recebe o volume do lote, nunca o tamanho do bloco; acima de 100, o harness nunca é escolhido.
3. 🟢 **Custo e autorização** (`service.py:381-436`): tokens médios da amostra (4 caracteres por token); `estimate_cost(volume, média)`; com `requires_authorization` e sem `--authorize-usd`, termina com 15 sem nenhum pedido, citando o valor arredondado para cima em centavos (ou "preço desconhecido"); autorização abaixo da estimativa gera aviso; o valor autorizado (ou o teto da política) fica em `run.json`.
4. 🟢 **Teto na retomada** (`service.py:439-470`): o provedor recebe `autorizado − custo já gasto`; com saldo 0 e custo > 0, o lote termina como `interrompido_custo` sem chamar o provedor; a estimativa por pedido é `estimativa ÷ número de blocos`.
5. 🟢 **Bloco adaptativo** (`plan.py:23-29`): `min(10, max(1, 4000 // tokens médios))`; `--block-size` de 1 a 100 substitui (Q46).
6. 🟢 **Rodadas** (`engine.py:124-183`): 1ª rodada + até 3 extras, cada uma pedindo só os faltantes; fila de blocos atendida por até 8 trabalhadores; falha do provedor, teto atingido, falha de mascaramento ou de escrita param a fila (`asyncio.Event`); blocos em voo terminam; falha de mascaramento ou escrita é relançada depois do `gather`.
7. 🟢 **Status final** (`engine.py:58-75`): `concluido` com aceitos ≥ ⌈0,95 × volume⌉; `incompleto` abaixo disso; `interrompido_custo` com `stop_reason = "teto de custo"`; `falha_provedor` com `ProviderError`. Em todos, o arquivo final é gerado.
8. 🟢 **Revisão por bloco** (`review.py:56-90`): valida; duplicado pelo SHA-256 da linha bruta (só em memória) e da linha mascarada; mascara e revalida; aceita até o tamanho do bloco; registros além do pedido são ignorados.
9. 🟢 **Gravação durável** (`output.py:22-41`): anexa o bloco, `flush` e `fsync`; erro trunca o arquivo ao tamanho anterior. `run.json` é gravado depois, por `write_atomic`.
10. 🟢 **Retomada** (`output.py:44-69`): o arquivo parcial é a fonte da verdade; uma última linha sem quebra é cortada do arquivo; os aceitos são recontados e o índice de duplicados mascarados é reconstruído. A retomada zera o contador de rodadas.
11. 🟢 **Caminho do harness** (`engine.py:185-238`): 1 pedido com todos os faltantes por rodada, "bloco 1 de 1, rodada r de 4"; `HarnessResponsePending` grava `aguardando_agente`; a resposta lida é revisada e apagada.
12. 🟢 **Background** (`service.py:564-579`, `background.py`): volume > 100 grava `iniciando` e inicia `python -m sintetica.batch.worker` em sessão própria (POSIX `start_new_session`; Windows `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP`), entrada nula, saída em `worker.log`; o comando volta com o PID. O processo grava o próprio PID e muda para `em_andamento`.
13. 🟢 **Trava por dataset** (`lock.py`): `output/run.lock`; em POSIX, o pai abre a trava e o filho herda o descritor (`pass_fds`), e o pai fecha a sua cópia sem destravar; no Windows, o filho tenta pegar a trava por até 10 s. A trava some com o processo, então `status` detecta processo encerrado sem depender do PID.
14. 🟢 **Lote existente** (`service.py:329-378`): trava ocupada ou `iniciando` recente → 16 com o status; `aguardando_agente` → continua; contrato mudado → 16 sugerindo `--new`; `concluido` → 16 sugerindo `--new`; outros status sem `--resume` → 16 sugerindo `--resume` ou `--new`; `--resume` com `--authorize-usd` troca o teto total.
15. 🟢 **Conversão final** (`output.py:82-110`): em fluxo; JSONL copiado; JSON vira lista com 1 registro por linha; CSV com cabeçalho na ordem do contrato, `\r\n` e aspas pela RFC 4180; gravação por arquivo temporário e `os.replace`.
16. 🟢 **Avaliação no fim** (`service.py:505-509`): depois do arquivo final, `evaluate_after_lot` roda dentro da trava; o bloco da avaliação entra na saída; o código do `generate` não muda.
17. 🟢 **Privacidade do log** (`worker.py:46-50`): erro inesperado no background registra só o nome da exceção.

### Tratamento de erros

🟢 `_Fail(code, message)`; `MaskingFailed` (9, cita `--resume`); `BatchWriteError` (10); `RunStateError` (2, sugere `--new`); erro ao iniciar o processo (10).

### Constantes

| Constante | Valor | Local |
|-----------|-------|-------|
| `MAX_ROUNDS` | 4 | `state.py:22` |
| `MAX_BLOCK_OVERRIDE` | 100 | `state.py:23` |
| `CONFORMITY` | 0,95 | `state.py:24` |
| `TOKEN_TARGET`, `MAX_BLOCK` | 4000, 10 | `plan.py:11-12` |
| `BACKGROUND_ABOVE` | 100 | `service.py:70` |
| `STARTING_GRACE_S` | 10 s | `service.py:71` |
| Códigos próprios | 14, 15, 16 | `service.py:66-68` |

### Dependências

🟢 `providers`, `schema`, `intent`, `sample` (sementes, `review` e `CommandResult`), `pii`, `quality` (importação tardia), `fsutil`, `command`.
