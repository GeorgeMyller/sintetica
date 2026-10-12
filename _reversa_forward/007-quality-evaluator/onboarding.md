# Onboarding: quality-evaluator

> Identificador: `007-quality-evaluator`
> Data: `2026-10-12`
> Para quem vai testar a feature pela primeira vez, depois do `/reversa-coding`.

## Pré-requisitos

1. Instale Python 3.10 ou superior e o `uv`.
2. Abra um terminal na raiz do projeto.
3. Instale as dependências com `uv sync`.
4. Siga o `onboarding.md` da feature 006 até o passo 4. O resultado esperado é o dataset `pedidos` com o lote concluído.

## Passo a passo

1. Rode as verificações. O resultado esperado é 0 erros e todos os testes passando.
   ```bash
   uv run mypy && uv run ruff check && uv run pytest --cov=sintetica.quality
   ```
2. Confira a avaliação automática. O resultado esperado é a saída do `generate` com o veredito e os arquivos `report.md` e `report.json`.
   ```bash
   ls datasets/pedidos/report.*
   uv run sintetica status pedidos
   ```
3. Rode a avaliação avulsa. O resultado esperado é o mesmo veredito, com código 0 (`APROVADO`) ou 17 (`REPROVADO`).
   ```bash
   uv run sintetica eval pedidos; echo "código $?"
   ```
4. Insira um e-mail real numa cópia do dataset e avalie de novo. O resultado esperado é 1 vazamento, código 17 e só a prévia do e-mail no relatório.
   ```bash
   cp datasets/pedidos/output/dataset.json /tmp/dataset.json.bak
   sed -i.tmp 's/"Cliente 1"/"Cliente 1 ana.souza@empresa.com.br"/' datasets/pedidos/output/dataset.json
   uv run sintetica eval pedidos; echo "código $?"
   grep -c "ana.souza@empresa.com.br" datasets/pedidos/report.md || echo "e-mail completo ausente"
   cp /tmp/dataset.json.bak datasets/pedidos/output/dataset.json
   ```
5. Apague o dataset final e avalie. O resultado esperado é o código 18 com o comando `sintetica generate`.

## Limpeza

```bash
rm -rf datasets/pedidos
```
