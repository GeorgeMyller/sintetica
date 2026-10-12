# Onboarding: schema-builder

> Identificador: `003-schema-builder`
> Data: `2026-10-12`
> Para quem vai testar a feature pela primeira vez, depois do `/reversa-coding`.

## Pré-requisitos

1. Instale Python 3.10 ou superior e o `uv`.
2. Abra um terminal na raiz do projeto.
3. Instale as dependências com `uv sync`.

## Passo a passo

1. Rode as verificações. O resultado esperado é 0 erros e todos os testes passando, incluindo a suíte `codegen`.
   ```bash
   uv run mypy
   uv run ruff check
   uv run pytest --cov=sintetica.schema
   ```
2. Crie um dataset de teste com intenção e rascunho:
   ```bash
   mkdir -p datasets/demo/seeds
   cat > datasets/demo/intent.json <<'EOF'
   {"slug": "demo", "mode": "guiado", "format": "csv",
    "structure": {"status": "definido", "text": "clientes com endereço"}}
   EOF
   cat > datasets/demo/schema.draft.json <<'EOF'
   {"model_name": "Record", "format": "csv", "fields": [
     {"name": "Nome Completo", "type": "text", "constraints": {"min_length": 3}},
     {"name": "idade", "type": "int", "constraints": {"ge": 18, "le": 90}},
     {"name": "saldo", "type": "decimal", "constraints": {"casas_decimais": 2}},
     {"name": "tags", "type": "list", "items": {"name": "tag", "type": "text"}},
     {"name": "endereco", "type": "object", "fields": [
       {"name": "cidade", "type": "text"}, {"name": "uf", "type": "enum", "constraints": {"choices": ["SP", "RJ"]}}]}
   ]}
   EOF
   ```
3. Gere o contrato. O resultado esperado é o código 0, avisos de achatamento e de lista, e uma tabela com `nome_completo`, `idade`, `saldo`, `tags`, `endereco_cidade` e `endereco_uf`.
   ```bash
   uv run sintetica schema build demo
   ```
4. Confira os arquivos: `schema.json`, `schema.py`, `record.schema.json` e `schema.state.json` com `status: em_revisao`.
   ```bash
   ls datasets/demo
   head -3 datasets/demo/schema.py
   ```
5. Faça um ajuste. Mude `"le": 90` para `"le": 80` no rascunho e rode `build` de novo. O resultado esperado é `~ idade: le 90 → 80` e "Rodada de ajuste 1 de 5".
6. Teste um erro. Ponha `"ge": 95` no rascunho. O resultado esperado é o código 6 e uma mensagem com 95 e 80.
7. Aprove. O resultado esperado é `status: aprovado` em `schema.state.json`.
   ```bash
   uv run sintetica schema approve demo
   ```
8. Confira a integração com o protocolo do harness. O resultado esperado é o código 0.
   ```bash
   uv run sintetica request demo --n-records 3 --instructions "teste" --schema datasets/demo/record.schema.json
   ```

## Limpeza

```bash
rm -rf datasets/demo
```
