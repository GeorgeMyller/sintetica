# pii-guard

Detecção e mascaramento local de PII (dados pessoais identificáveis) do sintetica. Tudo roda na máquina: nenhuma chamada de rede.

## Uso

```python
from pathlib import Path
from sintetica.pii import PiiGuard

guard = PiiGuard.for_dataset(Path("datasets/pedidos"), Path(".sintetica/policy.json"), seed=42)

guard.scan("CPF 529.982.247-25")        # lista de achados: tipo, início, fim, campo, prévia
guard.mask("CPF 529.982.247-25").text   # "CPF 104.965.823-05" com seed=42 (valor falso, mesmo formato)
guard.leaks(texto)                      # achados que NÃO são valores falsos inseridos pelo mask
guard.coverage()                        # tipos cobertos, padrões extras e limites conhecidos
```

- `mask` troca cada achado por um valor falso do mesmo tipo e formato e grava o hash SHA-256 do valor falso em `datasets/<slug>/.pii_allowlist`.
- `leaks` ignora os achados cujo hash está na allowlist. Um CPF falso pedido no schema não conta como vazamento.
- Sem `.pii_allowlist`, todo achado conta como vazamento. `guard.allowlist_available` informa esse caso.
- Se o substituto falhar 5 vezes, o valor vira `***` do mesmo tamanho e `MaskResult.fallbacks` aumenta.
- O valor original nunca é gravado. A prévia mostra só os 2 primeiros caracteres seguidos de `***`.

## Tipos cobertos

| Tipo | Regra |
|------|-------|
| `cpf` | 11 dígitos, com ou sem pontuação, dígitos verificadores válidos |
| `cnpj` | 14 dígitos numéricos, com ou sem pontuação, dígitos verificadores válidos |
| `email` | `parte-local@domínio.tld` |
| `phone` | DDD de 11 a 99 e 8 ou 9 dígitos, **apenas** com formatação (`(11) 91234-5678`, `11 91234-5678`) ou prefixo `+55` |
| `card` | 13 a 19 dígitos, espaço ou hífen opcional, válido por Luhn |
| `ipv4`, `ipv6` | Confirmados pelo módulo `ipaddress` |
| `custom` | Padrões de `pii_custom_patterns` |

## Padrões extras

Em `.sintetica/policy.json`:

```json
{ "pii_custom_patterns": ["MAT-\\d{6}"] }
```

- Cada padrão é uma expressão regular Python com no máximo 200 caracteres.
- Padrão inválido gera `PolicyError` com o índice do padrão; nenhum texto é processado.
- Evite padrões com quantificadores aninhados, como `(a+)+`. Eles podem travar o processo por retrocesso catastrófico.

## Limites conhecidos

- Nomes de pessoas e endereços em texto livre não são detectados.
- CNPJ alfanumérico não é detectado.
- Telefone com dígitos corridos, sem `+55`, não é detectado.
- Números de versão no formato `a.b.c.d` podem ser detectados como IPv4.
- Um CPF ou CNPJ falso válido pode coincidir com o documento real de outra pessoa.

## Testes

```bash
uv run pytest --cov=sintetica.pii   # suíte padrão
uv run pytest -m perf               # desempenho: 10.000 registros de 1 KB em ≤ 30 s
```

O conjunto de referência fica em `tests/fixtures/pii_reference/`, com 20 casos positivos e 20 negativos por tipo.
