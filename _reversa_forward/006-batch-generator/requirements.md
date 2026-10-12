# Requirements: batch-generator (geração do lote completo)

> Identificador: `006-batch-generator`
> Data: `2026-10-12`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA
> Cenário: greenfield. Fontes planejadas, mais os adendos vigentes `addenda/001-pii-guard.md` a `addenda/005-sample-preview.md`, que descrevem código entregue.

## 1. Resumo executivo

🟡 O `batch-generator` é a skill `sintetica-generate`. Ele gera o lote completo do dataset (1 a 10.000 registros) a partir da intenção, do contrato e da amostra aprovada.
🟡 Ele estima o custo antes de começar, pede os registros em blocos ao provedor, valida cada registro pelo contrato, descarta duplicados, troca dados pessoais por valores falsos e grava o progresso a cada bloco, para retomar sem perda.
🟡 O resultado é `output/dataset.<ext>` no formato pedido (CSV, JSON ou JSONL) e `run.json` com a contagem e o custo.
🟡 Ele entrega a métrica de conformidade do PRD: ≥ 95% do volume pedido com registros válidos.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/sdd/batch-generator.md#6. Requisitos Funcionais` | RF-01 a RF-11: pré-condições, custo, blocos, validação com 3 rodadas extras, duplicados, mascaramento, arquivo parcial, background, `run.json`, retomada, conversão final | 🟡 |
| `_reversa_sdd/sdd/batch-generator.md#11. Edge Cases e Tratamento de Erros` | Falha do provedor, teto de custo, conformidade < 95%, processo morto, disco cheio, lote duplicado | 🟡 |
| `_reversa_sdd/sdd/batch-generator.md#9. Modelo de Dados` | `RunState` com status, contagens, custo e versão do contrato | 🟡 |
| `_reversa_sdd/questions.md#Q10` e `#Q28` | Lote de teste ≤ 100; acima de 100, geração assíncrona em background | 🟡 |
| `_reversa_sdd/questions.md#Q17` | Autorização explícita acima de US$ 5,00 | 🟡 |
| `_reversa_sdd/addenda/002-llm-provider.md#Impacto por artefato da extração` | `build_provider` com teto, concorrência 8, mascaramento e retry; `estimate_cost` com `requires_authorization`; o chamador pergunta e reconstrói com `authorized_usd`; parada por teto como `stop_reason = "teto de custo"`; harness atende até 100 registros por pedido | 🟢 |
| `_reversa_sdd/addenda/003-schema-builder.md#Impacto por artefato da extração` | `load_record_model`, `to_jsonl_line`, `to_csv_row`, `csv_columns`; decimal exato no JSON e casas fixas no CSV | 🟢 |
| `_reversa_sdd/addenda/004-intent-interview.md#Impacto por artefato da extração` | `intent.json` com volume, formato e modo | 🟢 |
| `_reversa_sdd/addenda/005-sample-preview.md#Impacto por artefato da extração` | Semente em `seeds/sample.jsonl` com `schema_version` em `seeds/sample.meta.json`; conferir a versão antes do lote | 🟢 |
| `_reversa_sdd/addenda/001-pii-guard.md#Impacto por artefato da extração` | `PiiGuard.mask` grava os valores falsos na allowlist do dataset | 🟢 |

> As 5 últimas linhas recebem 🟢 porque descrevem código entregue nas features 001 a 005.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| `engenheiro-de-ml` | 2.000 conversas rotuladas para fine-tuning | 🟡 Autoriza o custo estimado, acompanha o progresso e recebe `dataset.jsonl`. |
| `dev-de-testes` | 50 registros de teste em JSON | 🟡 Recebe `dataset.json` em poucos minutos, sem chave de API. |
| `analista-de-dados` | 500 linhas em CSV | 🟡 Retoma o lote depois de uma queda e recebe `dataset.csv` sem linhas repetidas. |
| Componente `quality-evaluator` (futuro) | Avaliar o lote | 🟡 Lê `output/dataset.<ext>` e `run.json`. |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** 🟡 O lote só começa com o contrato aprovado e atual e com a amostra aprovada para a mesma versão do contrato (`seeds/sample.meta.json`).
   - Origem: `_reversa_sdd/sdd/batch-generator.md#6` (RF-01), `addenda/005-sample-preview.md`
   - Tipo: nova
2. **RN-02:** 🟡 O provedor é escolhido pelo volume total do lote, não pelo tamanho do bloco. Assim, lotes acima de 100 registros nunca vão para o harness, que atende até 100 registros por pedido.
   - Origem: `addenda/002-llm-provider.md` (`select_provider` recebe o número de registros), `_reversa_sdd/questions.md#Q8`
   - Tipo: nova
3. **RN-03:** 🟡 Lotes de até 100 registros podem usar o agente do harness, pela política da feature 002. Com o harness, o lote vai num único pedido de até 100 registros, com as sementes da amostra; cada rodada extra pede só os faltantes, com id de pedido próprio. Os provedores automáticos (Ollama e API externa) recebem blocos concorrentes (RN-06).
   - Origem: `_reversa_sdd/questions.md#Q8` (harness para amostras e prototipagem), `#Q10`, `#Q44`
   - Tipo: nova
4. **RN-04:** 🟡 Antes do 1º pedido, o sistema estima o custo com o tamanho médio dos registros da amostra. Acima do teto da política (padrão US$ 5,00), o lote só começa com autorização explícita do valor; o custo acumulado nunca passa do valor autorizado.
   - Origem: `#6` (RF-02), `_reversa_sdd/questions.md#Q17`, `addenda/002-llm-provider.md`
   - Tipo: nova
5. **RN-05:** 🟡 Lotes acima de 100 registros rodam num processo separado, em sessão própria e desligado do terminal, e o comando devolve o controle ao chat em até 5 s. O PID e o progresso ficam em `run.json`. O comando de status mostra o andamento e detecta processo encerrado; a opção `--resume` continua do último bloco gravado (RN-09).
   - Origem: `#6` (RF-08), `#11` (EC-04), `_reversa_sdd/questions.md#Q28`, `#Q45`
   - Tipo: nova
6. **RN-06:** 🟡 Com provedor automático, o volume é pedido em blocos, enviados com a concorrência do provedor. O bloco é adaptativo: no máximo 10 registros, reduzido para que a saída estimada (tamanho médio dos registros da amostra × registros do bloco) fique em cerca de 4.000 tokens, com mínimo de 1. A opção `--block-size` define o bloco à mão.
   - Origem: `#6` (RF-03), `#14` (OQ-02), `_reversa_sdd/questions.md#Q46`
   - Tipo: nova
7. **RN-07:** 🟡 Cada registro é validado pelo contrato; inválidos e duplicados exatos são descartados e repostos em até 3 rodadas extras; depois disso, o lote termina com o que tiver.
   - Origem: `#6` (RF-04, RF-05)
   - Tipo: nova
8. **RN-08:** 🟡 Todo registro aceito passa pelo mascaramento de PII e é revalidado antes de ir ao disco; falha no mascaramento interrompe o lote sem gravar o bloco.
   - Origem: `#6` (RF-06), `addenda/001-pii-guard.md`, `addenda/005-sample-preview.md` (mesma regra da amostra)
   - Tipo: nova
9. **RN-09:** 🟡 O progresso é gravado a cada bloco concluído; a retomada continua do último bloco gravado, sem duplicar registros e sem novo custo pelos blocos já gravados.
   - Origem: `#6` (RF-07, RF-10)
   - Tipo: nova
10. **RN-10:** 🟡 Status final: `concluido` (≥ 95% do volume), `incompleto` (< 95% após as rodadas extras), `interrompido_custo` (teto atingido) ou `falha_provedor`. Em todos, o arquivo final é gerado com o que foi aceito.
    - Origem: `#9`, `#11` (EC-01 a EC-03), `_reversa_sdd/prd.md#3` (conformidade ≥ 95%)
    - Tipo: nova
11. **RN-11:** 🟡 Só 1 lote por dataset em andamento; um 2º pedido de geração é recusado com o status do lote atual.
    - Origem: `#11` (EC-06)
    - Tipo: nova
12. **RN-12:** 🟡 Nesta feature, a cadeia termina no arquivo final: o resultado indica a avaliação de qualidade como próximo passo, a ser ligada pela feature `quality-evaluator`.
    - Origem: `_reversa_sdd/questions.md#Q40`
    - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O sistema deve recusar o lote sem contrato aprovado e atual, ou sem amostra aprovada para a mesma versão do contrato, indicando o comando a rodar (RN-01). | Must | Com a amostra de uma versão antiga, o comando falha e cita `sintetica sample run`. | 🟡 |
| RF-02 | O sistema deve ler o volume e o formato da intenção e as sementes de `seeds/sample.jsonl`. | Must | Intenção com volume 50 e formato JSON gera 50 registros em `dataset.json`. | 🟡 |
| RF-03 | O sistema deve escolher o provedor pelo volume total (RN-02) e informar o provedor e o motivo. | Must | Volume 1.000 com o harness disponível e o Ollama desligado escolhe a API externa. | 🟡 |
| RF-04 | O sistema deve estimar o custo antes do 1º pedido e, acima do teto, parar sem pedir nada, mostrando o valor e o comando para autorizar (RN-04). | Must | Estimativa de US$ 6,00 sem autorização: 0 pedidos e a saída mostra o valor e o comando. | 🟡 |
| RF-05 | O sistema deve aceitar a autorização de um valor e nunca gastar além dele. | Must | Autorizado US$ 6,00: o custo acumulado em `run.json` fica ≤ 6,00. | 🟡 |
| RF-06 | O sistema deve pedir os registros em blocos adaptativos aos provedores automáticos, e num único pedido ao harness, com as sementes da amostra como exemplos e instruções vindas da intenção (RN-03, RN-06). | Must | Volume 1.000 com registros curtos gera 100 pedidos de 10 na 1ª rodada; registros de cerca de 1.000 tokens geram blocos de 4; volume 50 com o harness gera 1 pedido de 50. | 🟡 |
| RF-07 | O sistema deve validar, descartar duplicados (inclusive contra os já gravados), mascarar e revalidar cada registro (RN-07, RN-08). | Must | Um bloco com 1 inválido, 1 duplicado e 1 CPF real grava só os válidos, com o CPF trocado. | 🟡 |
| RF-08 | O sistema deve repor descartados em até 3 rodadas extras e então encerrar com o status da RN-10. | Must | Com 10% de inválidos persistentes, o status final é `incompleto` e o arquivo existe. | 🟡 |
| RF-09 | O sistema deve gravar os aceitos em `output/records.partial.jsonl` e atualizar `run.json` (aceitos, descartados, custo, status, provedor) a cada bloco (RN-09). | Must | Interrompido no meio, o arquivo parcial tem todos os blocos concluídos e `run.json` bate com ele. | 🟡 |
| RF-10 | O sistema deve retomar um lote interrompido do ponto em que parou (RN-09). | Must | Após retomar, o total final é o volume pedido, sem duplicados e sem repetir blocos gravados. | 🟡 |
| RF-11 | O sistema deve rodar lotes acima de 100 registros num processo separado (RN-05) e mostrar o progresso por um comando de status, que detecta processo encerrado e sugere `--resume`. | Must | Volume 1.000: o comando devolve o controle em ≤ 5 s; o status mostra aceitos, descartados, custo e estado; com o PID inexistente, o status sugere `--resume`. | 🟡 |
| RF-12 | O sistema deve recusar um 2º lote com outro em andamento (RN-11). | Must | Com um lote em andamento, um 2º pedido é recusado e mostra o status atual. | 🟡 |
| RF-13 | Ao terminar, o sistema deve converter o arquivo parcial em `output/dataset.<ext>`: JSON como lista, JSONL com 1 registro por linha, CSV em UTF-8 com cabeçalho na ordem do contrato e aspas pela RFC 4180. | Must | O CSV abre num leitor padrão com o cabeçalho e as linhas esperados; o JSON é uma lista válida. | 🟡 |
| RF-14 | Ao terminar, o sistema deve indicar a avaliação de qualidade como próximo passo (RN-12). | Must | A saída final cita a avaliação de qualidade. | 🟡 |
| RF-15 | O sistema deve tratar falha do provedor e disco cheio mantendo o último bloco íntegro e indicando a retomada. | Must | Com o provedor falhando no 3º bloco, os 2 primeiros ficam gravados e o status é `falha_provedor`. | 🟡 |
| RF-16 | No modo Expresso, o lote começa sem pergunta, exceto a autorização de custo. | Must | Expresso com custo abaixo do teto: o lote começa direto após a amostra aprovada. | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | Lote de 100 registros em ≤ 5 min com provedor automático. | `_reversa_sdd/sdd/batch-generator.md#3` (G-02) | 🟡 |
| Durabilidade | 0 registros perdidos após interrupção; gravação por bloco. | `#3` (G-03) | 🟡 |
| Privacidade | 0 registros gravados sem passar pelo mascaramento; resposta bruta do provedor nunca fica no disco. | `#3` (G-04), `addenda/005-sample-preview.md` | 🟡 |
| Custo | Custo acumulado ≤ valor autorizado. | Q17 | 🟡 |
| Memória | ≤ 500 MB para 10.000 registros de 1 KB. | `#7` (RNF-06) | 🟡 |
| Qualidade | Tipagem estrita e lint sem erros; cobertura ≥ 80%. | `_reversa_sdd/questions.md#Q19` | 🟡 |
| Testabilidade | Toda a suíte roda sem rede, com provedor simulado. | Padrão da feature 002 | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Lote recusado sem amostra da versão atual
  Dado um contrato aprovado e uma amostra aprovada para outra versão
  Quando o agente pede o lote
  Então o comando falha e cita sintetica sample run

Cenário: Provedor escolhido pelo volume total
  Dado o harness disponível, o Ollama desligado e uma chave de API definida
  Quando o lote de 1.000 registros é pedido
  Então o provedor escolhido é a API externa

Cenário: Custo acima do teto exige autorização
  Dado uma estimativa de US$ 6,00 e o teto de US$ 5,00
  Quando o agente pede o lote sem autorização
  Então nenhum pedido é enviado
  E a saída mostra o valor e o comando para autorizar

Cenário: Lote autorizado respeita o valor
  Dado o lote autorizado em US$ 6,00
  Quando a geração termina
  Então o custo acumulado em run.json é menor ou igual a 6,00

Cenário: Lote completo em JSON
  Dado uma intenção com volume 50 e formato JSON, contrato e amostra aprovados
  Quando o lote termina
  Então output/dataset.json é uma lista com 50 registros válidos
  E run.json tem status concluido
  E a saída indica a avaliação de qualidade como próximo passo

Cenário: Lote em CSV
  Dado uma intenção com formato CSV
  Quando o lote termina
  Então output/dataset.csv tem cabeçalho na ordem do contrato e aspas pela RFC 4180

Cenário: Inválidos, duplicados e PII num bloco
  Dado um bloco com 1 registro inválido, 1 duplicado de um já gravado e 1 CPF real
  Quando o bloco é processado
  Então só os válidos são gravados, com o CPF trocado por um valor falso
  E o CPF original não aparece em nenhum arquivo do dataset

Cenário: Rodadas extras esgotadas
  Dado um provedor que devolve 10% de registros inválidos sempre
  Quando as 3 rodadas extras terminam
  Então o status é incompleto e output/dataset.json existe com os válidos

Cenário: Retomada sem perda
  Dado um lote interrompido depois de 2 de 5 blocos
  Quando o agente retoma o lote
  Então o total final é o volume pedido, sem duplicados
  E os 2 blocos gravados não são pedidos de novo

Cenário: Falha do provedor no meio do lote
  Dado um provedor que falha no 3º bloco
  Quando o lote roda
  Então os 2 primeiros blocos ficam gravados
  E o status é falha_provedor com o comando de retomada

Cenário: Teto de custo atingido no meio
  Dado o custo real acima do estimado
  Quando o custo acumulado atinge o valor autorizado
  Então o status é interrompido_custo e o arquivo final é gerado com o que foi aceito

Cenário: Lote acima de 100 sem prender o chat
  Dado um lote de 1.000 registros
  Quando o agente pede o lote
  Então o comando devolve o controle em até 5 s
  E o comando de status mostra o progresso

Cenário: Processo encerrado durante o lote
  Dado um lote em background cujo processo foi encerrado
  Quando o agente consulta o status
  Então o status informa o processo encerrado e sugere --resume

Cenário: Lote de teste com o harness
  Dado o harness disponível e uma intenção com volume 50
  Quando o agente pede o lote
  Então é gravado 1 único pedido de 50 registros para o agente
  E a rodada extra pede só os faltantes, com outro id de pedido

Cenário: Bloco adaptativo para registros longos
  Dado uma amostra com registros de cerca de 1.000 tokens e provedor automático
  Quando o lote é pedido sem --block-size
  Então cada bloco tem 4 registros

Cenário: Segundo lote recusado
  Dado um lote em andamento
  Quando o agente pede outro lote para o mesmo dataset
  Então o pedido é recusado com o status do lote atual

Cenário: Expresso começa direto
  Dado o modo Expresso, a amostra aprovada e custo abaixo do teto
  Quando o agente pede o lote
  Então o lote começa sem pergunta
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 a RF-05, RF-07 a RF-10, RF-12, RF-13, RF-15, RF-16 | Must | Entrega principal do produto e métrica de conformidade do PRD. |
| RF-06 | Must | RN-03 e RN-06 (Q44, Q46). |
| RF-11 | Must | RN-05 (Q28, Q45). |
| RF-14 | Must | Encadeamento com a avaliação (Q40). |
| RNF de desempenho | Should | Meta de 3 meses do PRD. |

## 9. Esclarecimentos

### Sessão 2026-10-12

> Respostas do Antigravity em `_reversa_sdd/questions.md` (Etapa 12).

- **Q:** Lotes de até 100 registros usam o agente do harness? Num único pedido ou em blocos? (Q44)
  **R:** Sim. Pedido único de até 100 registros com as sementes; rodadas extras pedem só os faltantes. Os provedores automáticos usam blocos concorrentes. Atualizou RN-03 e RF-06.
- **Q:** Qual o mecanismo de execução em background para lotes acima de 100? (Q45)
  **R:** Processo separado em sessão própria, com PID em `run.json`, comando de status para acompanhamento e `--resume` incremental. Atualizou RN-05 e RF-11.
- **Q:** Qual o tamanho do bloco por pedido aos provedores automáticos? (Q46)
  **R:** Bloco adaptativo com teto de 10 registros, ajustado para cerca de 4.000 tokens de saída, com `--block-size` para ajuste manual. Atualizou RN-06 e RF-06.

## 10. Lacunas

Nenhuma lacuna aberta. As 3 dúvidas foram resolvidas pelas Q44 a Q46.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-12 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-12 | Respostas Q44 a Q46 integradas por `/reversa-clarify`: RN-03, RN-05, RN-06, RF-06, RF-11 e 3 cenários novos | reversa |
