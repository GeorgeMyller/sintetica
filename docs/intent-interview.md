# intent-interview

Entrevista de intenção do sintetica: ponto de entrada da skill `sintetica-start`. O agente do harness conversa com o usuário; o runtime cria a pasta, mascara dados pessoais, valida e grava cada resposta em `datasets/<slug>/intent.json`.

> No projeto do usuário, instalado por `npx sintetica install`, os comandos rodam pelo lançador `.sintetica/bin/sintetica` no lugar de `uv run sintetica` (`docs/cli-installer.md`).

## Fluxo para a skill `sintetica-start`

1. Rode `uv run sintetica start "<nome>" [--mode expresso]` **antes** da primeira pergunta. Mostre ao usuário o caminho absoluto impresso na linha `Pasta:`.
2. Rode `uv run sintetica intent questions --mode <modo>` e faça as perguntas:
   - Guiado: 1 por vez, na ordem.
   - Expresso: as 5 numa única mensagem.
3. A cada resposta, rode `uv run sintetica intent set <slug> ...` e mostre ao usuário os avisos e o resumo devolvidos.
4. Siga a última linha do resumo:
   - `Faltam: ...` → pergunte os itens que faltam;
   - `Confirme ...` → mostre o resumo, peça "sim" e rode `uv run sintetica intent confirm <slug>`;
   - `Próximo passo: uv run sintetica schema build <slug>` → siga para o contrato de dados (`docs/schema-builder.md`).

## Registro de respostas

```bash
uv run sintetica intent set pedidos \
  --objective 'testar a tela de pedidos' \
  --structure 'cliente, bebida, tamanho, valor' \
  --rules 'valor entre 5 e 50 reais' \
  --format json --volume 50
```

- "Não sei": `--unknown <item>` (repetível). Itens: `objective`, `structure`, `rules`, `format`, `volume`.
- Padrões para "não sei": formato JSONL e volume 10, marcados como `(padrão)` no resumo.
- Formatos aceitos: CSV, JSON, JSONL (sem diferenciar maiúsculas).
- Volume: 1 a 10.000; aceita `2000`, `2.000` ou `2 000`. Na 3ª recusa seguida, vale o padrão 10.
- Cada chamada é tudo ou nada: com 1 item inválido, nada é gravado.
- Responder de novo um item já confirmado exige nova confirmação.

### Citação de textos no shell

Use aspas simples para o texto do usuário: elas evitam a expansão de `$`, crases e `!`. Uma aspa simples dentro do texto vira `'\''`:

```bash
uv run sintetica intent set pedidos --structure 'bebida '\''gelada'\'' e "VIP"'
```

## Privacidade

Objetivo, estrutura e regras passam pelo `pii-guard` antes de qualquer gravação. Dados pessoais viram valores falsos do mesmo tipo; o aviso cita o item e os tipos (`e-mail (1)`), nunca o valor original. Se a política de PII (`.sintetica/policy.json`) for inválida, nada é gravado (código 9).

## Confirmação

| Modo | Precisa confirmar? |
|------|--------------------|
| Guiado | Sempre, depois da intenção completa |
| Expresso | Só se objetivo **e** estrutura forem "não sei" (o contrato terá 1 campo genérico) |

## Códigos de saída

| Código | Significado |
|--------|-------------|
| 0 | Sucesso |
| 2 | Dataset ou intenção ausente, ou uso inválido (nenhum item; item e `--unknown` juntos) |
| 8 | Resposta inválida, ou confirmação com intenção incompleta |
| 9 | Mascaramento de PII indisponível |
| 10 | Falha de escrita |

## API

```python
from sintetica.intent import Answers, start, set_answers, show, confirm, load_intent_model

start(project_dir, "Pedidos de Café", "guiado")
set_answers(project_dir, "pedidos-de-cafe", Answers({"objective": "..."}, format="json", volume="50"))
intent = load_intent_model(project_dir / "datasets" / "pedidos-de-cafe")
```
