# User Stories: analista-de-dados (CSV com regras de negócio)

> Gerado pelo Redator do Reversa em 2026-10-12. 🟢 CONFORME CÓDIGO.

## US-30 — CSV que respeita as regras
**Como** analista-de-dados, **quero** colunas com tipos e restrições **para** carregar no meu pipeline.

```gherkin
Cenário: Objeto aninhado em CSV
  Dado um campo endereco com cidade
  Quando roda schema build com formato csv
  Então a coluna é endereco_cidade e há aviso de achatamento

Cenário: Lista em CSV
  Dado um campo tags como lista de texto
  Quando o dataset é gerado
  Então a célula traz os itens separados por |

Cenário: Decimal com casas fixas
  Dado um campo saldo decimal com 2 casas
  Quando o CSV é gerado
  Então 1.5 aparece como 1.50
```
🟢 Prioridade: Must.

## US-31 — Arquivo CSV padrão
**Como** analista-de-dados, **quero** um CSV que abra em qualquer leitor **para** não tratar o arquivo.

```gherkin
Cenário: RFC 4180
  Dado um nome com vírgula e aspas
  Quando output/dataset.csv é gerado
  Então o campo vem entre aspas com as aspas duplicadas
  E o cabeçalho segue a ordem do contrato e as linhas terminam em CRLF
```
🟢 Prioridade: Must.

## US-32 — Ver os registros com problema
**Como** analista-de-dados, **quero** os índices dos registros inválidos **para** corrigir o contrato.

```gherkin
Cenário: Linha com colunas a mais
  Dado um CSV editado com uma linha de colunas a mais
  Quando roda sintetica eval
  Então a linha conta como inválida e o índice aparece no report.md
```
🟢 Prioridade: Should.
