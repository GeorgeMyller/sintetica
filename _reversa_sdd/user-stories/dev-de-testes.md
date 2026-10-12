# User Stories: dev-de-testes (lote de teste em JSON ou CSV)

> Gerado pelo Redator do Reversa em 2026-10-12. 🟢 CONFORME CÓDIGO (`intent`, `schema`, `sample`, `batch`, `quality`).

## US-10 — Descrever o dataset sem jargão
**Como** dev-de-testes, **quero** dizer o que preciso em linguagem natural **para** não escrever gerador.

```gherkin
Cenário: Entrevista Guiada
  Dado o sintetica instalado
  Quando digito /sintetica-start
  Então a pasta datasets/<slug>/ existe e o caminho aparece antes da 1ª pergunta
  E respondo objetivo, estrutura, regras, formato JSON e volume 50
  E confirmo a intenção

Cenário: "Não sei" não trava
  Dado a pergunta de formato
  Quando respondo "não sei"
  Então o formato vira JSONL (padrão) e a entrevista continua
```
🟢 Prioridade: Must.

## US-11 — Revisar o contrato
**Como** dev-de-testes, **quero** ver a tabela de campos e ajustar **para** garantir os tipos certos.

```gherkin
Cenário: Contrato aprovado
  Dado a intenção confirmada
  Quando o agente grava o rascunho e roda schema build
  Então vejo a tabela com tipos e restrições
  E aprovo com schema approve

Cenário: Rascunho inválido
  Dado um campo enum sem choices
  Quando roda schema build
  Então o código é 6 com o caminho do problema
```
🟢 Prioridade: Must.

## US-12 — Aprovar uma amostra sem chave de API
**Como** dev-de-testes, **quero** ver 3 registros gerados pelo próprio agente **para** validar o estilo de graça.

```gherkin
Cenário: Amostra pelo harness
  Dado o contrato aprovado
  Quando roda sample run
  Então o agente responde o pedido por submit
  E vejo 3 registros válidos e aprovo

Cenário: Dado pessoal na resposta
  Dado uma resposta com um CPF real
  Quando a amostra é revisada
  Então o CPF vira um CPF falso e o original não fica em nenhum arquivo
```
🟢 Prioridade: Must.

## US-13 — Receber 50 registros validados
**Como** dev-de-testes, **quero** o lote em menos de 10 minutos **para** testar a tela hoje.

```gherkin
Cenário: Lote de teste com o harness
  Dado a amostra aprovada e volume 50
  Quando roda generate
  Então o agente responde 1 pedido de 50 registros
  E recebo output/dataset.json com status concluido
  E a avaliação mostra APROVADO e a duração
```
🟢 Prioridade: Must.
