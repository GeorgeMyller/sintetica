# Requirements: quality-evaluator (avaliação de qualidade do dataset)

> Identificador: `007-quality-evaluator`
> Data: `2026-10-12`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA
> Cenário: greenfield. Fontes planejadas, mais os adendos vigentes `addenda/001-pii-guard.md` a `addenda/006-batch-generator.md`, que descrevem código entregue.

## 1. Resumo executivo

🟡 O `quality-evaluator` é a skill `sintetica-eval`. Ele avalia o dataset final gerado pelo lote e mede 4 números: conformidade com o contrato, unicidade estrutural, unicidade semântica e vazamentos de PII.
🟡 Ele fecha a medição de tempo iniciada por `sintetica start` e dá o veredito `APROVADO` ou `REPROVADO`.
🟡 O resultado é `report.md` e `report.json` na pasta do dataset, com as métricas, o veredito, a duração, os índices dos registros com problema e o escopo da detecção de PII.
🟡 É o último elo do pipeline e a prova das 3 métricas de sucesso do PRD que são medidas (conformidade, diversidade e PII).

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/sdd/quality-evaluator.md#6. Requisitos Funcionais` | RF-01 a RF-11: conformidade, unicidade estrutural e semântica, MinHash acima de 1.000, PII fora da allowlist, duração, meta de tempo, veredito, relatório, escopo da PII, código de saída | 🟡 |
| `_reversa_sdd/sdd/quality-evaluator.md#11. Edge Cases e Tratamento de Erros` | Dataset ausente, linha corrompida, schema sem texto, allowlist ausente, schema alterado | 🟡 |
| `_reversa_sdd/sdd/quality-evaluator.md#9. Modelo de Dados` | `Report` com veredito, métricas, cobertura de PII, duração, status do lote e índices | 🟡 |
| `_reversa_sdd/prd.md#3. Métricas de sucesso` | Conformidade ≥ 95%, 0 vazamentos, tempo < 10 min para até 100 registros | 🟡 |
| `_reversa_sdd/questions.md#Q9`, `#Q16`, `#Q20`, `#Q27` | Critério de vazamento; unicidade ≥ 90%; janela de tempo; Jaccard ≥ 0,8 sobre 3-gramas | 🟡 |
| `_reversa_sdd/addenda/001-pii-guard.md#Impacto por artefato da extração` | `PiiGuard.leaks` ignora valores falsos da allowlist; `coverage()` lista 7 tipos, padrões extras e 6 limites; `allowlist_available` | 🟢 |
| `_reversa_sdd/addenda/003-schema-builder.md#Impacto por artefato da extração` | `load_record_model`, `parse_line` com decimal exato, colunas do CSV na ordem do contrato, listas com `\|` | 🟢 |
| `_reversa_sdd/addenda/004-intent-interview.md#Impacto por artefato da extração` | `started_at` em UTC no `intent.json`; o avaliador pode gravar chaves próprias sem perdê-las | 🟢 |
| `_reversa_sdd/addenda/006-batch-generator.md#Impacto por artefato da extração` | Entrada: `output/dataset.<ext>` e `output/run.json` com `status` e `schema_version`; o lote só indica a avaliação como próximo passo | 🟢 |

> As 4 últimas linhas recebem 🟢 porque descrevem código entregue nas features 001 a 006.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| `dev-de-testes` | Saber se os 50 registros de teste servem | 🟡 Lê o veredito e a duração; a meta de 10 min vale para o lote dele. |
| `engenheiro-de-ml` | Saber se as 2.000 conversas são diversas e sem PII | 🟡 Lê a unicidade semântica e os vazamentos antes do fine-tuning. |
| `analista-de-dados` | Saber se o CSV respeita as regras | 🟡 Lê a conformidade e os índices das linhas inválidas. |
| Automação de CI do usuário | Barrar dataset ruim | 🟡 Lê `report.json` e o código de saída do comando. |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** 🟡 A conformidade é o número de registros válidos pelo contrato atual dividido pelo volume pedido na intenção. Registros descartados pelo lote contam contra a meta.
   - Origem: `_reversa_sdd/sdd/quality-evaluator.md#6` (RF-01), `#15` (decisão "conformidade sobre o volume pedido")
   - Tipo: nova
2. **RN-02:** 🟡 A unicidade estrutural é o número de registros distintos pelo JSON canônico dividido pelo total de registros lidos.
   - Origem: `#6` (RF-02)
   - Tipo: nova
3. **RN-03:** 🟡 A unicidade semântica usa 3-gramas de palavras sobre o texto livre do registro. O texto livre são todos os campos de tipo texto, inclusive em listas e objetos aninhados, unidos na ordem do contrato e normalizados (minúsculas, sem pontuação, espaços únicos). Texto com menos de 3 palavras vira 1 único trecho com o texto inteiro. Campos de escolha fixa (enum), números e datas ficam fora. Um registro com Jaccard ≥ 0,8 com outro anterior conta como quase-duplicado. A unicidade é a fração de registros com texto que não são quase-duplicados; a meta é ≥ 90%. Registro sem texto livre fica fora da conta; contrato sem campo de texto livre dá "não aplicável".
   - Origem: `#6` (RF-03, RF-04), `_reversa_sdd/questions.md#Q16`, `#Q27`, `#Q47`
   - Tipo: nova
4. **RN-04:** 🟡 Acima de 1.000 registros, a unicidade semântica usa MinHash com LSH, com semente fixa, para avaliar 10.000 registros em ≤ 120 s com o mesmo resultado a cada execução.
   - Origem: `#6` (RF-04), `#7` (RNF-04, RNF-05)
   - Tipo: nova
5. **RN-05:** 🟡 Vazamento é cada achado do `PiiGuard` em campo de texto que não está na allowlist do dataset. Sem allowlist, todo achado conta como vazamento e o relatório cita a causa. O relatório mostra índice, campo, tipo e prévia mascarada, nunca o valor completo.
   - Origem: `#6` (RF-05), `#11` (EC-04), `#12`, `addenda/001-pii-guard.md`, `_reversa_sdd/questions.md#Q9`
   - Tipo: nova
6. **RN-06:** 🟡 A duração vai de `started_at` da intenção até a emissão do relatório, em minutos com 1 casa decimal. Sem `started_at`, a duração é "não medida". A meta de tempo (< 10 min) só se aplica a volume ≤ 100.
   - Origem: `#6` (RF-06, RF-07), `#6.3` (Fluxo A), `_reversa_sdd/questions.md#Q20`
   - Tipo: nova
7. **RN-07:** 🟡 O veredito é `APROVADO` só com conformidade ≥ 95%, as 2 unicidades ≥ 90% e 0 vazamentos. Senão, `REPROVADO` com a lista das métricas que falharam. Unicidade semântica "não aplicável" (contrato sem texto) não entra no veredito.
   - Origem: `#6` (RF-08), `#11` (EC-03)
   - Tipo: nova
8. **RN-08:** 🟡 O avaliador nunca altera o dataset nem chama provedor de LLM (0 chamadas de rede). As métricas são determinísticas e locais; não há LLM-juiz nesta versão.
   - Origem: `#4` (NG-01, NG-02), `#7` (RNF-06), `#14` (OQ-02)
   - Tipo: nova
9. **RN-09:** 🟡 O relatório cita o status do lote (`run.json`). Com lote `incompleto`, `interrompido_custo` ou `falha_provedor`, o avaliador avalia o que existe. Com o contrato alterado depois do lote, o relatório avisa a divergência e avalia com o contrato atual.
   - Origem: `#6.3` (Fluxo B), `#11` (EC-05), `addenda/006-batch-generator.md`
   - Tipo: nova
10. **RN-10:** 🟡 O comando de avaliação termina com 0 em `APROVADO` e 17 em `REPROVADO`. Dataset final ausente gera o código 18. Os demais erros de execução mantêm os códigos existentes: 2 (dataset, intenção ou argumento), 9 (mascaramento de PII indisponível), 10 (escrita) e 11 (contrato).
    - Origem: `#6` (RF-11), `#15` (decisão "código de saída 2", substituída), `addenda/006-batch-generator.md` (tabela de códigos), `_reversa_sdd/questions.md#Q48`
    - Tipo: nova
11. **RN-11:** 🟡 O fim do lote roda a avaliação sozinho, em primeiro plano e no processo em background, em todo status final. O comando `sintetica eval <slug>` também existe para avaliação avulsa e para CI. O código de saída do `generate` não muda com o veredito; o veredito aparece na saída e no `report.json`.
    - Origem: `#5` (jornada futura, passo 1), `#6.2` (passo 1), `_reversa_sdd/questions.md#Q40`, `#Q49`, `addenda/006-batch-generator.md`
    - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O sistema deve ler `output/dataset.<ext>` no formato do contrato (lista JSON, JSONL ou CSV), validando cada registro com o contrato atual; linha ilegível conta como inválida e entra nos índices de inválidos. | Must | Um JSONL com 1 linha corrompida entre 10 conta 9 válidos e cita o índice da linha. | 🟡 |
| RF-02 | O sistema deve calcular a conformidade pela RN-01. | Must | 96 válidos de 100 pedidos dão 96,0%. | 🟡 |
| RF-03 | O sistema deve calcular a unicidade estrutural pela RN-02. | Must | 100 registros com 5 cópias exatas dão 95,0%. | 🟡 |
| RF-04 | O sistema deve calcular a unicidade semântica pela RN-03 e RN-04. | Must | 2 textos que diferem só em pontuação e caixa contam como quase-duplicados; textos com menos de 3 palavras viram 1 trecho; 10.000 registros de 1 KB são avaliados em ≤ 120 s. | 🟡 |
| RF-05 | O sistema deve contar vazamentos de PII pela RN-05. | Must | 1 e-mail real inserido gera 1 vazamento; os valores falsos da allowlist geram 0. | 🟡 |
| RF-06 | O sistema deve calcular a duração e a meta de tempo pela RN-06. | Must | Lote de 50 registros com 12 min de duração marca a meta de tempo como não atingida. | 🟡 |
| RF-07 | O sistema deve dar o veredito pela RN-07. | Must | Conformidade de 94% gera `REPROVADO` com "conformidade" na lista de métricas que falharam. | 🟡 |
| RF-08 | O sistema deve gravar `report.md` e `report.json` com os mesmos números, o veredito, a duração, o status do lote e os índices dos registros com problema. | Must | Os 2 arquivos existem e os números batem. | 🟡 |
| RF-09 | O relatório deve ter a seção "Escopo e limites da detecção de PII" com os dados de `coverage()`. | Must | A seção lista os 7 tipos, o número de padrões extras e os 6 limites conhecidos. | 🟡 |
| RF-10 | O sistema deve mostrar no chat um bloco curto com o veredito, os 4 números, a duração e o caminho absoluto do relatório. | Must | A saída tem 1 linha por métrica e o caminho de `report.md`. | 🟡 |
| RF-11 | O sistema deve terminar com o código de saída da RN-10. | Should | `sintetica eval` devolve 17 com dataset reprovado e 18 sem dataset final; um pipeline de CI falha nos 2 casos. | 🟡 |
| RF-12 | O sistema deve recusar a avaliação sem dataset final, indicando o comando do lote (`generate` ou `--resume`). | Must | Sem `output/dataset.<ext>`, o comando falha e cita `sintetica generate`. | 🟡 |
| RF-13 | O sistema deve recusar a avaliação sem contrato legível ou com o mascaramento de PII indisponível, sem emitir veredito. | Must | Com a política de PII inválida, o comando falha e não grava relatório. | 🟡 |
| RF-14 | O sistema deve rodar a avaliação ao fim do lote conforme a RN-11. | Must | Um lote concluído em primeiro plano ou em background deixa `report.json`; a saída do `generate` mostra o veredito e o código do `generate` não muda. | 🟡 |
| RF-15 | O sistema deve produzir o mesmo `report.json` para o mesmo dataset, exceto a data de emissão e a duração. | Must | 2 avaliações seguidas do mesmo dataset diferem só nesses campos. | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | 10.000 registros de 1 KB avaliados em ≤ 120 s. | `_reversa_sdd/sdd/quality-evaluator.md#7` (RNF-04) | 🟡 |
| Determinismo | Mesmo dataset gera o mesmo relatório, exceto data e duração. | `#7` (RNF-05) | 🟡 |
| Rede | 0 chamadas de rede. | `#7` (RNF-06), Q15 | 🟡 |
| Privacidade | O relatório nunca mostra o valor completo de um achado de PII. | `#12` | 🟡 |
| Memória | Leitura do dataset em fluxo; índice semântico proporcional ao número de registros, não ao texto completo. | Coerente com a RNF de memória da feature 006 | 🟡 |
| Qualidade | Tipagem estrita e lint sem erros; cobertura ≥ 80%. | `_reversa_sdd/questions.md#Q19` | 🟡 |
| Testabilidade | Toda a suíte roda sem rede, com datasets de referência de métricas conhecidas. | `#13` (rollout) | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Dataset aprovado
  Dado um lote concluido de 50 registros válidos, distintos e sem PII
  Quando o agente pede a avaliação
  Então o veredito é APROVADO
  E report.md e report.json existem com os mesmos números
  E a saída mostra os 4 números, a duração e o caminho do relatório

Cenário: Conformidade abaixo da meta
  Dado um lote incompleto com 94 registros válidos de 100 pedidos
  Quando o agente pede a avaliação
  Então a conformidade é 94,0%
  E o veredito é REPROVADO com "conformidade" entre as métricas que falharam
  E o relatório cita o status incompleto do lote

Cenário: Cópias exatas
  Dado 100 registros com 5 cópias exatas
  Quando o agente pede a avaliação
  Então a unicidade estrutural é 95,0%

Cenário: Quase-duplicados por pontuação
  Dado 2 registros cujos textos diferem só em pontuação e caixa
  Quando o agente pede a avaliação
  Então os 2 contam como quase-duplicados

Cenário: Contrato sem campo de texto
  Dado um contrato só com campos numéricos
  Quando o agente pede a avaliação
  Então a unicidade semântica é "não aplicável" e não entra no veredito

Cenário: PII real no dataset
  Dado um dataset com 1 e-mail real e valores falsos registrados na allowlist
  Quando o agente pede a avaliação
  Então o relatório conta 1 vazamento com índice, campo, tipo e prévia mascarada
  E o e-mail completo não aparece no relatório
  E o veredito é REPROVADO

Cenário: Allowlist ausente
  Dado um dataset com valores falsos e sem o arquivo da allowlist
  Quando o agente pede a avaliação
  Então todo achado conta como vazamento e o relatório cita a causa

Cenário: Linha corrompida
  Dado um JSONL com 1 linha que não é JSON
  Quando o agente pede a avaliação
  Então a linha conta como inválida e o índice dela aparece no relatório

Cenário: Meta de tempo não atingida
  Dado um lote de 50 registros com started_at 12 minutos antes da avaliação
  Quando o agente pede a avaliação
  Então o relatório marca a meta de tempo como não atingida

Cenário: Avaliação sem started_at
  Dado uma intenção sem started_at
  Quando o agente pede a avaliação
  Então a duração aparece como não medida

Cenário: Contrato alterado depois do lote
  Dado um run.json com schema_version diferente do contrato atual
  Quando o agente pede a avaliação
  Então o relatório avisa a divergência e avalia com o contrato atual

Cenário: Dataset ausente
  Dado um dataset sem output/dataset.<ext>
  Quando o agente pede a avaliação
  Então o comando falha com o código 18 e cita sintetica generate

Cenário: Mascaramento indisponível
  Dado uma política de PII inválida
  Quando o agente pede a avaliação
  Então o comando falha sem emitir veredito nem gravar relatório

Cenário: Avaliação determinística
  Dado um dataset avaliado 2 vezes
  Quando os 2 report.json são comparados
  Então eles diferem só na data de emissão e na duração

Cenário: Avaliação ao fim do lote
  Dado um lote de 20 registros que termina com status concluido
  Quando o generate termina
  Então report.json existe e a saída do generate mostra o veredito
  E o código de saída do generate é o mesmo de antes da avaliação

Cenário: Código de saída para CI
  Dado um dataset reprovado
  Quando o agente roda sintetica eval
  Então o código de saída é 17

Cenário: Textos curtos e campos fixos
  Dado registros cujo texto livre tem 2 palavras e um campo enum igual em todos
  Quando o agente pede a avaliação
  Então cada texto curto vira 1 trecho e o enum não entra na comparação

Cenário: Desempenho em lote grande
  Dado 10.000 registros de cerca de 1 KB
  Quando o agente pede a avaliação
  Então a avaliação termina em até 120 s
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 a RF-10, RF-12, RF-13, RF-15 | Must | Medição das métricas do PRD e relatório. |
| RF-04 | Must | RN-03 (Q16, Q27, Q47). |
| RF-14 | Must | RN-11 (Q40, Q49). |
| RF-11 | Should | RN-10 (Q48); a spec marca como Should. |
| RNF de desempenho | Should | Meta do MVP da spec (G-02). |

## 9. Esclarecimentos

### Sessão 2026-10-12

> Respostas do Antigravity em `_reversa_sdd/questions.md` (Etapa 13).

- **Q:** Os 3-gramas da unicidade semântica são de palavras ou de caracteres? Qual texto entra, e como tratar textos curtos? (Q47)
  **R:** 3-gramas de palavras sobre o texto livre agregado e normalizado; texto com menos de 3 palavras vira 1 trecho; enum, números e datas ficam fora. Atualizou RN-03 e RF-04.
- **Q:** Qual código de saída para `REPROVADO`? (Q48)
  **R:** 0 para `APROVADO`, 17 para `REPROVADO`, 18 para dataset final ausente; os erros de execução mantêm os códigos existentes. Atualizou RN-10 e RF-11.
- **Q:** O fim do lote roda a avaliação sozinho? (Q49)
  **R:** Sim, em primeiro plano e em background; `sintetica eval <slug>` continua disponível para execuções avulsas e CI. Atualizou RN-11 e RF-14.

## 10. Lacunas

Nenhuma dúvida de escopo aberta. As 3 dúvidas foram resolvidas pelas Q47 a Q49.

- 🟡 Decisão técnica para o plano, sem dúvida de escopo: MinHash com LSH por implementação própria (sem dependência nova) ou pela biblioteca `datasketch` (dependência opcional citada na spec, `#10`).

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-12 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-12 | Respostas Q47 a Q49 integradas por `/reversa-clarify`: RN-03, RN-10, RN-11, RF-04, RF-11, RF-14 e 3 cenários novos | reversa |
