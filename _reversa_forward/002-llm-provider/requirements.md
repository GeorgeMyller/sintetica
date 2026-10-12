# Requirements: llm-provider (porta de geração por LLM, custo e mascaramento)

> Identificador: `002-llm-provider`
> Data: `2026-10-09`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA
> Cenário: greenfield. As fontes são artefatos planejados, mais o adendo vigente `_reversa_sdd/addenda/001-pii-guard.md`, que registra o `pii-guard` já entregue.

## 1. Resumo executivo

🟡 O `llm-provider` é a porta única pela qual o sintetica pede registros a um modelo de linguagem (LLM, *Large Language Model*).
🟡 Ele oferece 2 adaptadores: o provedor externo (OpenAI, Anthropic, Gemini e Ollama local) e o provedor do harness (o próprio agente do assistente de IA).
🟡 Ele escolhe o provedor pela política do projeto, estima o custo antes do lote, aplica o teto de US$ 5,00 e mascara PII antes de qualquer envio externo.
🟡 Ele resolve 2 problemas: cada usuário teria de escrever um cliente por API, e o custo só apareceria na fatura.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/sdd/llm-provider.md#1. Resumo` | Porta `LLMProvider` com 2 adaptadores; estimativa de custo e autorização acima de US$ 5,00 | 🟡 |
| `_reversa_sdd/sdd/llm-provider.md#6. Requisitos Funcionais` | RF-01 a RF-11: backends, prioridade, limite do harness, mascaramento, custo, teto, retry, concorrência | 🟡 |
| `_reversa_sdd/sdd/llm-provider.md#11. Edge Cases e Tratamento de Erros` | 429, timeout, 401/403, preço ausente, teto no meio do lote, resposta malformada | 🟡 |
| `_reversa_sdd/questions.md#Q8` | Interface abstrata com `ExternalAPIProvider` e `HarnessAgentProvider` | 🟡 |
| `_reversa_sdd/questions.md#Q17` | Autorização explícita quando o custo estimado passa de US$ 5,00 | 🟡 |
| `_reversa_sdd/questions.md#Q21` | Mascaramento preventivo antes de qualquer trânsito ao provedor externo; prioridade ao harness ou Ollama | 🟡 |
| `_reversa_sdd/sdd/cli-installer.md#6. Requisitos Funcionais` (RF-06) | Valores padrão de `policy.json`: `pii_premask`, `cost_ceiling_usd`, `provider_priority` | 🟡 |
| `_reversa_sdd/addenda/001-pii-guard.md#Impacto por artefato da extração` | `PiiGuard` entregue; consumidores devem usar a fachada e tratar exceções como falha segura | 🟢 |

> A última linha recebe 🟢 porque descreve código entregue e aprovado na feature 001, não um plano.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| `engenheiro-de-ml` | Gerar 1.000 a 10.000 conversas rotuladas | 🟡 O lote usa uma API externa; o sistema mostra o custo estimado e pede autorização acima de US$ 5,00. |
| `dev-de-testes` | Gerar até 100 registros de teste sem chave de API | 🟡 O lote usa o próprio agente do harness, com custo zero. |
| `analista-de-dados` | Gerar dados sem enviar nada para fora da máquina | 🟡 O lote usa o Ollama local. |
| Componentes `sample-preview` e `batch-generator` | Pedir registros sem conhecer o backend | 🟡 Chamam a porta única e recebem registros, tokens e custo. |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** 🟡 O provedor é escolhido pela ordem de `provider_priority` da política do projeto. Provedores indisponíveis são pulados.
   - Origem: `_reversa_sdd/sdd/llm-provider.md#6` (RF-03), `_reversa_sdd/questions.md#Q21`
   - Tipo: nova
2. **RN-02:** 🟡 O provedor do harness atende só pedidos de até 100 registros. O runtime Python obtém os registros do agente por um protocolo em 2 passos por arquivo:
   1. `uv run sintetica request <slug>` grava `datasets/<slug>/requests/<id>.json` com instruções, schema e sementes, e mostra o pedido ao agente.
   2. O agente gera os registros e executa `uv run sintetica submit <slug> <id>`, com o JSONL na entrada padrão. O `HarnessAgentProvider` lê a resposta, valida o formato e devolve o resultado comum da porta.
   - Origem: `_reversa_sdd/sdd/llm-provider.md#6` (RF-04), `_reversa_sdd/sdd/sample-preview.md#14` (OQ-02), `_reversa_sdd/questions.md#Q29`
   - Tipo: nova
3. **RN-03:** 🟡 Todo o conteúdo de um pedido passa pelo mascaramento de PII antes de sair para um provedor externo, quando `pii_premask` está ativo. Sem o mascaramento disponível, o pedido é recusado.
   - Origem: `_reversa_sdd/questions.md#Q21`, `_reversa_sdd/sdd/llm-provider.md#10`
   - Tipo: nova
4. **RN-04:** 🟡 O mascaramento da RN-03 vale para os 4 backends externos: OpenAI, Anthropic, Gemini e Ollama. O Ollama é mascarado sempre, mesmo com `OLLAMA_HOST` local (falha segura). O provedor do harness não é externo e não passa pela RN-03.
   - Origem: `_reversa_sdd/sdd/llm-provider.md#14` (OQ-03), `_reversa_sdd/questions.md#Q30`
   - Tipo: nova
5. **RN-05:** 🟡 O custo estimado é `registros × tokens médios por registro × preço por token`. Harness e Ollama custam US$ 0. Modelo sem preço conhecido é tratado como acima do teto.
   - Preços: tabela embutida no pacote, sobrescrita entrada a entrada por `.sintetica/pricing.json`.
   - Origem: `_reversa_sdd/sdd/llm-provider.md#6` (RF-06), `#11` (EC-04), `_reversa_sdd/questions.md#Q31`
   - Tipo: nova
6. **RN-06:** 🟡 Custo estimado acima de `cost_ceiling_usd` (padrão US$ 5,00) exige autorização explícita antes do primeiro pedido. Durante a geração, o custo acumulado nunca ultrapassa o valor autorizado.
   - Origem: `_reversa_sdd/questions.md#Q17`, `_reversa_sdd/sdd/llm-provider.md#6` (RF-07, RF-08)
   - Tipo: nova
7. **RN-07:** 🟡 Chaves de API vêm apenas de variáveis de ambiente e nunca aparecem em logs, arquivos ou relatórios.
   - Origem: `_reversa_sdd/sdd/llm-provider.md#7` (RNF-04)
   - Tipo: nova
8. **RN-08:** 🟡 Cada backend externo tem modelo padrão embutido no pacote. O usuário sobrescreve por `SINTETICA_OPENAI_MODEL`, `SINTETICA_ANTHROPIC_MODEL`, `SINTETICA_GEMINI_MODEL` ou `SINTETICA_OLLAMA_MODEL`. Os padrões e a tabela de preços são atualizados a cada versão do sintetica.
   - Padrões indicados pelo revisor: `gpt-4o-mini`, `claude-3-5-haiku-latest`, `gemini-1.5-flash`, `llama3.2`. 🟡 Validar os identificadores vigentes antes do coding (ver Lacunas).
   - Origem: `_reversa_sdd/sdd/llm-provider.md#14` (OQ-01, OQ-02), `_reversa_sdd/questions.md#Q31`
   - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O sistema deve oferecer uma porta única de geração, assíncrona, com as operações gerar, estimar custo, nome e indicador de execução local. | Must | Os 2 adaptadores passam no mesmo conjunto de testes de contrato. | 🟡 |
| RF-02 | O provedor externo deve suportar os backends `openai`, `anthropic`, `gemini` e `ollama`, com chaves em `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` e `GEMINI_API_KEY`, e endereço em `OLLAMA_HOST` (padrão `http://localhost:11434`). O modelo de cada backend segue a RN-08. | Must | Com um servidor simulado por backend, cada um devolve registros no formato comum. Com `SINTETICA_OPENAI_MODEL=x`, o pedido enviado usa o modelo `x`. | 🟡 |
| RF-03 | O sistema deve escolher o provedor pela RN-01 e informar qual escolheu e por quê. | Must | Com prioridade `harness, ollama, external`, Ollama desligado e pedido de 101 registros, o escolhido é `external`. | 🟡 |
| RF-04 | O provedor do harness deve seguir o protocolo `request`/`submit` da RN-02 e recusar pedidos acima de 100 registros com erro de limite. | Must | Pedido de 101 registros gera o erro de limite do harness. `submit` com JSONL válido devolve o resultado comum; `submit` com JSONL malformado ou id de pedido inexistente devolve erro sem gravar resultado. | 🟡 |
| RF-14 | O sistema deve gravar cada pedido do harness em `datasets/<slug>/requests/<id>.json` e a resposta correspondente ao lado, para auditoria. | Must | Após `request` e `submit`, a pasta contém o pedido e a resposta com o mesmo `<id>`. | 🟡 |
| RF-05 | O sistema deve aplicar a RN-03 ao pedido inteiro (instruções, sementes e schema) antes do envio externo. | Must | Com um e-mail real nas instruções, o conteúdo enviado ao servidor simulado contém só o valor falso. | 🟡 |
| RF-06 | O sistema deve estimar o custo pela RN-05, com a tabela de preços embutida e as sobrescritas de `.sintetica/pricing.json`. | Must | 1.000 registros, 500 tokens e US$ 0,00001 por token resultam em US$ 5,00. Uma entrada em `pricing.json` substitui o preço embutido do mesmo modelo. | 🟡 |
| RF-07 | O sistema deve marcar a estimativa como "exige autorização" quando o valor passar do teto, e o lote só começa após resposta `sim`. | Must | Estimativa de US$ 5,01 exige autorização; US$ 5,00 não exige. | 🟡 |
| RF-08 | O sistema deve parar de enviar pedidos quando o custo acumulado atingir o valor autorizado e devolver os registros já obtidos com o motivo da parada. | Must | Com teto de US$ 1,00 e US$ 0,40 por pedido, o 3º pedido não é enviado e o motivo é "teto de custo". | 🟡 |
| RF-09 | O sistema deve repetir pedidos com erro 429, erro 5xx, timeout de 60 s ou resposta malformada, com espera de 1 s, 2 s e 4 s, no máximo 3 tentativas. | Must | Servidor simulado com 2 erros 503 e depois sucesso recebe 3 chamadas e devolve 1 resultado. | 🟡 |
| RF-10 | O sistema não deve repetir pedidos com erro 401 ou 403 e deve encerrar com mensagem que cita o nome da variável de ambiente da chave, sem o valor. | Must | Chave inválida gera 1 chamada e mensagem com `OPENAI_API_KEY`. | 🟡 |
| RF-11 | O sistema deve limitar a concorrência por provedor a 8 pedidos simultâneos por padrão, com ajuste pelo chamador. | Should | Com 100 pedidos, nunca há mais de 8 em andamento. | 🟡 |
| RF-12 | O sistema deve informar, quando nenhum provedor estiver disponível, a lista de variáveis de ambiente e de endereços verificados. | Must | Sem chaves e sem Ollama, a mensagem lista as 3 variáveis e `OLLAMA_HOST`. | 🟡 |
| RF-13 | O sistema deve devolver em cada resultado os registros brutos (ainda não validados pelo schema), os tokens de entrada, os tokens de saída e o custo real. | Must | O resultado de um pedido simulado traz os 4 campos. | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Segurança | 0 chaves de API em logs, arquivos ou relatórios. | RN-07 | 🟡 |
| Privacidade | 0 pedidos externos sem passar pelo mascaramento quando `pii_premask` está ativo. | `_reversa_sdd/sdd/llm-provider.md#3` (G-02) | 🟡 |
| Precisão de custo | Erro da estimativa ≤ 25% do custo real. | `_reversa_sdd/sdd/llm-provider.md#3` (G-04) | 🟡 |
| Desempenho | Timeout de 60 s por pedido; concorrência padrão de 8. | RF-09, RF-11 | 🟡 |
| Testabilidade | Toda a suíte roda sem rede, com servidores simulados. | `_reversa_sdd/questions.md#Q15` (sem chamadas não autorizadas) | 🟡 |
| Qualidade | Tipagem estrita e lint sem erros; cobertura ≥ 80%. | `_reversa_sdd/questions.md#Q19` | 🟡 |
| Plataforma | Runtime Python ≥ 3.10 com concorrência assíncrona nativa. | `_reversa_sdd/questions.md#Q18` | 🟡 |
| Observabilidade | Cada resultado registra provedor, tokens e custo, para o `run.json` do gerador. | `_reversa_sdd/sdd/llm-provider.md#12` | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Lote de teste usa o harness sem custo
  Dado a prioridade "harness, ollama, external" e o harness disponível
  Quando o gerador pede 50 registros
  Então o provedor escolhido é "harness"
  E a estimativa de custo é US$ 0 e não exige autorização

Cenário: Lote grande pula harness e Ollama indisponível
  Dado a prioridade "harness, ollama, external", Ollama desligado e OPENAI_API_KEY definida
  Quando o gerador pede 1.000 registros
  Então o provedor escolhido é "external" com backend "openai"

Cenário: Harness recusa pedido acima do limite
  Dado o provedor do harness
  Quando ele recebe um pedido de 101 registros
  Então ele devolve o erro de limite do harness

Cenário: Protocolo do harness em 2 passos
  Dado um pedido do harness gravado por "sintetica request" com id "r1"
  Quando o agente executa "sintetica submit" com 10 registros JSONL válidos para "r1"
  Então o provedor do harness devolve 10 registros brutos com custo US$ 0
  E a pasta requests contém o pedido e a resposta de "r1"

Cenário: Submit com pedido inexistente
  Dado nenhum pedido gravado com id "r9"
  Quando o agente executa "sintetica submit" para "r9"
  Então o sistema devolve erro de pedido inexistente e não grava resposta

Cenário: Ollama também recebe conteúdo mascarado
  Dado pii_premask ativo, backend "ollama" com OLLAMA_HOST local e instruções com "ana@empresa.com"
  Quando o provedor externo envia o pedido
  Então o conteúdo recebido pelo servidor simulado não contém "ana@empresa.com"

Cenário: Preço do projeto sobrescreve o preço embutido
  Dado o preço embutido de US$ 0,00001 por token para o modelo "m" e pricing.json com US$ 0,00002 para "m"
  Quando o sistema estima 100 registros de 500 tokens com o modelo "m"
  Então a estimativa é US$ 1,00

Cenário: Nenhum provedor disponível
  Dado nenhuma chave de API definida e o Ollama desligado
  Quando o gerador pede 1.000 registros
  Então o sistema encerra com mensagem que lista OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY e OLLAMA_HOST

Cenário: PII mascarada antes do envio externo
  Dado pii_premask ativo e instruções com "ana@empresa.com"
  Quando o provedor externo envia o pedido
  Então o conteúdo recebido pelo servidor simulado não contém "ana@empresa.com"

Cenário: Mascaramento indisponível bloqueia o envio
  Dado pii_premask ativo e uma política de PII inválida
  Quando o provedor externo prepara o pedido
  Então nenhum pedido é enviado e o erro de política é devolvido

Cenário: Estimativa exata no teto não pede autorização
  Dado o preço de US$ 0,00001 por token
  Quando o sistema estima 1.000 registros de 500 tokens
  Então a estimativa é US$ 5,00 e não exige autorização

Cenário: Estimativa acima do teto exige autorização
  Dado uma estimativa de US$ 5,01
  Quando o chamador consulta a estimativa
  Então a estimativa exige autorização

Cenário: Modelo sem preço conhecido
  Dado um modelo ausente de pricing.json
  Quando o sistema estima o custo
  Então a estimativa exige autorização

Cenário: Teto atingido no meio do lote
  Dado o valor autorizado de US$ 1,00 e custo real de US$ 0,40 por pedido
  Quando o lote envia pedidos em sequência
  Então o 3º pedido não é enviado
  E os registros dos 2 primeiros pedidos são devolvidos com o motivo "teto de custo"

Cenário: Retry em erro temporário
  Dado um servidor simulado que responde 503, 503 e depois 200
  Quando o provedor envia 1 pedido
  Então o servidor recebe 3 chamadas e o resultado traz os registros

Cenário: Esgotar tentativas
  Dado um servidor simulado que responde 429 sempre
  Quando o provedor envia 1 pedido
  Então o servidor recebe 3 chamadas e o pedido falha com o motivo "falha do provedor"

Cenário: Chave inválida não repete
  Dado um servidor simulado que responde 401
  Quando o provedor envia 1 pedido
  Então o servidor recebe 1 chamada
  E a mensagem cita OPENAI_API_KEY sem mostrar o valor da chave

Cenário: Resposta malformada conta como falha temporária
  Dado um servidor simulado que responde texto que não é JSON e depois uma resposta válida
  Quando o provedor envia 1 pedido
  Então o servidor recebe 2 chamadas e o resultado traz os registros

Cenário: Concorrência limitada
  Dado 100 pedidos e concorrência padrão
  Quando o provedor envia todos
  Então nunca há mais de 8 pedidos em andamento ao mesmo tempo

Cenário: Resultado traz tokens e custo
  Dado um servidor simulado que informa 100 tokens de entrada e 400 de saída
  Quando o provedor envia 1 pedido
  Então o resultado traz os registros brutos, 100, 400 e o custo calculado pelo preço do modelo
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-03, RF-12, RF-13 | Must | Contrato usado por `sample-preview` e `batch-generator`. |
| RF-02 | Must | Q8 lista os 4 backends. |
| RF-04, RF-14 | Must | Q8, Q10 e Q29: harness para lotes de teste, com protocolo auditável. |
| RF-05 | Must | Q21: privacidade por design. |
| RF-06, RF-07, RF-08 | Must | Q17: teto de orçamento. |
| RF-09, RF-10 | Must | Lotes de 10.000 registros não sobrevivem sem retry e sem falha rápida de credencial. |
| RF-11 | Should | Protege contra limite de taxa; o valor padrão é ajustável. |
| RNF de precisão de custo | Should | Meta de 3 meses; depende de `pricing.json` atualizado. |

## 9. Esclarecimentos

### Sessão 2026-10-09

> Respostas do revisor Antigravity em `_reversa_sdd/questions.md` (bloco "Etapa 7, /reversa-clarify da feature 002-llm-provider").

- **Q:** Como os registros gerados pelo agente do harness chegam ao runtime Python (RN-02, RF-04)?
  **R:** Protocolo em 2 passos por arquivo: `sintetica request` grava o pedido em `datasets/<slug>/requests/<id>.json`; o agente gera e envia o JSONL por `sintetica submit` na entrada padrão. Limite de 100 registros por pedido. Fronteira desacoplada, rastreável e auditável.
- **Q:** O mascaramento antes do envio vale para o Ollama (RN-04)?
  **R:** Sim. Mascarar sempre, independentemente de `OLLAMA_HOST` (falha segura).
- **Q:** Quais modelos padrão usar, e quem mantém `pricing.json` (RF-02, RF-06)?
  **R:** Modelos padrão e tabela de preços embutidos no pacote, atualizados a cada versão. Override total por `SINTETICA_*_MODEL` e por `.sintetica/pricing.json`. Padrões indicados: `gpt-4o-mini`, `claude-3-5-haiku-latest`, `gemini-1.5-flash`, `llama3.2`.

## 10. Lacunas

- Nenhum marcador `[DÚVIDA]` aberto. As 3 dúvidas iniciais foram resolvidas na sessão de 2026-10-09.
- 🟡 Ressalva (não bloqueia o plano): os identificadores de modelo indicados na Q31 parecem desatualizados para outubro de 2026. Exemplo: a família Claude 3.5 Haiku foi descontinuada; o Haiku vigente é `claude-haiku-5-5`. A estrutura da decisão (padrão embutido + override) não muda. Os identificadores ficam em um único arquivo de dados e serão confirmados na Q32 antes do coding.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-09 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-09 | Q29 a Q31 integradas; RN-08, RF-14 e 4 cenários novos | reversa-clarify |
