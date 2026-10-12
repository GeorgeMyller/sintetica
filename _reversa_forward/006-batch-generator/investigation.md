# Investigation: batch-generator

> Identificador: `006-batch-generator`
> Data: `2026-10-12`
> Fonte: `_reversa_forward/006-batch-generator/roadmap.md`

## 1. Pesquisa de fundo (código entregue)

### 1.1 `build_provider` e a pilha de decoradores (feature 002)
- 🟢 `build_provider(n_records, dataset_dir, project_dir, harness_available, authorized_usd, per_request_estimate, …)` escolhe pela política e devolve `(provedor, ProviderChoice)`.
- 🟢 `select_provider` pula o harness quando `n_records > MAX_HARNESS_RECORDS` (100). Por isso o `n_records` passado precisa ser o volume total (D-03).
- 🟢 Pilha para provedor automático: `RetryingProvider` (3 chamadas) → `MaskingProvider` (com `pii_premask`, inclusive Ollama) → `ConcurrencyLimitedProvider` (8) → `BudgetedProvider`.
- 🟢 `BudgetedProvider` reserva o custo previsto antes de cada pedido; sem estimativa, o 1º pedido sai sozinho. Ao passar do teto, devolve resultado vazio com `stop_reason = "teto de custo"` e `stopped = True`; `spent_usd` dá o custo acumulado.
- 🟢 `estimate_cost(n, avg_tokens)` só conta tokens de saída (`n × avg × preço de saída`). Preço desconhecido devolve `requires_authorization = True` e `price_known = False`.
- 🟢 `estimate_tokens(texto)` usa 4 caracteres por token.
- 🟢 O `AnthropicBackend` pede `max_tokens = 8192`; o alvo de 4.000 tokens por bloco (Q46) fica abaixo desse limite.

### 1.2 `HarnessAgentProvider` (feature 002)
- 🟢 O id do pedido é o SHA-256 do pedido canônico; pedido igual devolve a resposta antiga.
- 🟢 `HarnessLimitExceeded` acima de 100 registros por pedido.
- 🟢 A resposta bruta (`<id>.response.jsonl`) mantém PII; a amostra a apaga depois de ler (W006).

### 1.3 Amostra (feature 005)
- 🟢 `seeds/sample.jsonl` com linhas de `to_jsonl_line`; `seeds/sample.meta.json` com `schema_version`.
- 🟢 `review_records` valida, descarta duplicado, mascara campo a campo com o caminho e revalida. Ele copia `existing` para um conjunto a cada chamada; para 10.000 registros em 1.000 blocos, isso seria caro. Daí a revisão própria por bloco (D-09), com as mesmas funções de base (D-10).
- 🟢 `_context` já faz as checagens de contrato com as mensagens e o código 11.

### 1.4 Contrato e intenção (features 003 e 004)
- 🟢 `to_jsonl_line`, `to_csv_row`, `csv_columns`, `parse_line` com `Decimal`.
- 🟢 `IntentModel.volume` entre `MIN_VOLUME` e `MAX_VOLUME`; `format` em `csv`, `json` ou `jsonl`.

## 2. Alternativas avaliadas

### 2.1 Execução sem prender o chat (Q45)
| Alternativa | Prós | Contras | Decisão |
|-------------|------|---------|---------|
| Processo separado em sessão própria | Comando volta em < 5 s; lote segue sem o agente | Harness pode encerrar o processo; diferenças entre POSIX e Windows | Escolhida (Q45), com `status` e `--resume` como recuperação |
| Fatias curtas a cada chamada | Funciona em qualquer harness | Agente precisa chamar dezenas de vezes; lote para quando o chat para | Descartada |

### 2.2 Detecção de processo vivo
| Alternativa | Prós | Contras | Decisão |
|-------------|------|---------|---------|
| Trava de arquivo (`flock` / `msvcrt.locking`) | Some com o processo; imune a PID reutilizado | Janela de herança no Windows | Escolhida (D-16) |
| PID e `os.kill(pid, 0)` | Simples | PID reutilizado dá falso positivo; não funciona igual no Windows | Só informativo |
| Batimento periódico em `run.json` | Portável | Precisa de limiar de tempo; blocos lentos parecem mortos | Descartada |

### 2.3 Concorrência dos blocos
| Alternativa | Prós | Contras | Decisão |
|-------------|------|---------|---------|
| Fila com N trabalhadores e evento de parada | Para de enviar após falha ou teto | Um pouco mais de código | Escolhida (D-08) |
| `asyncio.gather` de todos os blocos | Simples | Continua enviando após falha; 1.000 tarefas de uma vez | Descartada |
| `asyncio.TaskGroup` | Cancelamento estruturado | Exige Python 3.11; o projeto aceita 3.10 | Descartada |

### 2.4 Índice de duplicados
| Alternativa | Memória (10.000 × 1 KB) | Decisão |
|-------------|--------------------------|---------|
| Linhas inteiras | ≈ 10 MB | Descartada |
| SHA-256 (32 bytes) das linhas mascaradas e brutas | ≈ 1 MB | Escolhida (D-09); hashes brutos nunca vão ao disco |

## 3. Padrões aplicáveis

- 🟡 Escrita durável: anexar, `flush`, `os.fsync`; metadados por arquivo temporário e `os.replace` (`sintetica.fsutil.write_atomic`).
- 🟡 CSV pela RFC 4180: módulo `csv` com `lineterminator="\r\n"` e aspas mínimas.
- 🟡 Processo desligado: `subprocess.Popen(..., start_new_session=True, stdin=DEVNULL)` em POSIX; `creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP` no Windows.

## 4. Fontes externas

- Python, `subprocess.Popen` (`start_new_session`, `pass_fds`, `creationflags`): https://docs.python.org/3/library/subprocess.html
- Python, `fcntl.flock`: https://docs.python.org/3/library/fcntl.html
- Python, `msvcrt.locking`: https://docs.python.org/3/library/msvcrt.html
- RFC 4180, formato CSV: https://www.rfc-editor.org/rfc/rfc4180
