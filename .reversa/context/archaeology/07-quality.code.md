## Módulo `quality` (`src/sintetica/quality/`)

🟢 **Propósito:** avaliação de qualidade do dataset final (skill `sintetica-eval`). Mede conformidade, unicidade estrutural, unicidade semântica e vazamentos de PII; calcula a duração desde `started_at`; dá o veredito e grava `report.json` e `report.md`. Roda sozinha no fim do lote ou pelo comando `sintetica eval`. 100% local; não altera o dataset.

### Arquivos

| Arquivo | Papel |
|---------|-------|
| `reader.py` | `read_items`: leitura em fluxo de JSONL, lista JSON e CSV; `csv_record`; `Item`; `DatasetReadError` |
| `text.py` | `has_free_text`, `free_text`, `normalize`, `shingles` (3-gramas de palavras) |
| `semantic.py` | `similar` (Jaccard ≥ 0,8 em inteiros), `near_duplicates` (par a par ou filtro de prefixo) |
| `metrics.py` | `collect`, `pct`, `string_leaves`, `duration_min`, `time_target_met`, `verdict` |
| `report.py` | `Report` e submodelos, `write_report`, `render_markdown`, `metric_lines`, `headline`, `load_report` |
| `service.py` | `evaluate`, `evaluate_after_lot`; pré-condições e montagem do relatório |

### Funções e métodos principais

| Função | Assinatura | Retorno | Local |
|--------|-----------|---------|-------|
| `evaluate` | `(project, slug, *, clock=None)` | `CommandResult` (0, 2, 9, 10, 11, 16, 17, 18) | `service.py:244` |
| `evaluate_after_lot` | `(project, slug, *, clock=None)` | linhas da saída ou aviso | `service.py:253` |
| `read_items` | `(path, fmt, model, spec)` | `Iterator[Item]` | `reader.py:106` |
| `collect` | `(items, spec, leaks)` | `Stats` | `metrics.py:66` |
| `near_duplicates` | `(sets, *, force_prefix=False)` | posições quase-duplicadas | `semantic.py:65` |
| `verdict` | `(conformity, structural, semantic, leaks)` | `(veredito, métricas que falharam)` | `metrics.py:117` |
| `write_report` | `(dataset_dir, report)` | `(report.json, report.md)` | `report.py:180` |

### Algoritmos e regras

1. 🟢 **Pré-condições** (`service.py:83-112`, `147-160`): dataset e intenção (2); `schema.json` e `Record` legíveis (11); com a verificação de trava (só no comando avulso), lote em andamento dá 16; `output/dataset.<ext>` ausente dá 18; `PiiGuard` indisponível dá 9; `run.json` ilegível vira aviso.
2. 🟢 **Leitura** (`reader.py`): JSONL por linha, linhas vazias ignoradas, linha que não é JSON fica inválida; lista JSON lida inteira com decimal exato (arquivo que não é lista dá 18); CSV pelo `csv.reader`, com número de células comparado ao cabeçalho (colunas a mais ou a menos ficam inválidas) e conversão pelo contrato plano (vazio → `None`, ou `[]` em lista; lista dividida por `|`). Cada item tem o índice (a partir de 0), o registro válido ou o motivo, e a linha canônica (válido) ou bruta (inválido).
3. 🟢 **Conformidade** (`service.py:197`): `min(válidos, volume) ÷ volume`, com 1 casa (`ROUND_HALF_UP`). O volume vem de `run.json`; sem ele, da intenção; volumes diferentes geram aviso.
4. 🟢 **Unicidade estrutural** (`metrics.py:73-80`): SHA-256 da linha canônica; cópias exatas entram em `problem_indices.duplicates`; `(lidos − duplicados) ÷ lidos`.
5. 🟢 **Texto livre** (`text.py`): campos `text` do contrato, inclusive em listas e objetos, na ordem do contrato; numa conversa, o conteúdo das mensagens mais os campos `text` dos rótulos; `enum`, números e datas ficam fora. Normalização: minúsculas, pontuação Unicode (categoria P) vira espaço, espaços únicos. 3-gramas de palavras; menos de 3 palavras vira 1 trecho (Q47).
6. 🟢 **Quase-duplicados** (`semantic.py`): Jaccard ≥ 0,8 calculado em inteiros (`inter × 5 ≥ união × 4`), com filtro de tamanho. Até 1.000 registros com texto, par a par; acima disso, filtro de prefixo (AllPairs): trechos ordenados pela raridade global, com desempate pelo texto, e prefixo de `n − ⌈0,8·n⌉ + 1` trechos indexado; candidatos verificados pelo Jaccard exato. O resultado é igual ao par a par. Só o registro posterior de cada par conta.
7. 🟢 **Unicidade semântica** (`service.py:199-203`): `(com texto − quase-duplicados) ÷ com texto`; contrato sem texto livre: "não aplicável" (`None`), fora do veredito.
8. 🟢 **PII** (`metrics.py:84-96`): cada texto do registro válido (texto livre e `enum`), com o caminho do campo, passa por `PiiGuard.leaks`; linha inválida passa inteira, no campo `registro`. Cada vazamento guarda índice, campo, tipo e prévia; nunca o valor.
9. 🟢 **Duração** (`metrics.py:99-114`): minutos com 1 casa entre `started_at` e a emissão; sem `started_at` ou com formato inválido, "não medida"; meta de tempo (< 10 min) só para volume ≤ 100, fora do veredito.
10. 🟢 **Veredito** (`metrics.py:117-129`): `APROVADO` só com conformidade ≥ 95%, unicidades ≥ 90% e 0 vazamentos; métricas que falharam em ordem fixa (`conformidade`, `unicidade_estrutural`, `unicidade_semantica`, `pii`).
11. 🟢 **Relatório** (`report.py`): `report.json` com decimais como número exato (`to_json_text`), e `report.md` gerado do mesmo objeto, com métricas, avisos, até 20 índices por tipo e a seção "Escopo e limites da detecção de PII" (`coverage()`). Ambos por `write_atomic`.
12. 🟢 **Avisos** (`service.py:161-176`): status do lote diferente de `concluido`, contrato mudado depois do lote, volume divergente, `run.json` ausente ou ilegível, allowlist ausente.
13. 🟢 **Avaliação no fim do lote** (`service.py:253-259`): mesma avaliação, sem checar a trava (o lote a segura); erro vira 1 linha de aviso com o comando `eval`.

### Constantes

| Constante | Valor | Local |
|-----------|-------|-------|
| `CONFORMITY_TARGET`, `UNIQUENESS_TARGET` | 95, 90 | `metrics.py:19-20` |
| `TIME_TARGET_MIN`, `TIME_TARGET_MAX_VOLUME` | 10 min, 100 | `metrics.py:21-22` |
| `PAIRWISE_LIMIT` | 1.000 | `semantic.py:14` |
| `SHINGLE_WORDS` | 3 | `text.py:15` |
| `MD_INDEX_LIMIT` | 20 | `report.py:17` |
| Códigos próprios | 17 (`REPROVADO`), 18 (dataset ausente ou ilegível) | `service.py:55-56` |

### Dependências

🟢 `schema`, `intent`, `pii`, `batch` (só `state` e `lock`), `sample` (`first_error`, `CommandResult`), `fsutil`.
