# Onboarding: llm-provider

> Identificador: `002-llm-provider`
> Data: `2026-10-09`
> Público: pessoa que vai testar a feature pela primeira vez, depois do `/reversa-coding`.

## 1. Pré-requisitos

1. Instale o `uv` e o Python ≥ 3.10.
2. Na raiz do projeto, execute `uv sync`.
3. Confirme que a suíte da feature 001 continua verde: `uv run pytest tests/pii`.

## 2. Suíte automática (sem rede)

1. Execute `uv run pytest tests/providers tests/cli`.
2. Execute `uv run mypy` e `uv run ruff check`.
3. Execute `uv run pytest --cov=sintetica --cov-report=term-missing`.
4. Confirme cobertura ≥ 80% em `sintetica.providers` e `sintetica.cli`.

## 3. Protocolo do harness (sem chave de API)

1. Crie um dataset de teste: `mkdir -p datasets/demo`.
2. Grave um pedido de 5 registros:
   `uv run sintetica request demo --n-records 5 --instructions "clientes de uma loja" --schema schema.json`
3. Confira o id exibido e o arquivo `datasets/demo/requests/<id>.json`.
4. Envie 5 registros pela entrada padrão:
   `printf '{"nome":"A"}\n{"nome":"B"}\n{"nome":"C"}\n{"nome":"D"}\n{"nome":"E"}\n' | uv run sintetica submit demo <id>`
5. Confira o arquivo `datasets/demo/requests/<id>.response.jsonl`.
6. Repita o passo 2 com `--n-records 101`. O comando deve recusar com erro de limite do harness.
7. Repita o passo 4 com um id inexistente. O comando deve recusar sem gravar resposta.

## 4. Teste de fumaça com API real (opcional, gera custo)

> Execute só com autorização de gasto. Cada passo custa centavos.

1. Defina 1 chave, por exemplo `export OPENAI_API_KEY=...`.
2. Se quiser, defina o modelo: `export SINTETICA_OPENAI_MODEL=<modelo>`.
3. Execute `uv run pytest -m live -k openai`.
4. Confira no resultado: 3 registros, tokens de entrada e saída maiores que 0, custo maior que US$ 0.
5. Repita para `anthropic`, `gemini` e `ollama` (este último exige `ollama serve` e `ollama pull llama3.2`).

## 5. Mascaramento

1. Execute `uv run pytest tests/providers -k masking -v`.
2. Confirme que o e-mail das instruções não chega ao servidor simulado, inclusive no backend `ollama`.
3. Abra `datasets/<slug>/.pii_allowlist` gerado pelo teste. Ele contém só hashes, nunca o e-mail.

> Comportamento esperado: um dado pessoal real escrito nas instruções é trocado por um valor falso do mesmo tipo antes do envio. Isso vale também para valores que o usuário escreveu de propósito.

## 6. Custo e teto

1. Execute `uv run pytest tests/providers -k "cost or budget" -v`.
2. Confirme os 4 casos: US$ 5,00 não pede autorização; US$ 5,01 pede; modelo sem preço pede; o 3º pedido de US$ 0,40 com teto de US$ 1,00 não sai.
3. Para testar preço próprio, crie `.sintetica/pricing.json` com uma entrada e rode o cenário "Preço do projeto sobrescreve o preço embutido".

## 7. Problemas comuns

| Sintoma | Causa provável | Ação |
|---------|----------------|------|
| "Nenhum provedor disponível" com a lista de variáveis | Nenhuma chave definida e Ollama desligado | Defina 1 chave ou inicie o Ollama |
| Erro que cita `OPENAI_API_KEY` | Chave inválida (401 ou 403) | Troque a chave; o sistema não repete o pedido |
| Erro 404 de modelo | Identificador de modelo descontinuado | Defina `SINTETICA_<BACKEND>_MODEL` com um modelo vigente |
| `MaskingUnavailable` | `.sintetica/policy.json` com padrão de PII inválido | Corrija `pii_custom_patterns` |
