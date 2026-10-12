# Investigation: quality-evaluator

> Identificador: `007-quality-evaluator`
> Data: `2026-10-12`
> Fonte: `_reversa_forward/007-quality-evaluator/roadmap.md`

## 1. Pesquisa de fundo (código entregue)

### 1.1 `PiiGuard` (feature 001)
- 🟢 `PiiGuard.for_dataset(dataset_dir, policy_path)` levanta `PolicyError` com política inválida.
- 🟢 `leaks(texto, field)` devolve os achados fora da allowlist; cada `PiiFinding` traz `type`, `start`, `end`, `field` e `preview` (2 caracteres + `***`).
- 🟢 `allowlist_available` é falso sem o arquivo da allowlist; nesse caso todo achado conta.
- 🟢 `coverage()` devolve 7 tipos fixos, o número de padrões extras e 6 limites conhecidos.

### 1.2 Contrato (feature 003)
- 🟢 `schema.json` guarda o contrato normalizado; para CSV, a versão achatada (colunas `endereco_cidade`, listas simples com `|`).
- 🟢 `load_record_model` importa o `Record`; `to_jsonl_line` dá o JSON canônico com decimal exato.
- 🟢 Contrato `conversation` gera `Record(messages: list[Message], labels: Labels)`, com `Message.role` fixo e `Message.content` texto.

### 1.3 Lote (feature 006)
- 🟢 `output/dataset.json` é uma lista com 1 registro canônico por linha; `dataset.jsonl` tem 1 por linha; `dataset.csv` usa CRLF, cabeçalho na ordem do contrato e aspas pela RFC 4180.
- 🟢 `run.json` tem `status`, `volume_requested` e `schema_version`.
- 🟢 `sintetica.batch.service._execute` gera o arquivo final em todo status final, dentro da trava do lote: é o ponto de ligação da avaliação (D-16).

### 1.4 Intenção (feature 004)
- 🟢 `started_at` gravado por `sintetica start`, em UTC; `IntentModel` aceita chaves extras.

## 2. Alternativas avaliadas

### 2.1 Busca de quase-duplicados acima de 1.000 registros
| Alternativa | Prós | Contras | Decisão |
|-------------|------|---------|---------|
| MinHash com LSH em Python puro | Sem dependência | 128 permutações × 10.000 registros × ~170 trechos ≈ 2 × 10⁸ operações; passa de 120 s; resultado aproximado | Descartada |
| `datasketch` (MinHash com LSH) | Rápida | Traz `numpy`; resultado aproximado; semente precisa ser fixada | Descartada |
| Filtro de prefixo com índice invertido e Jaccard exato | Exato (mesmo resultado do par a par); sem dependência; determinístico | Pior caso com textos muito parecidos gera mais candidatos | Escolhida (D-07) |

### 2.2 Onde gravar `finished_at`
| Alternativa | Prós | Contras | Decisão |
|-------------|------|---------|---------|
| Só no `report.json` | A avaliação não altera arquivos de outras features | A intenção não guarda o fim | Escolhida (D-10) |
| Também no `intent.json` | Fim da medição junto do início | Uma nova avaliação reescreve a intenção | Descartada |

## 3. Padrões aplicáveis

- 🟡 Similaridade de conjuntos: Jaccard = |A ∩ B| / |A ∪ B|; com tamanhos `a ≤ b`, Jaccard ≥ t só é possível se `a ≥ t·b` (filtro de tamanho).
- 🟡 Filtro de prefixo (algoritmo AllPairs): com os elementos de cada conjunto ordenados por uma ordem global, 2 conjuntos com Jaccard ≥ t compartilham pelo menos 1 elemento dos prefixos de tamanho `|A| − ⌈t·|A|⌉ + 1`.
- 🟡 Normalização Unicode: `unicodedata.category(c).startswith("P")` identifica pontuação em qualquer idioma.

## 4. Fontes externas

- Bayardo, Ma, Srikant, "Scaling Up All Pairs Similarity Search", WWW 2007: https://dl.acm.org/doi/10.1145/1242572.1242591
- Python, `unicodedata`: https://docs.python.org/3/library/unicodedata.html
- Python, `csv`: https://docs.python.org/3/library/csv.html
