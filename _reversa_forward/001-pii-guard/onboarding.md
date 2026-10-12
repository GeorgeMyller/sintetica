# Onboarding: pii-guard

> Identificador: `001-pii-guard`
> Data: `2026-10-09`
> Para quem vai testar a feature pela primeira vez, depois do `/reversa-coding`.

## Pré-requisitos

1. Instale Python 3.10 ou superior. Confira com `python3 --version`.
2. Instale o `uv`. Confira com `uv --version`.
3. Abra um terminal na raiz do projeto `data_sintetic_generation`.

## Passo a passo

1. Instale as dependências:
   ```bash
   uv sync
   ```
2. Rode a verificação de tipos. O resultado esperado é `Success: no issues found`.
   ```bash
   uv run mypy --strict src
   ```
3. Rode o lint. O resultado esperado é `All checks passed!`.
   ```bash
   uv run ruff check
   ```
4. Rode os testes com cobertura. O resultado esperado é cobertura ≥ 80% no total e 100% em `checksums.py` e `detectors.py`.
   ```bash
   uv run pytest tests/pii --cov=sintetica.pii --cov-report=term-missing
   ```
5. Teste o mascaramento à mão:
   ```bash
   uv run python -c "
   from pathlib import Path
   from sintetica.pii import PiiGuard
   g = PiiGuard.for_dataset(Path('/tmp/ds-teste'), Path('.sintetica/policy.json'), seed=42)
   r = g.mask('CPF 529.982.247-25, e-mail ana@exemplo.com, tel (11) 91234-5678')
   print(r.text); print(r.counts)
   print('vazamentos:', g.leaks(r.text))
   "
   ```
   Resultado esperado:
   - O texto mostra outro CPF, outro e-mail e outro telefone, no mesmo formato.
   - `counts` mostra 1 achado para cada um dos 3 tipos: cpf, email e phone.
   - `vazamentos: []`.
6. Confira que o valor original não ficou no disco. O resultado esperado é nenhuma linha.
   ```bash
   grep -r "529.982.247-25" /tmp/ds-teste
   ```
7. Confira a regra de telefone. O resultado esperado é `[]`.
   ```bash
   uv run python -c "
   from pathlib import Path
   from sintetica.pii import PiiGuard
   print(PiiGuard.for_dataset(Path('/tmp/ds-teste'), Path('nao-existe.json')).scan('Chave 11912345678'))
   "
   ```
8. Rode o teste de desempenho. É opcional e fica fora da suíte padrão. O resultado esperado é ≤ 30 s.
   ```bash
   uv run pytest -m perf tests/pii
   ```

## Limpeza

```bash
rm -rf /tmp/ds-teste
```
