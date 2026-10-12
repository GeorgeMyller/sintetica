# Data Delta: pii-guard

> Identificador: `001-pii-guard`
> Data: `2026-10-09`
> Base: `_reversa_sdd/sdd/pii-guard.md#9. Modelo de Dados`. Não há modelo extraído de legado (greenfield).

## 1. Tipos novos em memória

```
PiiType (str, Enum)
  CPF = "cpf" | CNPJ = "cnpj" | EMAIL = "email" | PHONE = "phone"
  CARD = "card" | IPV4 = "ipv4" | IPV6 = "ipv6" | CUSTOM = "custom"

PiiFinding (frozen dataclass)
  type: PiiType
  start: int                     // posição inicial no texto (inclusiva)
  end: int                       // posição final no texto (exclusiva)
  field: str | None              // nome do campo, quando o chamador informa
  preview: str                   // 2 primeiros caracteres + "***"
  // NÃO há atributo com o valor original (RN-04)

MaskResult (frozen dataclass)
  text: str                      // texto mascarado
  counts: dict<PiiType, int>     // achados substituídos por tipo
  fallbacks: int                 // substitutos que caíram para "***" (EC-04)

Coverage (frozen dataclass)
  types: tuple<PiiType, ...>     // os 7 tipos fixos
  custom_patterns: int           // quantidade de padrões extras ativos
  limits: tuple<str, ...>        // limites conhecidos (nomes, endereços livres, CNPJ alfanumérico, IPv4 x versões)

PolicyError (Exception)
  index: int                     // posição do padrão inválido em pii_custom_patterns
```

🟡 Diferença em relação à spec: `MaskResult` ganha `fallbacks`, para o chamador saber quantos substitutos falharam (EC-04). `PiiType` ganha o valor `custom`, já citado no RF-04 da spec.

## 2. Arquivo novo por dataset

**Caminho:** `datasets/<slug>/.pii_allowlist`

```
# 1 linha por valor falso inserido
<sha256 hex de 64 caracteres do valor normalizado>
```

- 🟡 Escrita por acréscimo, com `fsync` a cada chamada de `mask`.
- 🟡 Linhas duplicadas são permitidas no arquivo e removidas ao carregar no `set`.
- 🟡 Normalização antes do hash:

| Tipo | Normalização |
|------|--------------|
| cpf, cnpj, card, phone | só dígitos; telefone sem o prefixo 55 |
| email | minúsculas, sem espaços nas pontas |
| ipv4, ipv6 | `str(ipaddress.ip_address(valor))` (forma canônica) |
| custom | texto exato do achado |

## 3. Chave lida de arquivo existente

**Arquivo:** `.sintetica/policy.json` (criado pelo `cli-installer`, feature futura)

```
pii_custom_patterns: list<str>   // padrão: []; cada item ≤ 200 caracteres
```

- 🟡 Arquivo ausente: o módulo usa só os 7 detectores fixos.
- 🟡 Chave ausente: equivale a lista vazia.
- 🟡 JSON inválido ou padrão que não compila: `PolicyError`.

## 4. Migrações necessárias

Nenhuma. Projeto novo.
