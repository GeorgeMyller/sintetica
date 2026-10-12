# Onboarding: batch-generator

> Identificador: `006-batch-generator`
> Data: `2026-10-12`
> Para quem vai testar a feature pela primeira vez, depois do `/reversa-coding`.

## Pré-requisitos

1. Instale Python 3.10 ou superior e o `uv`.
2. Abra um terminal na raiz do projeto.
3. Instale as dependências com `uv sync`.
4. Siga o `onboarding.md` da feature 005 até o passo 7. O resultado esperado é o dataset `pedidos` com a amostra aprovada (`seeds/sample.jsonl`).

## Passo a passo

1. Rode as verificações. O resultado esperado é 0 erros e todos os testes passando.
   ```bash
   uv run mypy && uv run ruff check && uv run pytest --cov=sintetica.batch
   ```
2. Gere o lote de teste com o harness (volume 20 da intenção). O resultado esperado é o estado `aguardando_agente`, com 1 pedido de 20 registros e o comando `submit`.
   ```bash
   uv run sintetica generate pedidos
   ```
3. Faça o papel do agente. Gere 20 linhas JSONL, 1 delas com CPF, e envie com o `<id>` impresso.
   ```bash
   uv run sintetica submit pedidos <id> < respostas.jsonl
   uv run sintetica generate pedidos
   ```
   O resultado esperado é `output/dataset.json` com os registros válidos, ou um novo pedido só com os faltantes.
4. Confira o resultado. O resultado esperado é o status `concluido` e nenhum CPF original no dataset.
   ```bash
   uv run sintetica status pedidos
   grep -r "529.982.247-25" datasets/pedidos || echo "CPF original ausente"
   ```
5. Teste o background com o Ollama ligado. Mude o volume para 500 e gere de novo com `--new`. O resultado esperado é o controle de volta em até 5 s, com o PID. Se a intenção pedir nova confirmação, siga a mensagem do comando.
   ```bash
   uv run sintetica intent set pedidos --volume 500 && uv run sintetica intent confirm pedidos
   uv run sintetica generate pedidos --new
   uv run sintetica status pedidos
   ```
6. Encerre o processo e retome. O resultado esperado é o status "processo encerrado" e, depois do `--resume`, o lote concluído sem duplicados.
   ```bash
   kill <pid>
   uv run sintetica status pedidos
   uv run sintetica generate pedidos --resume
   ```
7. Teste a autorização com uma API externa e um teto baixo (`cost_ceiling_usd` em `.sintetica/policy.json`). O resultado esperado é o código 15, 0 pedidos e o comando com `--authorize-usd`.

## Limpeza

```bash
rm -rf datasets/pedidos
```
