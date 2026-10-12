# User Stories: engenheiro-de-ml (conversas para fine-tuning)

> Gerado pelo Redator do Reversa em 2026-10-12. 🟢 CONFORME CÓDIGO.

## US-20 — Contrato de conversa
**Como** engenheiro-de-ml, **quero** registros com mensagens e rótulos **para** fine-tuning.

```gherkin
Cenário: Conversa em JSONL
  Dado um rascunho com kind conversation e rótulo enum sentimento
  Quando roda schema build
  Então o Record tem messages (system, user, assistant) e labels

Cenário: Conversa em CSV
  Dado kind conversation e formato csv
  Quando roda schema build
  Então o código é 6
```
🟢 Prioridade: Must.

## US-21 — Gerar 2.000 conversas sem prender o chat
**Como** engenheiro-de-ml, **quero** o lote em background com custo controlado **para** seguir trabalhando.

```gherkin
Cenário: Autorização de custo
  Dado uma estimativa de US$ 6,00 acima do teto de US$ 5,00
  Quando roda generate
  Então nenhum pedido sai e o código é 15 com o comando --authorize-usd 6.00
  E com a minha autorização o lote começa

Cenário: Background
  Dado volume 2.000 e Ollama ou uma chave de API
  Quando roda generate
  Então o comando volta em até 5 s com o PID
  E status mostra aceitos, descartados, custo e rodada

Cenário: Conversas longas
  Dado uma amostra com mensagens de ~1.000 tokens
  Quando o lote começa
  Então cada pedido tem 4 registros
```
🟢 Prioridade: Must.

## US-22 — Retomar depois de uma queda
**Como** engenheiro-de-ml, **quero** retomar sem repetir custo **para** não perder o que já foi gerado.

```gherkin
Cenário: Processo encerrado
  Dado o processo do lote encerrado no meio
  Quando roda status
  Então vejo "Processo encerrado" e o comando --resume
  E generate --resume conclui sem duplicados nem blocos repetidos

Cenário: Teto atingido
  Dado o lote em interrompido_custo
  Quando roda generate --resume --authorize-usd 20
  Então o teto do restante é 20 menos o já gasto
```
🟢 Prioridade: Must.

## US-23 — Saber se as conversas são diversas
**Como** engenheiro-de-ml, **quero** a unicidade semântica e os vazamentos **para** decidir se uso o dataset.

```gherkin
Cenário: Quase-duplicados
  Dado 2 conversas que diferem só em pontuação
  Quando a avaliação roda
  Então a posterior conta como quase-duplicada

Cenário: CI
  Dado um dataset reprovado
  Quando a CI roda sintetica eval
  Então o código é 17
```
🟢 Prioridade: Must.
