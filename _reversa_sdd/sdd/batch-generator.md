# Spec: batch-generator

> Selo 🟢 CONFORME CÓDIGO em todos os itens, salvo marcação. Fonte: `src/sintetica/batch/`, testes `tests/batch/` (inclui processo real em background e `-m perf`).
> Consolida os adendos `006-batch-generator.md`, `007-quality-evaluator.md` (avaliação no fim, veredito no `status`) e `008-cli-installer.md` (mensagens). Versão planejada em `sdd/_planejado/batch-generator.md`.

**Versão:** 2.0 (extraída do código)
**Status:** Implementado
**Autor:** reversa-writer
**Data:** 2026-10-12

---

## 1. Resumo

🟢 O `batch-generator` é o pacote `sintetica.batch` e a skill `sintetica-generate`. `sintetica generate <slug>` gera o lote (1 a 10.000 registros): escolhe o provedor pelo volume total, estima o custo e exige autorização acima do teto, pede os registros em blocos adaptativos (ou 1 pedido por rodada ao harness), valida, descarta duplicados, mascara, grava cada bloco com `fsync`, retoma sem perda, roda em background acima de 100 registros com trava por dataset, gera `output/dataset.<ext>` e roda a avaliação de qualidade. `sintetica status <slug>` mostra o progresso.

## 2. Contexto

🟢 Lotes de 1.000 a 10.000 registros são lentos e frágeis; o PRD exige ≥ 95% de conformidade e 0 perda após interrupção (Q10, Q28).

## 3. Goals

- 🟢 G-01: ≥ 95% do volume com registros válidos (status `concluido`).
- 🟢 G-02: 0 registros perdidos após interrupção.
- 🟢 G-03: 0 registros gravados sem mascaramento.
- 🟢 G-04: Custo acumulado ≤ valor autorizado.

## 4. Non-Goals

- 🟢 NG-01: Sem lotes acima de 10.000; sem execução distribuída; sem Parquet ou XLSX.

## 5. Usuários

🟢 As 3 personas (pelo agente); `quality` (lê `output/`).

## 6. Requisitos Funcionais

| ID | Requisito | Critério de aceite | Fonte |
|----|-----------|--------------------|-------|
| RF-01 | 🟢 Pré-condições: dataset e intenção (2); contrato aprovado e atual (11); `seeds/sample.meta.json` com a versão do contrato e `sample.jsonl` não vazio (14, cita `sample run`); volume definido (2) | — | `service.py:112-176` |
| RF-02 | 🟢 Provedor escolhido pelo volume total, nunca pelo bloco | 1.000 registros com o harness disponível vão a Ollama ou API | `service.py:210-217` |
| RF-03 | 🟢 Tokens médios da amostra (4 caracteres/token); bloco = `min(10, max(1, 4000 // média))`; `--block-size` de 1 a 100 substitui | Registros de ~1.000 tokens = blocos de 4 (Q46) | `plan.py` |
| RF-04 | 🟢 Estimativa antes do 1º pedido; com `requires_authorization` e sem `--authorize-usd`: código 15, 0 pedidos, valor arredondado para cima em centavos (ou "preço desconhecido") e o comando; autorização abaixo da estimativa gera aviso | — | `service.py:381-436` |
| RF-05 | 🟢 Teto passado ao provedor = autorizado − custo já gasto; saldo 0 com custo > 0 encerra como `interrompido_custo` sem chamar o provedor; estimativa por pedido = estimativa ÷ número de blocos | — | `service.py:439-470` |
| RF-06 | 🟢 Rodadas: 1ª + até 3 extras, cada uma só com os faltantes; instruções com "bloco b de B, rodada r de 4" e as sementes da amostra | — | `engine.py:124-183`, `request.py` |
| RF-07 | 🟢 Fila de blocos com até 8 trabalhadores; falha do provedor, teto, falha de mascaramento ou de escrita param a fila; blocos em voo terminam | — | `engine.py:135-183` |
| RF-08 | 🟢 Revisão por bloco: valida; duplicado por SHA-256 da linha bruta (só em memória) e da mascarada; mascara e revalida; até o tamanho do bloco | — | `review.py` |
| RF-09 | 🟢 Gravação: anexa o bloco a `output/records.partial.jsonl` com `flush` e `fsync`; erro trunca ao tamanho anterior (código 10); depois grava `run.json` | — | `output.py:22-41`, `engine.py:95-111` |
| RF-10 | 🟢 Status final: `concluido` (≥ ⌈0,95 × volume⌉), `incompleto`, `interrompido_custo`, `falha_provedor`; em todos, gera o arquivo final | `falha_provedor` termina com 12 | `engine.py:58-75`, `service.py:506-507` |
| RF-11 | 🟢 Harness (≤ 100): 1 pedido por rodada com todos os faltantes; `aguardando_agente` com o comando `submit`; a resposta lida é revisada e apagada; `generate` de novo continua | Q44 | `engine.py:185-238` |
| RF-12 | 🟢 Background (> 100): grava `iniciando`, inicia `python -m sintetica.batch.worker` em sessão própria (POSIX `start_new_session`, Windows `DETACHED_PROCESS \| CREATE_NEW_PROCESS_GROUP`), entrada nula, saída em `output/worker.log`; volta com o PID em ≤ 5 s; o processo grava o próprio PID | Q45 | `service.py:564-579`, `background.py`, `worker.py` |
| RF-13 | 🟢 Trava `output/run.lock` (`fcntl.flock`/`msvcrt.locking`); em POSIX o filho herda o descritor (`pass_fds`) e o pai fecha sem destravar; no Windows o filho pega a trava em até 10 s | 2º `generate` com a trava ocupada = 16 | `lock.py`, `background.py:36-58` |
| RF-14 | 🟢 Lote existente: `aguardando_agente` continua; contrato mudado ou `concluido` = 16 sugerindo `--new`; outros sem `--resume` = 16 sugerindo `--resume` ou `--new`; `--resume` sem lote = 16; `--resume` e `--new` juntos = 2 | — | `service.py:329-378`, `509-561` |
| RF-15 | 🟢 Retomada: reconta o arquivo parcial (corta linha incompleta), reconstrói o índice de duplicados mascarados, zera as rodadas; `--resume --authorize-usd X` troca o teto total | — | `output.py:44-69`, `service.py:362-378` |
| RF-16 | 🟢 `--new` apaga os arquivos de `output/` (menos a trava) e começa de novo | — | `service.py:320-326` |
| RF-17 | 🟢 Conversão final em fluxo: JSONL copiado; JSON em lista com 1 registro por linha; CSV com cabeçalho na ordem do contrato, `\r\n` e aspas pela RFC 4180; arquivo temporário e `os.replace` | — | `output.py:82-110` |
| RF-18 | 🟢 Avaliação no fim, dentro da trava: o bloco da avaliação entra na saída (e no `worker.log`); erro vira aviso com o comando `eval`; o código do `generate` não muda | Q49 | `service.py:505-509` |
| RF-19 | 🟢 `status <slug>`: status, modo, PID, aceitos/volume, descartados, custo/autorizado, provedor, bloco, rodada, causa, arquivos; "Processo encerrado" + `--resume` quando `em_andamento`/`iniciando` (> 10 s) e a trava está livre; linha "Avaliação: <veredito>" com `report.json` | Sem lote = 16 | `service.py:246-282`, `609-620` |
| RF-20 | 🟢 Primeiro plano: 1 linha de progresso por bloco (`Bloco b/B (rodada r), N válidos, D descartados, US$ x,xx`) | — | `engine.py:113-118` |
| RF-21 | 🟢 Erro inesperado no background registra só o nome da exceção | — | `worker.py:46-50` |

## 7. Requisitos Não-Funcionais

| ID | Requisito | Evidência |
|----|-----------|-----------|
| RNF-01 | 🟢 Durabilidade: `fsync` por bloco; arquivo parcial como fonte da verdade | `output.py` |
| RNF-02 | 🟢 Memória: escrita e conversão em fluxo; índice só de hashes | Teste `perf` com 10.000 registros (~5 s, < 500 MB) |
| RNF-03 | 🟢 Concorrência: 8 pedidos simultâneos | `providers/decorators/concurrency.py` |
| RNF-04 | 🟢 Privacidade: log sem valores; resposta bruta apagada | `worker.py`, `engine.py:190-206` |
| RNF-05 | 🟡 Portabilidade Windows experimental até haver teste real em CI (Q53) | `lock.py`, `background.py` |

## 8. Interface

```
uv run sintetica generate <slug> [--resume] [--new] [--authorize-usd 6.00] [--block-size 1..100]
uv run sintetica status <slug>
```

| Código | Significado |
|--------|-------------|
| 0 | Sucesso, aguardando o agente, background iniciado, `concluido`, `incompleto`, `interrompido_custo` |
| 2 | Dataset, intenção ou argumento inválido; `run.json` ilegível (sugere `--new`) |
| 9 | Mascaramento indisponível (bloco não gravado; sugere `--resume`) |
| 10 | Falha de escrita |
| 11 | Contrato não aprovado ou desatualizado |
| 12 | Falha do provedor (inclui `falha_provedor`) |
| 14 | Amostra ausente ou de outra versão |
| 15 | Custo exige autorização |
| 16 | Lote em andamento, interrompido ou existente |

## 9. Modelo de Dados

🟢 `RunState` (`output/run.json`, 7 status), `records.partial.jsonl`, `dataset.<ext>`, `run.lock`, `worker.log`. Detalhe em `data-dictionary.md#módulo-batch` e `state-machines.md#4`.

## 10. Integrações

🟢 `providers`, `schema`, `intent`, `sample` (sementes, `review`, `CommandResult`), `pii`, `quality` (importação tardia).

## 11. Edge Cases

| Cenário | Comportamento |
|---------|---------------|
| 🟢 Queda no meio da escrita | Linha incompleta cortada na retomada |
| 🟢 Processo morto | `status` detecta pela trava; `--resume` continua |
| 🟢 Disco cheio | Bloco truncado; código 10 |
| 🟢 Custo real acima do estimado | Teto contém; `interrompido_custo` |
| 🟢 Registro igual a uma semente | Aceito (a amostra fica fora do lote) |
| 🟡 Duplicado com PII depois de uma retomada | Pode passar (hash bruto só em memória) |

## 12. Segurança

- 🟢 Nenhum registro vai ao disco sem mascaramento e revalidação.

## 13. Decisões (consolidadas)

| Decisão | Fonte |
|---------|-------|
| 🟢 Lote durável com retomada | ADR 010 |
| 🟢 Provedor pelo volume; harness com 1 pedido por rodada; bloco adaptativo | Q44, Q46, ADR 011 |
| 🟢 Background com trava de arquivo | Q28, Q45, ADR 012 |
| 🟢 Teto e autorização | Q17, ADR 013 |
| 🟢 Avaliação no fim do lote | Q49, ADR 014 |

## 14. Lacunas

- 🟡 Ramo Windows experimental: sem teste real até existir um runner Windows em CI (Q53).
- 🟡 Checagem do contrato duplicada com `sample`; `CommandResult` emprestado de `sample`.

## Histórico

| Versão | Data | Mudança |
|--------|------|---------|
| 1.0 | 2026-10-09 | Spec planejada (`_planejado/`) |
| 2.0 | 2026-10-12 | Reescrita conforme o código; adendos 006, 007 e 008 consolidados |
