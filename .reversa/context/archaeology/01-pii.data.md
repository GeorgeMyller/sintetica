## Módulo `pii`

### `PiiType` (enum, `domain.py:10`)

| Valor | Observação |
|-------|------------|
| `cpf`, `cnpj`, `email`, `phone`, `card`, `ipv4`, `ipv6` | `FIXED_TYPES`, os 7 tipos fixos (Q9) |
| `custom` | Padrões extras de `pii_custom_patterns` |

### `PiiFinding` (dataclass imutável, `domain.py:35`)

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `type` | `PiiType` | sim | Tipo detectado |
| `start` | `int` | sim | Índice inicial, inclusivo |
| `end` | `int` | sim | Índice final, exclusivo |
| `field` | `str \| None` | sim | Caminho do campo (ex.: `end.cidade`, `tags[]`) |
| `preview` | `str` | sim | 2 primeiros caracteres + `***`; nunca o valor completo |

### `MaskResult` (`domain.py:46`)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `text` | `str` | Texto mascarado |
| `counts` | `Mapping[PiiType, int]` | Achados trocados por tipo |
| `fallbacks` | `int` | Trocas por `***` (substituto indisponível) |

### `Coverage` (`domain.py:55`)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `types` | `tuple[PiiType, ...]` | Os 7 tipos fixos |
| `custom_patterns` | `int` | Número de padrões extras |
| `limits` | `tuple[str, ...]` | 6 limites conhecidos |

### `PolicyError` (exceção, `domain.py:63`)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `index` | `int` | Padrão com problema, ou -1 para o arquivo |

### Arquivo `datasets/<slug>/.pii_allowlist`

🟢 Texto UTF-8, 1 SHA-256 hexadecimal por linha, do valor falso normalizado por tipo. Só cresce (anexo com `fsync`).

### Chave `pii_custom_patterns` de `.sintetica/policy.json`

🟢 Lista de regex não vazias, até 200 caracteres cada, compiláveis pelo `re`. Ausente vale `[]`.
