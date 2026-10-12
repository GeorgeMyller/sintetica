# Requirements: schema-builder (contrato de dados do dataset)

> Identificador: `003-schema-builder`
> Data: `2026-10-12`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA
> Cenário: greenfield. Fontes planejadas, mais os adendos vigentes `addenda/001-pii-guard.md` e `addenda/002-llm-provider.md`, que descrevem código entregue.

## 1. Resumo executivo

🟡 O `schema-builder` é a skill `sintetica-schema`. Ela transforma a intenção do usuário (`intent.json`) no contrato de dados do dataset.
🟡 O contrato tem 3 formas: uma definição declarativa (`schema.json`), um modelo de validação gerado (`schema.py`, classe `Record`) e o JSON Schema exportado, que o provedor de LLM recebe.
🟡 O usuário revisa o contrato numa tabela legível, sem ler código, e pede ajustes em linguagem natural.
🟡 O contrato aprovado valida cada registro na amostra, na geração e na avaliação, e torna mensurável a meta de ≥ 95% de conformidade do PRD.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/sdd/schema-builder.md#1. Resumo` | Traduz `intent.json` em modelo de validação e mostra para revisão | 🟡 |
| `_reversa_sdd/sdd/schema-builder.md#6. Requisitos Funcionais` | RF-01 a RF-10: definição declarativa, gerador determinístico, 9 tipos, 7 restrições, conversa, CSV plano, ajustes, validação, versão | 🟡 |
| `_reversa_sdd/sdd/schema-builder.md#9. Modelo de Dados` | `SchemaSpec` e `FieldSpec` | 🟡 |
| `_reversa_sdd/sdd/schema-builder.md#11. Edge Cases e Tratamento de Erros` | Nomes inválidos, restrições contraditórias, falha de validação, aninhamento em CSV, 100 campos, 5 rodadas | 🟡 |
| `_reversa_sdd/sdd/intent-interview.md#9. Modelo de Dados` | Formato de entrada `Intent` e `Item` (`definido` ou `indefinido`) | 🟡 |
| `_reversa_sdd/prd.md#3. Métricas de sucesso` | Conformidade com o schema ≥ 95% | 🟡 |
| `_reversa_sdd/addenda/002-llm-provider.md#Impacto por artefato da extração` | O comando `sintetica request` recebe um arquivo JSON Schema do registro (`--schema`); o provedor mascara os textos do schema antes do envio externo | 🟢 |
| `_reversa_sdd/addenda/001-pii-guard.md#Impacto por artefato da extração` | Consumidores tratam exceções do `pii-guard` como falha segura | 🟢 |

> As 2 últimas linhas recebem 🟢 porque descrevem código entregue e aprovado nas features 001 e 002.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| `dev-de-testes` | Comparar o contrato com os modelos do sistema sob teste | 🟡 Revisa a tabela de campos de um JSON de pedidos e ajusta 1 restrição. |
| `engenheiro-de-ml` | Contrato de conversa com papéis e rótulos | 🟡 Recebe `Record` com `messages` e `labels` para JSONL de fine-tuning. |
| `analista-de-dados` | Colunas tipadas com restrições | 🟡 Pede "idade entre 18 e 90" e vê a coluna `idade` com mínimo 18 e máximo 90. |
| Componentes `sample-preview`, `batch-generator`, `quality-evaluator` | Validar registros | 🟡 Carregam a classe `Record` do dataset e o JSON Schema exportado. |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** 🟡 O agente do harness traduz a intenção e os ajustes em linguagem natural para a definição declarativa. O runtime Python nunca executa código escrito pelo modelo: ele valida a definição e gera o código por um gerador determinístico.
   - Origem: `_reversa_sdd/sdd/schema-builder.md#4` (NG-02), `#15`; padrão do protocolo de arquivo da Q29 (`addenda/002-llm-provider.md`)
   - Tipo: nova
2. **RN-02:** 🟡 Todo texto vindo da definição (nomes, descrições, padrões, valores permitidos) entra no código gerado apenas como literal escapado, nunca como código.
   - Origem: `_reversa_sdd/sdd/schema-builder.md#12` (segurança de código)
   - Tipo: nova
3. **RN-03:** 🟡 Nomes de campo são normalizados para snake_case ASCII. Palavras reservadas do Python e nomes reservados pelo modelo de validação ganham sufixo `_`. Nomes repetidos após a normalização ganham sufixo numérico.
   - Origem: `_reversa_sdd/sdd/schema-builder.md#11` (EC-01)
   - Tipo: nova
4. **RN-04:** 🟡 Formato CSV aceita só colunas planas. Objetos aninhados viram colunas com prefixo (ex.: `endereco_cidade`). Lista de valores simples (texto, número, data, enum) vira 1 coluna de texto com os itens separados por `|`; por isso, nenhum item pode conter `|`. Lista de objetos é recusada com mensagem que orienta usar JSON ou JSONL.
   - Origem: `_reversa_sdd/sdd/schema-builder.md#6` (RF-06), `#11` (EC-04), `_reversa_sdd/questions.md#Q35`
   - Tipo: nova
5. **RN-05:** 🟡 A versão do contrato é o hash SHA-256 da forma canônica da definição (chaves ordenadas, sem espaços variáveis). Mudar 1 campo muda a versão; reformatar o arquivo não muda.
   - Origem: `_reversa_sdd/sdd/schema-builder.md#6` (RF-10)
   - Tipo: nova
6. **RN-06:** 🟡 Limites: até 100 campos por contrato (contando campos aninhados) e até 5 rodadas de ajuste antes de sugerir nova entrevista.
   - Origem: `_reversa_sdd/sdd/schema-builder.md#7` (RNF-05), `#11` (EC-05, EC-06)
   - Tipo: nova
7. **RN-07:** 🟡 Estrutura `indefinido` na intenção gera 1 campo de texto `descricao` com a descrição "a definir" e um aviso ao usuário.
   - Origem: `_reversa_sdd/sdd/schema-builder.md#6` (RF-09)
   - Tipo: nova
8. **RN-08:** 🟡 O contrato gerado só chega ao usuário depois de validado no runtime por importação do código, presença da classe `Record` e exportação do JSON Schema. A verificação estrita de tipos e o lint do código gerado ficam na suíte de testes do gerador, que cobre todos os tipos, restrições e casos de borda.
   - Origem: `_reversa_sdd/sdd/schema-builder.md#6` (RF-08), `#7` (RNF-02), `_reversa_sdd/questions.md#Q36`
   - Tipo: nova
9. **RN-09:** 🟡 O tipo decimal aceita número ou texto numérico na entrada e tem a restrição opcional `casas_decimais`. No JSON e no JSONL, o valor sai como número; no CSV, como texto com ponto decimal e as casas definidas.
   - Origem: `_reversa_sdd/questions.md#Q37`
   - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O sistema deve ler `datasets/<slug>/intent.json` e recusar intenção ausente ou malformada com mensagem que indica `/sintetica-start`. | Must | Sem `intent.json`, o comando termina com erro e a mensagem cita `/sintetica-start`. | 🟡 |
| RF-02 | O sistema deve validar a definição `schema.json` (nome, tipo, obrigatório, descrição e restrições de cada campo) e devolver todos os erros encontrados, com o caminho do campo. | Must | Uma definição com 2 erros devolve as 2 mensagens com os caminhos. | 🟡 |
| RF-03 | O sistema deve suportar 9 tipos: texto, inteiro, decimal, booleano, data, data-hora, enum, lista e objeto aninhado. | Must | Uma definição com os 9 tipos gera um modelo que aceita 1 registro válido de cada tipo. | 🟡 |
| RF-04 | O sistema deve suportar 7 restrições: obrigatório, mínimo, máximo, tamanho mínimo, tamanho máximo, padrão regex e valores permitidos. | Must | Para cada restrição, 1 registro que a viola é rejeitado. | 🟡 |
| RF-05 | O sistema deve gerar `schema.py`, com a classe raiz `Record`, por um gerador determinístico (RN-01, RN-02). | Must | 2 gerações da mesma definição produzem arquivos idênticos byte a byte. | 🟡 |
| RF-06 | Para formato JSONL conversacional, o sistema deve gerar `Record` com `messages` (lista de papel `system`, `user` ou `assistant` e conteúdo, mínimo 1 mensagem) e `labels` (objeto com os campos de rótulo definidos pelo usuário). | Must | Um registro com papel `bot` é rejeitado; um registro com 2 mensagens válidas e rótulos válidos é aceito. | 🟡 |
| RF-07 | Para formato CSV, o sistema deve aplicar a RN-04: achatar objetos com prefixo, serializar listas simples com `|`, recusar listas de objetos, e avisar o usuário de cada transformação. | Must | `endereco.cidade` vira `endereco_cidade`; a lista `["a","b"]` vira a célula `a|b`; uma lista de objetos gera erro que cita JSON ou JSONL. | 🟡 |
| RF-08 | O sistema deve normalizar nomes de campo pela RN-03. | Must | `Nome Completo` vira `nome_completo`; `class` vira `class_`; 2 campos `Idade` viram `idade` e `idade_2`. | 🟡 |
| RF-09 | O sistema deve recusar restrições contraditórias e mostrar os 2 valores em conflito. | Must | Mínimo 90 e máximo 18 geram erro com "90" e "18". | 🟡 |
| RF-10 | O sistema deve recusar padrão regex que não compila e lista de valores permitidos vazia. | Must | O padrão `(abc` gera erro com o caminho do campo. | 🟡 |
| RF-11 | O sistema deve recusar definições acima de 100 campos e pedir a divisão do dataset (RN-06). | Must | 101 campos geram erro com a contagem. | 🟡 |
| RF-12 | O sistema deve validar o contrato gerado antes de mostrá-lo (RN-08): o código importa, a classe `Record` existe e exporta JSON Schema. | Must | Um defeito simulado no gerador impede a exibição e grava o erro em `datasets/<slug>/errors.log`. | 🟡 |
| RF-19 | O sistema deve aplicar a RN-09 ao tipo decimal e oferecer a serialização de um registro válido para JSON, JSONL e CSV conforme o contrato. | Must | Com `casas_decimais` 2, a entrada `"19.9"` é aceita; no JSON sai `19.90` como número e no CSV sai o texto `19.90`. | 🟡 |
| RF-20 | A suíte de testes do gerador deve verificar, com tipagem estrita e lint, o código gerado para cada tipo, restrição e caso de borda (RN-08). | Must | A suíte falha se algum `schema.py` de teste tiver erro de tipagem ou de lint. | 🟡 |
| RF-13 | O sistema deve exportar o JSON Schema de `Record` em `datasets/<slug>/record.schema.json`, no formato aceito por `sintetica request --schema`. | Must | O arquivo exportado é aceito pelo comando `sintetica request`. | 🟡 |
| RF-14 | O sistema deve mostrar o contrato como tabela Markdown com as colunas campo, tipo, obrigatório, restrições e descrição, com campos aninhados em notação de ponto. | Must | Um contrato com 1 objeto aninhado mostra `endereco.cidade` na tabela. | 🟡 |
| RF-15 | Em ajustes, o sistema deve mostrar as diferenças em relação à versão anterior: campos novos, removidos e alterados. | Must | Mudar o máximo de `idade` de 90 para 80 mostra 1 campo alterado. | 🟡 |
| RF-16 | O sistema deve contar as rodadas de ajuste e, na 5ª sem aprovação, sugerir `/sintetica-start` (RN-06). | Should | Na 5ª rodada, a sugestão aparece. | 🟡 |
| RF-17 | O sistema deve gravar `schema_version` (RN-05) e marcar o contrato como aprovado só após a confirmação do usuário, ou de forma automática no modo Expresso. | Must | Sem confirmação no modo Guiado, o estado continua "em revisão"; no modo Expresso, vira "aprovado" sem pergunta. | 🟡 |
| RF-18 | O sistema deve gerar o contrato da RN-07 quando a estrutura da intenção estiver indefinida. | Should | Intenção com estrutura indefinida gera o campo `descricao` e o aviso. | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | Validação, geração e exportação em ≤ 10 s, sem contar o modelo de linguagem. | `_reversa_sdd/sdd/schema-builder.md#7` (RNF-04) | 🟡 |
| Segurança | 0 trechos de texto da definição interpretados como código (RN-02). | `_reversa_sdd/sdd/schema-builder.md#12` | 🟡 |
| Reprodutibilidade | Mesma definição gera o mesmo código e a mesma versão. | RF-05, RN-05 | 🟡 |
| Qualidade do código gerado | Todo código produzido pelo gerador passa em tipagem estrita e lint, verificado na suíte de testes. | `_reversa_sdd/sdd/schema-builder.md#7` (RNF-02) | 🟡 |
| Qualidade | Tipagem estrita e lint sem erros no módulo; cobertura ≥ 80%. | `_reversa_sdd/questions.md#Q19` | 🟡 |
| Plataforma | Runtime Python ≥ 3.10. | `_reversa_sdd/questions.md#Q18` | 🟡 |
| Privacidade | O contrato guarda só nomes, tipos, restrições e descrições; nenhum valor de registro. | `_reversa_sdd/sdd/schema-builder.md#12` | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Contrato de pedidos aprovado no modo Guiado
  Dado uma intenção definida com formato JSON
  E uma definição com 5 campos válidos
  Quando o sistema valida e gera o contrato
  Então schema.py, record.schema.json e a tabela de 5 linhas existem
  E o estado é "em revisão" até o usuário confirmar

Cenário: Modo Expresso aprova sem pergunta
  Dado uma intenção no modo Expresso e uma definição válida
  Quando o sistema gera o contrato
  Então o estado é "aprovado" sem confirmação

Cenário: Intenção ausente
  Dado um dataset sem intent.json
  Quando o comando de schema roda
  Então o comando termina com erro que cita /sintetica-start

Cenário: Os 9 tipos geram um modelo válido
  Dado uma definição com texto, inteiro, decimal, booleano, data, data-hora, enum, lista e objeto
  Quando o sistema gera o contrato
  Então 1 registro válido de cada tipo é aceito pelo Record

Cenário: Cada restrição rejeita o valor que a viola
  Dado uma definição com as 7 restrições
  Quando um registro viola uma delas
  Então o Record rejeita o registro

Cenário: Geração determinística
  Dado a mesma definição
  Quando o sistema gera o contrato 2 vezes
  Então os 2 schema.py são idênticos byte a byte e a versão é a mesma

Cenário: Reformatar a definição não muda a versão
  Dado uma definição com as chaves em outra ordem e outra indentação
  Quando o sistema calcula a versão
  Então a versão é igual à da definição original

Cenário: Texto malicioso na descrição não vira código
  Dado uma descrição com aspas, quebra de linha e o texto "import os"
  Quando o sistema gera o contrato
  Então o código gerado importa sem executar o texto
  E a descrição aparece intacta no JSON Schema exportado

Cenário: Contrato de conversa
  Dado uma intenção JSONL do engenheiro-de-ml com rótulo "sentimento"
  Quando o sistema gera o contrato
  Então o Record exige messages e labels.sentimento
  E uma mensagem com papel "bot" é rejeitada

Cenário: Objeto aninhado em CSV é achatado
  Dado uma intenção CSV com o objeto endereco e o campo cidade
  Quando o sistema gera o contrato
  Então a coluna endereco_cidade existe
  E o usuário recebe o aviso de achatamento

Cenário: Lista simples em CSV vira 1 coluna
  Dado uma intenção CSV com a lista de textos "tags"
  Quando o sistema gera o contrato e serializa o registro com tags ["a", "b"]
  Então a célula da coluna tags é "a|b"
  E um item com o caractere "|" é rejeitado pelo Record

Cenário: Lista de objetos em CSV é recusada
  Dado uma intenção CSV com uma lista de objetos "itens"
  Quando o sistema valida a definição
  Então a validação falha com mensagem que orienta usar JSON ou JSONL

Cenário: Decimal com casas definidas
  Dado o campo preco do tipo decimal com casas_decimais 2
  Quando o Record recebe o texto "19.9"
  Então o registro é aceito
  E o JSON sai com o número 19.90 e o CSV com o texto 19.90

Cenário: Normalização de nomes
  Dado os campos "Nome Completo", "class", "Idade" e "idade"
  Quando o sistema normaliza os nomes
  Então os nomes são nome_completo, class_, idade e idade_2

Cenário: Restrições contraditórias
  Dado o campo idade com mínimo 90 e máximo 18
  Quando o sistema valida a definição
  Então a validação falha com os valores 90 e 18 na mensagem

Cenário: Regex inválida
  Dado o campo codigo com o padrão "(abc"
  Quando o sistema valida a definição
  Então a validação falha com o caminho do campo

Cenário: Excesso de campos
  Dado uma definição com 101 campos
  Quando o sistema valida a definição
  Então a validação falha e pede para dividir o dataset

Cenário: Defeito no gerador não chega ao usuário
  Dado um gerador que produz código que não importa
  Quando o sistema valida o contrato gerado
  Então a tabela não é mostrada
  E o erro é gravado em errors.log

Cenário: Ajuste mostra as diferenças
  Dado um contrato com idade máxima 90
  Quando o ajuste muda o máximo para 80
  Então a saída mostra 1 campo alterado e a versão nova

Cenário: Rodadas de ajuste esgotadas
  Dado 4 rodadas de ajuste sem aprovação
  Quando o usuário pede o 5º ajuste
  Então o sistema sugere /sintetica-start

Cenário: Estrutura indefinida
  Dado uma intenção com estrutura indefinida
  Quando o sistema gera o contrato
  Então o Record tem o campo descricao com a descrição "a definir"
  E o usuário recebe o aviso

Cenário: JSON Schema aceito pelo provedor
  Dado um contrato gerado
  Quando o sistema exporta record.schema.json
  Então o comando sintetica request aceita o arquivo no argumento --schema
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 a RF-06, RF-08 a RF-11 | Must | Definem o contrato que mede a conformidade do PRD. |
| RF-07 | Must | O `analista-de-dados` depende de CSV plano; depende da RN-04. |
| RF-12, RF-20 | Must | Nenhum contrato defeituoso chega ao usuário (RN-08, Q36). |
| RF-19 | Must | Formato do valor no dataset final (Q37). |
| RF-13 | Must | Integração com o `llm-provider` entregue (`sintetica request --schema`). |
| RF-14, RF-15, RF-17 | Must | Revisão sem ler código (G-02 da spec). |
| RF-16, RF-18 | Should | Melhoram a experiência; o fluxo funciona sem eles. |
| RNF de segurança | Must | O código gerado roda no processo do usuário. |

## 9. Esclarecimentos

### Sessão 2026-10-12

> Respostas do revisor Antigravity em `_reversa_sdd/questions.md` (bloco "Etapa 9, /reversa-clarify da feature 003-schema-builder").

- **Q:** Como tratar listas em formato CSV (RN-04, RF-07)?
  **R:** Lista de valores simples vira 1 coluna serializada com `|`. Lista de objetos é recusada, com orientação para usar JSON ou JSONL.
- **Q:** Onde roda a verificação estrita de tipos do `schema.py` gerado (RN-08, RF-12)?
  **R:** Na suíte de testes do gerador, com tipagem estrita e lint. No runtime do usuário, a validação é por importação e exportação do JSON Schema.
- **Q:** Como representar valores decimais (RF-03)?
  **R:** Entrada como número ou texto numérico, restrição opcional `casas_decimais`; número em JSON e JSONL; texto com as casas fixadas em CSV.

## 10. Lacunas

- Nenhuma lacuna aberta. As 2 dúvidas iniciais e a lacuna de decimais foram resolvidas na sessão de 2026-10-12.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-12 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-12 | Esclarecimentos Q35 a Q37 integrados; RN-09, RF-19 e RF-20 adicionados; dúvidas zeradas | reversa-clarify |
