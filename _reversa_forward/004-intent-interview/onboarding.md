# Onboarding: intent-interview

> Identificador: `004-intent-interview`
> Data: `2026-10-12`
> Para quem vai testar a feature pela primeira vez, depois do `/reversa-coding`.

## Pré-requisitos

1. Instale Python 3.10 ou superior e o `uv`.
2. Abra um terminal na raiz do projeto.
3. Instale as dependências com `uv sync`.

## Passo a passo

1. Rode as verificações. O resultado esperado é 0 erros e todos os testes passando.
   ```bash
   uv run mypy && uv run ruff check && uv run pytest --cov=sintetica.intent
   ```
2. Inicie uma entrevista. O resultado esperado é a pasta `datasets/pedidos-de-cafe/seeds/` e o caminho absoluto na saída.
   ```bash
   uv run sintetica start "Pedidos de Café"
   ls datasets/pedidos-de-cafe
   ```
3. Veja as perguntas. O resultado esperado é 5 perguntas sem jargão, com exemplos.
   ```bash
   uv run sintetica intent questions
   ```
4. Responda com PII no objetivo. O resultado esperado é um aviso de e-mail mascarado, sem o valor original.
   ```bash
   uv run sintetica intent set pedidos-de-cafe --objective 'pedidos da loja, contato ana@empresa.com'
   grep -r "ana@empresa.com" datasets/pedidos-de-cafe || echo "valor original ausente"
   ```
5. Responda os outros itens, com "não sei" para regras. O resultado esperado é o resumo com regras `indefinido` e "Confirme a intenção".
   ```bash
   uv run sintetica intent set pedidos-de-cafe --structure 'cliente, bebida, valor' --unknown rules --format json --volume 50
   ```
6. Teste um volume inválido. O resultado esperado é o código 8 com o intervalo 1 a 10.000.
   ```bash
   uv run sintetica intent set pedidos-de-cafe --volume 50000; echo "código $?"
   ```
7. Confirme. O resultado esperado é "Próximo passo: uv run sintetica schema build pedidos-de-cafe".
   ```bash
   uv run sintetica intent confirm pedidos-de-cafe
   ```
8. Teste o Expresso crítico. O resultado esperado é o pedido de confirmação com o aviso de contrato genérico.
   ```bash
   uv run sintetica start rapido --mode expresso
   uv run sintetica intent set rapido --unknown objective --unknown structure --unknown rules --unknown format --unknown volume
   ```
9. Confira a integração com o `schema-builder`. O resultado esperado é o contrato padrão de 1 campo `descricao`.
   ```bash
   uv run sintetica intent confirm rapido
   uv run sintetica schema build rapido
   ```

## Limpeza

```bash
rm -rf datasets/pedidos-de-cafe datasets/rapido
```
