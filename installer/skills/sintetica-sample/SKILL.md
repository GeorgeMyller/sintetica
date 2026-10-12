---
name: sintetica-sample
description: Gera e revisa uma amostra de 3 a 5 registros do dataset do sintetica antes do lote completo. Use depois do contrato aprovado (sintetica-schema).
---

# sintetica-sample: amostra para aprovação

Você gera os registros quando o runtime pede e mostra a amostra ao usuário. O runtime valida, descarta inválidos e duplicados e troca dados pessoais por valores falsos. Rode os comandos na raiz do projeto, pelo lançador `.sintetica/bin/sintetica`.

## Passos

1. Peça a amostra (padrão 3; use `--n 5` para 5):
   ```bash
   .sintetica/bin/sintetica sample run <slug>
   ```
2. Se a saída trouxer "Pedido para o agente":
   1. Leia o arquivo do pedido (`datasets/<slug>/requests/<id>.json`): instruções, JSON Schema e exemplos.
   2. Gere os registros com dados fictícios, 1 objeto JSON por linha, num arquivo temporário.
   3. Envie com o comando impresso:
      ```bash
      .sintetica/bin/sintetica submit <slug> <id> < registros.jsonl
      ```
      Código 5: a resposta não é 1 objeto JSON por linha; corrija e envie de novo.
   4. Rode `sample run <slug>` de novo. Repita até a saída mostrar a amostra (até 3 tentativas).
3. Mostre a amostra e ofereça as 3 opções:
   - aprovar: `.sintetica/bin/sintetica sample approve <slug>`;
   - ajustar: `.sintetica/bin/sintetica sample adjust <slug> '<pedido>'` e volte ao passo 2;
   - voltar ao contrato: skill `sintetica-schema`.
4. Depois da aprovação, siga com a skill `sintetica-generate`.
5. Para rever: `.sintetica/bin/sintetica sample show <slug>`.

## Regras

- No Expresso, a amostra com N registros válidos é aprovada sozinha; amostra parcial para o fluxo e pede decisão ao usuário.
- No Guiado, amostra parcial pode ser aprovada com pelo menos 1 registro, com alerta.
- Nunca escreva dados pessoais reais nos registros.

## Códigos de saída

| Código | Significado |
|--------|-------------|
| 0 | Sucesso (inclui "aguardando o agente") |
| 2 | Dataset, intenção ou argumento inválido |
| 9 | Mascaramento de PII indisponível |
| 10 | Falha de escrita |
| 11 | Contrato não aprovado ou desatualizado |
| 12 | Falha do provedor |
| 13 | Amostra não aprovável no estado atual |
