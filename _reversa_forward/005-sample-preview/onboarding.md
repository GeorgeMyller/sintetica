# Onboarding: sample-preview

> Identificador: `005-sample-preview`
> Data: `2026-10-12`
> Para quem vai testar a feature pela primeira vez, depois do `/reversa-coding`.

## Pré-requisitos

1. Instale Python 3.10 ou superior e o `uv`.
2. Abra um terminal na raiz do projeto.
3. Instale as dependências com `uv sync`.

## Passo a passo

1. Rode as verificações. O resultado esperado é 0 erros e todos os testes passando.
   ```bash
   uv run mypy && uv run ruff check && uv run pytest --cov=sintetica.sample
   ```
2. Prepare um dataset com intenção e contrato aprovados:
   ```bash
   uv run sintetica start pedidos --mode guiado
   uv run sintetica intent set pedidos --objective 'testar pedidos' --structure 'cliente e valor' --unknown rules --format json --volume 20
   uv run sintetica intent confirm pedidos
   cat > datasets/pedidos/schema.draft.json <<'EOF'
   {"format": "json", "fields": [
     {"name": "cliente", "type": "text"},
     {"name": "valor", "type": "decimal", "constraints": {"ge": 5, "le": 50, "casas_decimais": 2}}]}
   EOF
   uv run sintetica schema build pedidos && uv run sintetica schema approve pedidos
   ```
3. Peça a amostra. O resultado esperado é o caminho do pedido e o comando `submit`.
   ```bash
   uv run sintetica sample run pedidos
   ```
4. Faça o papel do agente com 1 registro inválido e 1 CPF. Use o `<id>` impresso no passo 3.
   ```bash
   printf '%s\n' '{"cliente": "Ana 529.982.247-25", "valor": "19.9"}' '{"cliente": "Bia", "valor": 99}' '{"cliente": "Caio", "valor": 7}' \
     | uv run sintetica submit pedidos <id>
   uv run sintetica sample run pedidos
   ```
   O resultado esperado é 2 aceitos, 1 descartado (valor acima de 50) e um novo pedido de 1 registro. O CPF não aparece na saída.
5. Responda o novo pedido com 1 registro válido e rode `sample run` de novo. O resultado esperado é a amostra com 3 registros e as 3 opções.
6. Peça um ajuste. O resultado esperado é um pedido novo que contém "nomes mais variados".
   ```bash
   uv run sintetica sample adjust pedidos 'nomes mais variados'
   ```
7. Depois de responder e revisar, aprove. O resultado esperado é `seeds/sample.jsonl` com 3 linhas e `seeds/sample.meta.json` com a versão do contrato.
   ```bash
   uv run sintetica sample approve pedidos
   cat datasets/pedidos/seeds/sample.meta.json
   grep -r "529.982.247-25" datasets/pedidos || echo "CPF original ausente"
   ```

## Limpeza

```bash
rm -rf datasets/pedidos
```
