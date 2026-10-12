---
name: sintetica-start
description: Inicia um dataset sintético no sintetica e conduz a entrevista de intenção (objetivo, estrutura, regras, formato e volume), sem jargão técnico. Use quando o usuário pedir dados sintéticos, dados de teste, um dataset ou "/sintetica-start".
---

# sintetica-start: entrevista de intenção

Você conduz a conversa. O runtime cria a pasta, mascara dados pessoais, valida e grava cada resposta. Rode todos os comandos na raiz do projeto, pelo lançador `.sintetica/bin/sintetica` (no Windows, `.sintetica\bin\sintetica.cmd`).

## Passos

1. Antes da 1ª pergunta, crie o dataset e mostre ao usuário o caminho da linha `Pasta:`:
   ```bash
   .sintetica/bin/sintetica start '<nome do dataset>'            # modo Guiado
   .sintetica/bin/sintetica start '<nome do dataset>' --mode expresso
   ```
   Use o modo Expresso só se o usuário pedir para responder tudo de uma vez.
2. Mostre as perguntas:
   ```bash
   .sintetica/bin/sintetica intent questions --mode guiado
   ```
   - Guiado: faça 1 pergunta por vez, na ordem.
   - Expresso: faça as 5 numa única mensagem.
3. A cada resposta, registre com o slug impresso no passo 1 e mostre os avisos e o resumo devolvidos:
   ```bash
   .sintetica/bin/sintetica intent set <slug> --objective '<texto>' --structure '<texto>' \
     --rules '<texto>' --format json --volume 50
   ```
   - "Não sei": `--unknown <item>` (repetível; itens `objective`, `structure`, `rules`, `format`, `volume`).
   - Use aspas simples no texto do usuário. Uma aspa simples dentro do texto vira `'\''`.
4. Siga a última linha do resumo:
   - `Faltam: ...` → pergunte só os itens que faltam;
   - `Confirme ...` → mostre o resumo, peça "sim" e rode `.sintetica/bin/sintetica intent confirm <slug>`;
   - `Próximo passo: ... schema build <slug>` → siga com a skill `sintetica-schema`.
5. Para rever o estado: `.sintetica/bin/sintetica intent show <slug>`.

## Regras

- Não peça parâmetros técnicos (tipos, temperatura, modelo). Pergunte o que o usuário quer obter.
- Dados pessoais nas respostas viram valores falsos antes de qualquer gravação. Nunca repita o valor original.
- No Expresso, siga direto até o fim do pipeline. Só peça confirmação quando objetivo e estrutura forem "não sei".

## Códigos de saída

| Código | Significado |
|--------|-------------|
| 0 | Sucesso |
| 2 | Dataset ou intenção ausente, ou uso inválido |
| 8 | Resposta inválida, ou confirmação com intenção incompleta |
| 9 | Mascaramento de PII indisponível (`.sintetica/policy.json` inválido) |
| 10 | Falha de escrita |
