# Requirements: sample-preview (amostra de 3 a 5 registros para aprovação)

> Identificador: `005-sample-preview`
> Data: `2026-10-12`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA
> Cenário: greenfield. Fontes planejadas, mais os adendos vigentes `addenda/001-pii-guard.md` a `addenda/004-intent-interview.md`, que descrevem código entregue.

## 1. Resumo executivo

🟡 O `sample-preview` é a skill `sintetica-sample`. Ela pede de 3 a 5 registros ao provedor de LLM, valida cada um pelo contrato do dataset, troca dados pessoais por valores falsos e mostra a amostra para aprovação.
🟡 O usuário aprova, pede um ajuste em linguagem natural ou volta ao contrato.
🟡 A amostra aprovada vira semente (`seeds/`) para a geração em lote.
🟡 Ela é a mitigação principal da premissa 1 do PRD: ver a qualidade antes de gastar tempo e tokens com o lote.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/sdd/sample-preview.md#6. Requisitos Funcionais` | RF-01 a RF-09: N de 3 a 5, harness como padrão, validação com 3 tentativas, mascaramento, exibição, aprovar/ajustar/voltar, semente, 3 rodadas, Expresso | 🟡 |
| `_reversa_sdd/sdd/sample-preview.md#11. Edge Cases e Tratamento de Erros` | Inválidos após 3 tentativas, saída não JSON, duplicados, schema alterado, falha do provedor | 🟡 |
| `_reversa_sdd/sdd/sample-preview.md#9. Modelo de Dados` | `SampleFile` com versão do contrato, data de aprovação, provedor e registros | 🟡 |
| `_reversa_sdd/questions.md#Q6` | Mitigação da premissa 1: amostra de 3 a 5 registros antes do lote | 🟡 |
| `_reversa_sdd/addenda/002-llm-provider.md#Impacto por artefato da extração` | Harness em 2 passos (`request`/`submit`, Q29); `HarnessResponsePending` traz o comando; `build_provider(..., harness_available=True)`; mesmo pedido, mesmo id; OQ-02 da spec resolvida | 🟢 |
| `_reversa_sdd/addenda/003-schema-builder.md#Impacto por artefato da extração` | `load_record_model`, `to_jsonl_line`, `to_csv_row`, `csv_columns`; `record.schema.json`; `schema.state.json` com status `aprovado` | 🟢 |
| `_reversa_sdd/addenda/004-intent-interview.md#Impacto por artefato da extração` | `intent.json` com modo, objetivo, estrutura e regras (já mascarados), lido por `load_intent_model` | 🟢 |
| `_reversa_sdd/addenda/001-pii-guard.md#Impacto por artefato da extração` | `PiiGuard.mask` grava os valores falsos na allowlist; falha bloqueia gravação | 🟢 |

> As 4 últimas linhas recebem 🟢 porque descrevem código entregue nas features 001 a 004.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| `dev-de-testes` | Ver 3 registros de pedidos antes do lote | 🟡 Aprova a amostra em JSON e segue para a geração. |
| `engenheiro-de-ml` | Conferir 3 a 5 conversas rotuladas | 🟡 Pede "conversas mais longas" como ajuste e aprova a 2ª amostra. |
| `analista-de-dados` | Conferir 3 linhas da tabela | 🟡 Vê a amostra como tabela e volta ao contrato para mudar uma coluna. |
| Agente do harness | Gerar os registros pedidos | 🟡 Recebe o pedido, gera o JSONL e envia com `sintetica submit`. |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** 🟡 A amostra só começa com o contrato aprovado e atual: `schema.state.json` com status `aprovado` e versão igual à de `schema.json`.
   - Origem: `_reversa_sdd/sdd/sample-preview.md#6.2` (passo 1), `addenda/003-schema-builder.md`
   - Tipo: nova
2. **RN-02:** 🟡 A amostra tem N registros, com N de 3 a 5 e padrão 3; o agente pode pedir 5 com `--n 5`.
   - Origem: `#6` (RF-01), `#14` (OQ-01), `_reversa_sdd/questions.md#Q41`
   - Tipo: nova
3. **RN-03:** 🟡 O provedor segue a prioridade da política do projeto, com o harness disponível; no padrão, a amostra é gerada pelo agente do harness, sem chave de API e sem custo. O pedido usa o protocolo em 2 passos: o runtime grava o pedido, o agente gera e envia os registros, e o runtime lê a resposta na chamada seguinte.
   - Origem: `#6` (RF-02), `addenda/002-llm-provider.md` (Q29)
   - Tipo: nova
4. **RN-04:** 🟡 Cada registro é validado pelo contrato. Inválidos e duplicados exatos são descartados e pedidos de novo, em até 3 tentativas no total. Resposta que não é JSON já é recusada pelo `sintetica submit` (código 5, feature 002) e não chega à amostra: o agente envia de novo, sem gastar tentativa.
   - Origem: `#6` (RF-03), `#11` (EC-01 a EC-03), `addenda/002-llm-provider.md` (`interfaces/harness-cli.md`)
   - Tipo: nova
5. **RN-05:** 🟡 Todo texto da amostra passa pelo mascaramento de PII antes de ser mostrado ou gravado. Falha no mascaramento impede mostrar e gravar.
   - Origem: `#6` (RF-04), `addenda/001-pii-guard.md`
   - Tipo: nova
6. **RN-06:** 🟡 O usuário responde aprovar, ajustar (com um pedido em linguagem natural) ou voltar ao contrato. O pedido de ajuste também passa pelo mascaramento. A partir da 4ª rodada de ajuste sem aprovação, o sistema sugere voltar ao contrato.
   - Origem: `#6` (RF-06, RF-08)
   - Tipo: nova
7. **RN-07:** 🟡 A amostra aprovada é gravada sempre como `seeds/sample.jsonl` (1 registro por linha, aceito por `sintetica request --seeds`), acompanhada de `seeds/sample.meta.json` com versão do contrato, data de aprovação, provedor, número de registros e indicação de amostra parcial. Mudança no contrato invalida a amostra em revisão ou aprovada.
   - Origem: `#6` (RF-07), `#9`, `#11` (EC-04), `addenda/002-llm-provider.md` (`sintetica request --seeds` em JSONL), `_reversa_sdd/questions.md#Q42`
   - Tipo: nova
8. **RN-08:** 🟡 No modo Expresso, a amostra com N registros válidos é aprovada sem pergunta; amostra parcial interrompe a automação e exige decisão do usuário. No modo Guiado, o usuário pode aprovar uma amostra parcial com pelo menos 1 registro válido, com alerta explícito; amostra vazia nunca é aprovada.
   - Origem: `#6` (RF-09), `#11` (EC-01), `_reversa_sdd/questions.md#Q43`
   - Tipo: nova
9. **RN-09:** 🟡 Nesta feature, a cadeia termina na amostra aprovada: o resultado indica que a geração em lote é o próximo passo, a ser ligado pela feature `batch-generator`.
   - Origem: `_reversa_sdd/questions.md#Q40` (encadeamento progressivo)
   - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O sistema deve recusar a amostra quando o contrato não estiver aprovado ou estiver desatualizado, indicando o comando a rodar (RN-01). | Must | Com contrato em revisão, o comando falha e cita `sintetica schema approve`. | 🟡 |
| RF-02 | O sistema deve aceitar N de 3 a 5 e recusar valores fora disso (RN-02). | Must | N = 6 e N = 2 são recusados; sem N, a amostra tem 3 registros. | 🟡 |
| RF-03 | O sistema deve montar o pedido com o JSON Schema do contrato e instruções vindas da intenção (objetivo, estrutura e regras definidos). | Must | O pedido gravado contém o JSON Schema de `record.schema.json` e o texto do objetivo. | 🟡 |
| RF-04 | O sistema deve gravar o pedido do harness e devolver ao agente o comando exato de envio, sem erro, quando ainda não houver resposta (RN-03). | Must | A 1ª chamada termina com o comando `sintetica submit <slug> <id>` e o estado "aguardando o agente". | 🟡 |
| RF-05 | O sistema deve ler a resposta do agente na chamada seguinte, validar cada registro pelo contrato e separar válidos, inválidos e duplicados (RN-04). | Must | Resposta com 2 válidos, 1 inválido e 1 duplicado: 2 aceitos, 2 descartados com o motivo. | 🟡 |
| RF-06 | O sistema deve pedir de novo só os registros que faltam, até 3 tentativas no total; depois, mostrar os válidos, informar a falha e sugerir voltar ao contrato. | Must | Com o agente sempre devolvendo inválidos, a 3ª tentativa encerra com a sugestão. | 🟡 |
| RF-07 | O sistema deve mascarar PII nos registros aceitos antes de mostrar e gravar (RN-05). | Must | Um CPF real na resposta aparece trocado na exibição e no arquivo. | 🟡 |
| RF-08 | O sistema deve mostrar a amostra como tabela Markdown no formato CSV e como JSON formatado nos formatos JSON e JSONL, com decimais e listas como no dataset final. | Must | CSV mostra cabeçalho e N linhas; JSONL mostra N blocos JSON. | 🟡 |
| RF-09 | O sistema deve aceitar um pedido de ajuste, mascará-lo, descartar a amostra atual e pedir uma nova com o ajuste como instrução extra (RN-06). | Must | Após o ajuste "nomes mais variados", o novo pedido contém esse texto. | 🟡 |
| RF-10 | O sistema deve contar as rodadas de ajuste e sugerir voltar ao contrato a partir da 4ª (RN-06). | Should | Na 4ª rodada, a saída traz a sugestão. | 🟡 |
| RF-11 | O sistema deve gravar a amostra aprovada como semente, com a versão do contrato, a data de aprovação e o provedor (RN-07). | Must | Após aprovar, `seeds/sample.jsonl` tem os registros e `seeds/sample.meta.json` traz a versão igual à de `schema.json`, o provedor, a data e o número de registros. | 🟡 |
| RF-12 | O sistema deve invalidar a amostra quando a versão do contrato mudar e exigir nova amostra (RN-07). | Must | Após `schema build` com versão nova, aprovar a amostra antiga é recusado. | 🟡 |
| RF-13 | No modo Expresso, o sistema deve aprovar e gravar a amostra sem pergunta quando os N registros forem válidos (RN-08). | Must | Expresso com N válidos: a semente é gravada na mesma chamada. | 🟡 |
| RF-14 | O sistema deve recusar aprovar uma amostra vazia; no Guiado, deve aprovar a parcial com alerta; no Expresso, deve parar na parcial e pedir decisão (RN-08). | Must | Com 0 válidos, aprovar falha; com 2 de 3 no Guiado, aprova com alerta e `partial: true`; com 2 de 3 no Expresso, nada é gravado e a saída pede decisão. | 🟡 |
| RF-15 | Ao aprovar, o sistema deve indicar que a geração em lote é o próximo passo (RN-09). | Must | A saída da aprovação cita a geração em lote. | 🟡 |
| RF-16 | O sistema deve informar qual provedor gerou a amostra e por quê. | Should | A saída traz o provedor e o motivo da escolha. | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | Cada chamada do runtime termina em ≤ 5 s, sem contar o tempo do agente ou do provedor externo. | `_reversa_sdd/sdd/sample-preview.md#3` (G-03: ≤ 60 s até mostrar) | 🟡 |
| Custo | US$ 0 no padrão (harness). | `#7` (RNF-05), Q8 | 🟡 |
| Privacidade | 0 valores de PII não mascarados na exibição ou no disco. | RN-05, Q21 | 🟡 |
| Qualidade da amostra | 100% dos registros mostrados válidos pelo contrato. | `#3` (G-01) | 🟡 |
| Durabilidade | Gravação atômica do estado e da semente. | Padrão das features 003 e 004 | 🟡 |
| Qualidade | Tipagem estrita e lint sem erros; cobertura ≥ 80%. | `_reversa_sdd/questions.md#Q19` | 🟡 |
| Plataforma | Runtime Python ≥ 3.10. | `_reversa_sdd/questions.md#Q18` | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Amostra recusada sem contrato aprovado
  Dado um dataset com contrato em revisão
  Quando o agente pede a amostra
  Então o comando falha e cita sintetica schema approve

Cenário: Pedido ao harness e espera pelo agente
  Dado um contrato aprovado e o harness disponível
  Quando o agente pede a amostra pela 1ª vez
  Então o pedido é gravado com o JSON Schema do contrato e o objetivo da intenção
  E a saída traz o comando sintetica submit com o id do pedido

Cenário: Amostra válida mostrada como JSON
  Dado um pedido de 3 registros respondido pelo agente com 3 registros válidos
  Quando o agente pede a amostra de novo
  Então a saída mostra 3 blocos JSON
  E informa o provedor harness

Cenário: Amostra CSV mostrada como tabela
  Dado um contrato CSV aprovado e 3 registros válidos na resposta
  Quando o agente pede a amostra
  Então a saída mostra uma tabela com cabeçalho e 3 linhas

Cenário: Inválidos e duplicados pedidos de novo
  Dado uma resposta com 2 válidos, 1 inválido e 1 duplicado
  Quando o agente pede a amostra
  Então 2 registros são aceitos
  E um novo pedido de 1 registro é gravado

Cenário: Resposta que não é JSON
  Dado um pedido de amostra aguardando o agente
  Quando o agente envia texto livre em vez de JSONL
  Então sintetica submit recusa o envio com o código 5
  E a amostra continua aguardando, sem gastar tentativa

Cenário: Falha após 3 tentativas
  Dado um agente que só devolve registros inválidos
  Quando a 3ª tentativa termina
  Então a saída mostra os válidos, informa a falha e sugere voltar ao contrato

Cenário: PII mascarada na amostra
  Dado uma resposta com o CPF 529.982.247-25
  Quando a amostra é mostrada e aprovada
  Então nem a saída nem os arquivos contêm 529.982.247-25

Cenário: Ajuste em linguagem natural
  Dado uma amostra em revisão
  Quando o usuário pede o ajuste "nomes mais variados"
  Então a amostra atual é descartada
  E o novo pedido contém "nomes mais variados"

Cenário: Sugestão na 4ª rodada de ajuste
  Dado 3 rodadas de ajuste sem aprovação
  Quando o usuário pede o 4º ajuste
  Então a saída sugere voltar ao contrato

Cenário: Aprovação grava a semente
  Dado uma amostra em revisão com 3 registros válidos
  Quando o usuário aprova
  Então o arquivo de semente existe com a versão atual do contrato
  E a saída indica a geração em lote como próximo passo

Cenário: Contrato alterado invalida a amostra
  Dado uma amostra em revisão
  Quando o contrato é gerado de novo com outra versão
  Então aprovar a amostra antiga é recusado

Cenário: Expresso aprova sem pergunta
  Dado o modo Expresso e uma resposta com N registros válidos
  Quando o agente pede a amostra
  Então a semente é gravada na mesma chamada

Cenário: Amostra parcial no modo Guiado
  Dado uma amostra com 2 registros válidos de 3 após 3 tentativas
  Quando o usuário aprova
  Então a semente tem 2 registros
  E a saída alerta que a amostra é parcial

Cenário: Amostra parcial no modo Expresso
  Dado o modo Expresso e 2 registros válidos de 3 após 3 tentativas
  Quando o agente pede a amostra
  Então nada é gravado como semente
  E a saída pede a decisão do usuário

Cenário: Amostra vazia não é aprovada
  Dado uma amostra sem registros válidos
  Quando o usuário tenta aprovar
  Então a aprovação é recusada
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-03 a RF-09, RF-11 a RF-13, RF-15 | Must | Fluxo da amostra e mitigação da premissa 1 do PRD. |
| RF-02 | Must | Depende da RN-02. |
| RF-14 | Must | Depende da RN-08. |
| RF-10, RF-16 | Should | Melhoram a experiência; o fluxo funciona sem eles. |
| RNF de privacidade | Must | Q21. |

## 9. Esclarecimentos

### Sessão 2026-10-12

> Respostas do revisor Antigravity em `_reversa_sdd/questions.md` (bloco "Etapa 11, /reversa-clarify da feature 005-sample-preview").

- **Q:** Qual é o tamanho padrão da amostra (RN-02, RF-02)?
  **R:** 3 registros; o agente pode pedir 5 com `--n 5`.
- **Q:** Qual é o formato do arquivo de semente (RN-07, RF-11)?
  **R:** `seeds/sample.jsonl` sempre, para uso direto em `--seeds`, mais `seeds/sample.meta.json` com os metadados.
- **Q:** O usuário pode aprovar amostra parcial no Guiado (RN-08, RF-14)?
  **R:** Sim, com pelo menos 1 registro válido e alerta explícito. No Expresso, a automação para e exige intervenção humana.

## 10. Lacunas

- Nenhuma lacuna aberta. As 3 dúvidas foram resolvidas na sessão de 2026-10-12.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-12 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-12 | Esclarecimentos Q41 a Q43 integrados; 2 cenários de amostra parcial adicionados; dúvidas zeradas | reversa-clarify |
