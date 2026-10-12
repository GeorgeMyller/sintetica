# Regression Watch: schema-builder

> Identificador: `003-schema-builder`
> Data: `2026-10-12`
> Feature greenfield. Não há regras 🟢 para vigiar. O watch principal fica vazio. Os requisitos implementados ficam em "Observações", sem peso de regressão, até uma extração `/reversa` futura confirmá-los como 🟢.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|-------------------------|-----------------------------|---------------------|-------------------|

## Observações

| ID | Origem (arquivo, seção) | Regra esperada | Tipo de verificação | Sinal de violação |
|----|-------------------------|----------------|---------------------|-------------------|
| W001 | `_reversa_forward/003-schema-builder/requirements.md#4` RN-01, RN-02 | O runtime nunca executa código escrito pelo modelo; todo texto da definição entra no `schema.py` como literal escapado | ausência | `exec`/`eval` de texto da definição, ou f-string que interpola texto da definição em código |
| W002 | `requirements.md#5` RF-05 | Mesma definição gera o mesmo `schema.py`, byte a byte | presença | `test_generation_is_deterministic` falha |
| W003 | `requirements.md#4` RN-05 | Versão = SHA-256 do JSON canônico; formatação e ordem de chaves não mudam a versão | presença | Versão muda após reformatar `schema.json` |
| W004 | `requirements.md#4` RN-08 (Q36), D-13 | `schema.py` só é importado com versão do cabeçalho igual à de `schema.json` | presença | `load_record_model` importa um `schema.py` com versão divergente |
| W005 | `requirements.md#4` RN-04 (Q35) | CSV: objetos achatados com prefixo; listas simples em 1 coluna com `|`; lista de objetos recusada | presença | Lista de objetos aceita em CSV, ou item de texto com `|` aceito |
| W006 | `requirements.md#4` RN-09 (Q37) | Decimal: número exato no JSON/JSONL, texto com casas fixas no CSV | presença | `to_jsonl_line` emite decimal como texto ou `float` arredondado |
| W007 | `requirements.md#4` RN-03 | Nomes snake_case ASCII; reservados com `_`; repetidos com `_2` | presença | `schema.py` com nome de campo inválido ou que sombreia `datetime`, `int` etc. |
| W008 | `requirements.md#4` RN-06 | Até 100 campos contando aninhados; sugestão de `/sintetica-start` na 5ª rodada | presença | 101 campos aceitos |
| W009 | `requirements.md#5` RF-20 | O código gerado de cada definição de teste passa em `mypy --strict`, `ruff check` e `ruff format --check` | presença | `pytest -m codegen` falha |
| W010 | `interfaces/schema-cli.md#4` | Códigos de saída 6 e 7 exclusivos do `schema`; 3, 4 e 5 continuam do harness | redação | Colisão de códigos entre subcomandos |

## Histórico de re-extrações

### Re-extração 2026-10-12 12:00

> Watch principal vazio (feature greenfield). Itens de "Observações" verificados de forma informativa, sem peso de regressão.

| ID | Veredito | Observação |
|----|----------|------------|
| W001 | 🟢 verde | regra presente em `_reversa_sdd/sdd/schema-builder.md` e `_reversa_sdd/domain.md` |
| W002 | 🟢 verde | regra presente em `_reversa_sdd/sdd/schema-builder.md` e `_reversa_sdd/domain.md` |
| W003 | 🟢 verde | regra presente em `_reversa_sdd/sdd/schema-builder.md` e `_reversa_sdd/domain.md` |
| W004 | 🟢 verde | regra presente em `_reversa_sdd/sdd/schema-builder.md` e `_reversa_sdd/domain.md` |
| W005 | 🟢 verde | regra presente em `_reversa_sdd/sdd/schema-builder.md` e `_reversa_sdd/domain.md` |
| W006 | 🟢 verde | regra presente em `_reversa_sdd/sdd/schema-builder.md` e `_reversa_sdd/domain.md` |
| W007 | 🟢 verde | regra presente em `_reversa_sdd/sdd/schema-builder.md` e `_reversa_sdd/domain.md` |
| W008 | 🟢 verde | regra presente em `_reversa_sdd/sdd/schema-builder.md` e `_reversa_sdd/domain.md` |
| W009 | 🟢 verde | regra presente em `_reversa_sdd/sdd/schema-builder.md` e `_reversa_sdd/domain.md` |
| W010 | 🟢 verde | regra presente em `_reversa_sdd/sdd/schema-builder.md` e `_reversa_sdd/domain.md` |

| Data | Resultado | Observação |
|------|-----------|------------|

## Arquivadas

| ID | Motivo | Data |
|----|--------|------|
