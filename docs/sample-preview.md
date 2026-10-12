# sample-preview

Amostra de 3 a 5 registros para aprovação antes da geração em lote. É a skill `sintetica-sample`. O runtime pede os registros pelo provedor da política (o agente do harness, no padrão), valida cada um pelo contrato do dataset, troca dados pessoais por valores falsos e mostra a amostra.

> No projeto do usuário, instalado por `npx sintetica install`, os comandos rodam pelo lançador `.sintetica/bin/sintetica` no lugar de `uv run sintetica` (`docs/cli-installer.md`).

## Pré-condições

- Intenção registrada (`docs/intent-interview.md`).
- Contrato aprovado e atual (`uv run sintetica schema approve <slug>`; no Expresso, o `build` já aprova).

## Fluxo para a skill `sintetica-sample`

1. Rode `uv run sintetica sample run <slug>` (padrão: 3 registros; use `--n 5` para 5).
2. Se a saída trouxer "Pedido para o agente", leia o arquivo do pedido, gere os registros e envie:
   ```bash
   uv run sintetica submit <slug> <id> < registros.jsonl
   ```
   O `submit` recusa texto que não seja 1 objeto JSON por linha (código 5); corrija e envie de novo.
3. Rode `uv run sintetica sample run <slug>` de novo. O runtime lê a resposta, descarta inválidos e duplicados e, se faltarem registros, grava um novo pedido (até 3 tentativas). Repita os passos 2 e 3 até a saída mostrar a amostra.
4. Mostre a amostra ao usuário e ofereça as 3 opções:
   - **aprovar:** `uv run sintetica sample approve <slug>`;
   - **ajustar:** `uv run sintetica sample adjust <slug> '<pedido>'` e volte ao passo 2;
   - **voltar ao contrato:** edite `schema.draft.json` e rode `uv run sintetica schema build <slug>`; a amostra antiga é descartada.

## Regras

- Cada registro é validado pelo contrato; o motivo do descarte cita o campo e a regra, nunca o valor.
- Dados pessoais da resposta viram valores falsos antes de aparecer na tela ou no disco. A resposta bruta do agente é apagada depois de lida.
- A partir da 4ª rodada de ajuste, a saída sugere voltar ao contrato.
- Depois de 3 tentativas com registros faltando:
  - Guiado: a amostra parcial pode ser aprovada (com pelo menos 1 registro), com alerta;
  - Expresso: a automação para e pede decisão.
- No Expresso, a amostra com N registros válidos é aprovada na mesma chamada.

## Arquivos

| Arquivo | Conteúdo |
|---------|----------|
| `datasets/<slug>/sample.state.json` | Estado da rodada (aguardando_agente, em_revisao, aprovada, interrompida) |
| `datasets/<slug>/seeds/sample.jsonl` | Amostra aprovada, 1 registro por linha, pronta para `sintetica request --seeds` |
| `datasets/<slug>/seeds/sample.meta.json` | Versão do contrato, data, provedor, registros pedidos e aprovados, parcial, rodadas |

## Códigos de saída

| Código | Significado |
|--------|-------------|
| 0 | Sucesso (inclusive "aguardando o agente") |
| 2 | Dataset, intenção ou argumento inválido (`--n` fora de 3 a 5, ajuste vazio) |
| 9 | Mascaramento de PII indisponível |
| 10 | Falha de escrita |
| 11 | Contrato não aprovado ou desatualizado |
| 12 | Falha do provedor |
| 13 | Amostra não aprovável no estado atual |

## API

```python
from sintetica.sample import run, adjust, approve, show, load_sample_state

run(project_dir, "pedidos", n=3)
approve(project_dir, "pedidos")
state = load_sample_state(project_dir / "datasets" / "pedidos")
```
