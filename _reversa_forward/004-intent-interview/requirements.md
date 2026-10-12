# Requirements: intent-interview (entrevista de intenção e pasta do dataset)

> Identificador: `004-intent-interview`
> Data: `2026-10-12`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA
> Cenário: greenfield. Fontes planejadas, mais os adendos vigentes `addenda/001-pii-guard.md`, `addenda/002-llm-provider.md` e `addenda/003-schema-builder.md`, que descrevem código entregue.

## 1. Resumo executivo

🟡 O `intent-interview` é a skill `sintetica-start`, ponto de entrada das 3 personas.
🟡 Antes da primeira pergunta, ele cria a pasta do dataset, mostra o caminho absoluto e marca o início da medição de tempo.
🟡 Ele coleta 5 itens em linguagem natural (objetivo, estrutura, regras, formato e volume), aceita "não sei" sem travar e grava a intenção em `intent.json`, já sem dados pessoais.
🟡 A intenção alimenta o `schema-builder`, entregue na feature 003, que já lê esse arquivo.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/sdd/intent-interview.md#6. Requisitos Funcionais` | RF-01 a RF-11: pasta imediata, slug, início da medição, modos, 5 itens, "não sei", padrões, mascaramento, confirmação, Expresso, volume | 🟡 |
| `_reversa_sdd/sdd/intent-interview.md#9. Modelo de Dados` | `Intent` e `Item` | 🟡 |
| `_reversa_sdd/sdd/intent-interview.md#11. Edge Cases e Tratamento de Erros` | Slug repetido, falha de escrita, tudo indefinido, formato não suportado, falha do `pii-guard`, PII na resposta | 🟡 |
| `_reversa_sdd/prd.md#4. Escopo (in)` | Criação imediata da pasta, entrevista sem jargão, modos Guiado e Expresso, selo INDEFINIDO | 🟡 |
| `_reversa_sdd/questions.md#Q20` | A medição de tempo começa no disparo de `/sintetica-start` | 🟡 |
| `_reversa_sdd/questions.md#Q21` | Mascaramento de PII antes de qualquer gravação ou envio | 🟡 |
| `_reversa_sdd/addenda/001-pii-guard.md#Impacto por artefato da extração` | Fachada `PiiGuard.for_dataset(...).mask(...)`; exceções devem bloquear a gravação (falha segura) | 🟢 |
| `_reversa_sdd/addenda/002-llm-provider.md#Impacto por artefato da extração` | Padrão aprovado na Q29: o agente orquestra, o runtime Python grava e valida por comandos `sintetica` | 🟢 |
| `_reversa_sdd/addenda/003-schema-builder.md#Impacto por artefato da extração` | O `schema-builder` lê `slug`, `mode`, `format` e `structure.status` de `intent.json`; `sintetica schema build` é o passo seguinte | 🟢 |

> As 3 últimas linhas recebem 🟢 porque descrevem código entregue e aprovado nas features 001 a 003.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| `dev-de-testes` | Massa de teste para as entidades do sistema | 🟡 Executa `/sintetica-start pedidos`, descreve pedidos e clientes, escolhe JSON e 50 registros. |
| `engenheiro-de-ml` | Conversas rotuladas para fine-tuning | 🟡 Executa `/sintetica-start suporte expresso` e responde as 5 perguntas numa única mensagem. |
| `analista-de-dados` | Tabela para validar um dashboard | 🟡 Responde "não sei" para regras e recebe a intenção com o item marcado como indefinido. |
| Agente do harness | Conduzir a conversa e registrar as respostas | 🟡 Chama os comandos do runtime a cada resposta e mostra o resumo devolvido. |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** 🟡 A pasta `datasets/<slug>/seeds/` existe e o caminho absoluto aparece antes da primeira pergunta. O início da medição (`started_at`, UTC) é gravado no mesmo passo.
   - Origem: `_reversa_sdd/sdd/intent-interview.md#6` (RF-01, RF-03), `_reversa_sdd/questions.md#Q20`
   - Tipo: nova
2. **RN-02:** 🟡 O slug vem do nome informado, em kebab-case ASCII; sem nome, é `dataset-<AAAAMMDD-HHMMSS>`. Slug já existente ganha sufixo `-2`, `-3`, e assim por diante.
   - Origem: `#6` (RF-02), `#11` (EC-01)
   - Tipo: nova
3. **RN-03:** 🟡 O agente conduz a conversa; o runtime Python cria a pasta, mascara, valida e grava cada resposta por comandos `sintetica`. O runtime nunca chama um modelo de linguagem nesta etapa.
   - Origem: padrão da Q29 (`addenda/002-llm-provider.md`), `#8` (a entrevista não chama LLM externo)
   - Tipo: nova
4. **RN-04:** 🟡 Toda resposta passa pelo mascaramento de PII antes de ser gravada. Se houver PII, o usuário é avisado e só a versão mascarada vai para o disco. Falha no mascaramento impede a gravação.
   - Origem: `#6` (RF-08), `#11` (EC-05), `_reversa_sdd/questions.md#Q21`
   - Tipo: nova
5. **RN-05:** 🟡 "Não sei" grava o item com o selo INDEFINIDO e a entrevista continua.
   - Origem: `#6` (RF-06)
   - Tipo: nova
6. **RN-06:** 🟡 Formato indefinido vira JSONL e volume indefinido vira 10 registros, ambos marcados como padrão no resumo.
   - Origem: `#6` (RF-07), `#14` (OQ-01), `_reversa_sdd/questions.md#Q38`
   - Tipo: nova
7. **RN-07:** 🟡 Formatos aceitos: CSV, JSON e JSONL. Volume aceito: 1 a 10.000. Valor fora disso é recusado; após 2 recusas seguidas de volume, aplica-se o padrão.
   - Origem: `#6` (RF-05, RF-11), `#11` (EC-04)
   - Tipo: nova
8. **RN-08:** 🟡 No modo Guiado, o próximo passo só começa após confirmação do resumo. No modo Expresso, as etapas seguem sem confirmação, exceto em 1 caso: objetivo **e** estrutura indefinidos ao mesmo tempo, quando o contrato seria o padrão de 1 campo. A autorização de custo continua valendo nos 2 modos.
   - Origem: `#6` (RF-09, RF-10), `#11` (EC-03), `#14` (OQ-02), `_reversa_sdd/questions.md#Q39`
   - Tipo: nova
9. **RN-09:** 🟡 Nesta feature, o encadeamento vai até `sintetica schema build`: depois da intenção confirmada (ou dispensada no Expresso), o resumo indica esse comando. As features `sample-preview`, `batch-generator` e `quality-evaluator` acrescentam os elos seguintes.
   - Origem: `#6` (RF-10), `_reversa_sdd/questions.md#Q40`
   - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O sistema deve criar `datasets/<slug>/seeds/`, gravar `intent.json` inicial com `started_at` e mostrar o caminho absoluto num único comando, antes de qualquer pergunta (RN-01). | Must | Após o comando, a pasta existe, `started_at` é anterior ao término do comando e a saída traz o caminho absoluto. | 🟡 |
| RF-02 | O sistema deve gerar o slug pela RN-02. | Must | `Pedidos de Café` gera `pedidos-de-cafe`; sem nome, `dataset-20261012-083000`; com `pedidos` existente, `pedidos-2`. | 🟡 |
| RF-03 | O sistema deve aceitar o modo `guiado` ou `expresso`, com `guiado` como padrão. | Must | Sem modo, `intent.json` grava `mode: "guiado"`. | 🟡 |
| RF-04 | O sistema deve registrar a resposta de cada um dos 5 itens (objetivo, estrutura, regras, formato, volume), um por chamada, e devolver o resumo atualizado. | Must | Após 5 registros, `intent.json` tem os 5 itens e o resumo mostra todos. | 🟡 |
| RF-05 | O sistema deve aceitar o registro de vários itens numa única chamada, para o modo Expresso. | Must | Uma chamada com os 5 itens grava os 5. | 🟡 |
| RF-06 | O sistema deve gravar "não sei" como INDEFINIDO (RN-05). | Must | "Não sei" para regras grava `rules: {"status": "indefinido", "text": null}`. | 🟡 |
| RF-07 | O sistema deve aplicar a RN-06 a formato e volume indefinidos. | Must | Formato e volume indefinidos gravam `jsonl` e `10`, com origem `padrao`. | 🟡 |
| RF-08 | O sistema deve recusar formato fora de CSV, JSON e JSONL, com mensagem que lista os 3 formatos (RN-07). | Must | "Parquet" é recusado e a mensagem cita CSV, JSON e JSONL. | 🟡 |
| RF-09 | O sistema deve recusar volume fora de 1 a 10.000 e, na 3ª recusa seguida, aplicar o padrão (RN-07). | Should | 50.000, 0 e −5 em sequência: as 2 primeiras recusadas, a 3ª aplica o padrão com aviso. | 🟡 |
| RF-10 | O sistema deve mascarar cada resposta de texto pela RN-04 e avisar quando houver PII, sem mostrar o valor original. | Must | A resposta com `ana@empresa.com` é gravada com outro e-mail; `pii_masked` vira `true`; o aviso não contém `ana@empresa.com`. | 🟡 |
| RF-11 | O sistema não deve gravar a resposta quando o mascaramento falhar, e deve encerrar com mensagem que cita a causa. | Must | Com política de PII inválida, `intent.json` continua igual e o código de saída indica erro. | 🟡 |
| RF-12 | O sistema deve mostrar o resumo da intenção com cada item marcado como definido, indefinido ou padrão, e indicar se a intenção está completa. | Must | Com regras indefinidas e volume padrão, o resumo mostra as 2 marcações. | 🟡 |
| RF-13 | O sistema deve registrar a confirmação do resumo no modo Guiado e, só então, indicar o próximo comando (`sintetica schema build`). | Must | Antes da confirmação, o resumo não indica o próximo comando; depois, indica. | 🟡 |
| RF-14 | No modo Expresso, o sistema deve dar a intenção completa como confirmada e indicar `sintetica schema build` sem pedir confirmação, exceto quando objetivo e estrutura forem ambos indefinidos (RN-08, RN-09). | Must | Expresso com regras indefinidas: o resumo já indica o comando. Expresso com objetivo e estrutura indefinidos: o resumo pede 1 confirmação e avisa que o contrato será genérico. | 🟡 |
| RF-15 | O sistema deve recusar registro ou confirmação para um dataset sem `intent.json`, com mensagem que indica o comando de início. | Must | Registro em `datasets/nada` termina com erro e cita o comando de início. | 🟡 |
| RF-16 | O sistema deve encerrar sem fazer perguntas quando não conseguir criar a pasta ou gravar a intenção, com o caminho e a causa. | Must | Em diretório somente leitura, o comando termina com erro, caminho e causa. | 🟡 |
| RF-17 | O `intent.json` gravado deve ser lido pelo `schema-builder` sem alteração. | Must | Após a entrevista, `sintetica schema build` aceita a intenção (com rascunho, ou com a estrutura indefinida). | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Privacidade | 0 respostas gravadas sem passar pelo mascaramento; o valor original nunca aparece em arquivo ou saída. | `_reversa_sdd/questions.md#Q21`, RN-04 | 🟡 |
| Desempenho | Cada comando da entrevista termina em ≤ 2 s, para não pesar na meta de < 10 min do PRD. | `_reversa_sdd/prd.md#3` | 🟡 |
| Durabilidade | Gravação atômica de `intent.json`: uma falha no meio nunca deixa o arquivo corrompido. | RF-11, RF-16 | 🟡 |
| Linguagem | Mensagens e perguntas sem termos técnicos de aprendizado de máquina ou estatística. | `_reversa_sdd/sdd/intent-interview.md#7` (RNF-05) | 🟡 |
| Qualidade | Tipagem estrita e lint sem erros; cobertura ≥ 80%. | `_reversa_sdd/questions.md#Q19` | 🟡 |
| Plataforma | Runtime Python ≥ 3.10. | `_reversa_sdd/questions.md#Q18` | 🟡 |
| Rede | 0 chamadas de rede durante a entrevista. | RN-03 | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Pasta criada antes da primeira pergunta
  Dado um projeto sem datasets
  Quando o agente inicia a entrevista com o nome "Pedidos de Café"
  Então a pasta datasets/pedidos-de-cafe/seeds/ existe
  E a saída mostra o caminho absoluto
  E intent.json tem started_at em UTC e mode "guiado"

Cenário: Slug sem nome e slug repetido
  Dado a pasta datasets/pedidos já existente
  Quando o agente inicia a entrevista com o nome "pedidos"
  Então o slug é "pedidos-2"
  E sem nome o slug segue o padrão dataset-AAAAMMDD-HHMMSS

Cenário: Entrevista Guiada completa
  Dado uma entrevista iniciada no modo Guiado
  Quando o agente registra objetivo, estrutura, regras, formato JSON e volume 50
  Então o resumo mostra os 5 itens definidos e pede confirmação
  E o próximo comando só aparece após a confirmação

Cenário: Modo Expresso em uma única chamada
  Dado uma entrevista iniciada no modo Expresso
  Quando o agente registra os 5 itens numa única chamada
  Então intent.json tem os 5 itens
  E o resumo já indica sintetica schema build sem pedir confirmação

Cenário: Expresso pede confirmação só com objetivo e estrutura indefinidos
  Dado uma entrevista no modo Expresso
  Quando objetivo e estrutura são respondidos com "não sei" e os outros 3 itens são definidos
  Então o resumo pede 1 confirmação e avisa que o contrato será genérico
  E após a confirmação o resumo indica sintetica schema build

Cenário: Não sei vira INDEFINIDO
  Dado uma entrevista em andamento
  Quando o usuário responde "não sei" para regras
  Então rules é gravado como indefinido
  E a entrevista continua

Cenário: Padrões para formato e volume indefinidos
  Dado uma entrevista em andamento
  Quando formato e volume são respondidos com "não sei"
  Então format é "jsonl" e volume é 10, ambos com origem "padrao"

Cenário: Formato não suportado
  Dado uma entrevista em andamento
  Quando o formato informado é "Parquet"
  Então o registro é recusado com a lista CSV, JSON e JSONL

Cenário: Volume fora do intervalo
  Dado uma entrevista em andamento
  Quando o volume informado é 50.000, depois 0, depois -5
  Então os 2 primeiros são recusados
  E o 3º aplica o volume padrão com aviso

Cenário: PII mascarada antes de gravar
  Dado uma entrevista em andamento
  Quando o objetivo informado contém "ana@empresa.com"
  Então intent.json contém outro e-mail no lugar
  E pii_masked é true
  E nem o arquivo nem o aviso contêm "ana@empresa.com"

Cenário: Falha do mascaramento bloqueia a gravação
  Dado uma política de PII com padrão inválido
  Quando o agente registra o objetivo
  Então intent.json não muda
  E o comando termina com erro que cita a política

Cenário: Registro sem entrevista iniciada
  Dado a pasta datasets/nada sem intent.json
  Quando o agente registra um item
  Então o comando termina com erro que cita o comando de início

Cenário: Falha de escrita
  Dado um projeto sem permissão de escrita
  Quando o agente inicia a entrevista
  Então o comando termina com erro com o caminho e a causa

Cenário: Integração com o schema-builder
  Dado uma entrevista concluída com estrutura indefinida
  Quando o agente executa sintetica schema build
  Então o contrato padrão é gerado sem erro
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-02, RF-03 | Must | Princípio da pasta imediata e início da medição (Q20). |
| RF-04, RF-05, RF-06, RF-08 | Must | Coleta dos 5 itens nos 2 modos. |
| RF-07 | Must | Depende da RN-06. |
| RF-09 | Should | Melhora a experiência; o fluxo funciona sem a 3ª tentativa. |
| RF-10, RF-11 | Must | Privacidade por design (Q21). |
| RF-12, RF-13, RF-15, RF-16, RF-17 | Must | Revisão, erros e integração com a feature 003. |
| RF-14 | Must | Modo Expresso; depende da RN-08. |

## 9. Esclarecimentos

### Sessão 2026-10-12

> Respostas do revisor Antigravity em `_reversa_sdd/questions.md` (bloco "Etapa 10, /reversa-clarify da feature 004-intent-interview").

- **Q:** Quais padrões usar para "não sei" em formato e volume (RN-06, RF-07)?
  **R:** Formato JSONL e volume 10, documentados como padrão no resumo da intenção.
- **Q:** O modo Expresso pede confirmação quando tudo é indefinido (RN-08, RF-14)?
  **R:** Só na condição crítica: objetivo e estrutura indefinidos ao mesmo tempo. Em qualquer outro caso, segue sem interrupção.
- **Q:** Até onde o Expresso encadeia nesta feature?
  **R:** Até `sintetica schema build`. As features seguintes estendem a cadeia.

## 10. Lacunas

- Nenhuma lacuna aberta. As 3 dúvidas foram resolvidas na sessão de 2026-10-12.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-12 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-12 | Esclarecimentos Q38 a Q40 integrados; RN-09 adicionada; dúvidas zeradas | reversa-clarify |
