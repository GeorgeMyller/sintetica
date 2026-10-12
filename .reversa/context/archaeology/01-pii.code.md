## Módulo `pii` (`src/sintetica/pii/`)

🟢 **Propósito:** detectar dados pessoais (PII) em texto e trocá-los por valores falsos do mesmo tipo e formato, 100% local. A fachada `PiiGuard` é consumida por `intent`, `sample`, `providers` (decorador de mascaramento), `batch` e `quality`.

### Arquivos

| Arquivo | Papel |
|---------|-------|
| `domain.py` | `PiiType`, `FIXED_TYPES`, `PiiFinding`, `MaskResult`, `Coverage`, `PolicyError`, `make_preview` |
| `ports.py` | Protocolos `Detector`, `SubstituteGenerator`, `AllowlistStore` |
| `detectors.py` | 7 detectores por regex com validação, mais `CustomDetector` |
| `checksums.py` | Dígitos verificadores de CPF e CNPJ (módulo 11) e Luhn |
| `normalize.py` | Normalização por tipo antes do hash da allowlist |
| `substitutes.py` | `FakerSubstituteGenerator` (Faker `pt_BR`), formato espelhado |
| `allowlist.py` | `FileAllowlistStore`: arquivo `.pii_allowlist`, 1 SHA-256 por linha |
| `policy.py` | `load_custom_patterns` de `.sintetica/policy.json` |
| `guard.py` | `PiiGuard`: `scan`, `mask`, `leaks`, `coverage`, `for_dataset` |

### Funções e métodos principais

| Função | Assinatura | Retorno | Local |
|--------|-----------|---------|-------|
| `PiiGuard.for_dataset` | `(dataset_dir, policy_path, seed=None)` | `PiiGuard` | `guard.py:74` |
| `PiiGuard.scan` | `(text, field=None)` | `list[PiiFinding]` | `guard.py:89` |
| `PiiGuard.mask` | `(text, field=None)` | `MaskResult` | `guard.py:127` |
| `PiiGuard.leaks` | `(text, field=None)` | `list[PiiFinding]` fora da allowlist | `guard.py:146` |
| `PiiGuard.coverage` | `()` | `Coverage` | `guard.py:153` |
| `load_custom_patterns` | `(path)` | `tuple[str, ...]` | `policy.py:14` |
| `cpf_is_valid`, `cnpj_is_valid`, `luhn_is_valid` | `(value)` | `bool` | `checksums.py:36,44,65` |
| `fingerprint` | `(pii_type, value)` | SHA-256 hex do valor normalizado | `allowlist.py:15` |

### Algoritmos

1. 🟢 **Detecção por regex com fronteiras** (`detectors.py:42-64`): cada regex usa lookbehind/lookahead para não casar dentro de sequências maiores de dígitos (`(?<!\d)(?<!\d[./-])…(?!\d)(?![./-]\d)`).
2. 🟢 **Validação pós-regex:** CPF e CNPJ por módulo 11 com pesos fixos (`checksums.py:10-49`), rejeitando dígitos todos iguais; cartão por Luhn com 13 a 19 dígitos (`detectors.py:67`); telefone com 10 ou 11 dígitos e DDD ≥ 11, descontando o `55` do prefixo `+55` (`detectors.py:72`); IPv4 e IPv6 pelo `ipaddress` (`detectors.py:79-94`).
3. 🟢 **Telefone só formatado** (`detectors.py:52-61`): exige DDD entre parênteses, DDD seguido de espaço ou hífen, ou prefixo `+55`. Dígitos corridos não contam (Q25).
4. 🟢 **Resolução de sobreposição** (`guard.py:47-53`): ordena os achados por tamanho decrescente, depois pela prioridade `CARD < CNPJ < CPF < PHONE < IPV6 < IPV4 < EMAIL < CUSTOM`, depois pelo início; aceita cada achado que não cruza um já aceito.
5. 🟢 **Varredura em blocos** (`guard.py:98-110`): textos acima de 1 MiB são lidos em janelas de 64 KiB com 64 caracteres de sobreposição; um achado só conta na janela onde começa.
6. 🟢 **Mascaramento** (`guard.py:127-144`): percorre os achados do fim para o começo (os índices continuam válidos); pula valores já na allowlist (idempotência); gera substituto até 5 vezes, exigindo que seja diferente do original e detectável pelo mesmo detector de ponta a ponta; registra o hash do substituto na allowlist; se as 5 tentativas falharem, troca por `*` do mesmo tamanho e conta 1 `fallback`.
7. 🟢 **Substitutos com formato espelhado** (`substitutes.py:13-81`): `_lay_digits` troca só os dígitos do original e mantém a pontuação; telefone mantém `+55` e gera celular (9 + 8 dígitos) ou fixo (2 a 5 + dígitos); cartão começa com 4 e fecha com o dígito de Luhn; padrão extra com dígitos troca só os dígitos (mantém prefixos como `MAT-`), sem dígitos troca letras mantendo a caixa.
8. 🟢 **Normalização para o hash** (`normalize.py:11-23`): CPF, CNPJ e cartão só dígitos; telefone só dígitos sem `55` inicial (12 ou 13 dígitos); e-mail em minúsculas sem espaços; IP na forma canônica do `ipaddress`.

### Tratamento de erros

- 🟢 `PolicyError(index, msg)`: política ausente vale como sem padrões; JSON inválido, não objeto, lista inválida, padrão vazio, acima de 200 caracteres ou regex inválida geram erro (`policy.py:14-36`).
- 🟢 Falha do Faker ao gerar substituto é registrada em log e conta como tentativa (`guard.py:120-122`).
- 🟢 A gravação da allowlist faz `flush` e `fsync` a cada hash novo (`allowlist.py:37-46`).

### Constantes de domínio

| Constante | Valor | Local |
|-----------|-------|-------|
| `CHUNK_THRESHOLD` | 1 MiB | `guard.py:32` |
| `CHUNK_SIZE`, `CHUNK_OVERLAP` | 64 KiB, 64 | `guard.py:33-34` |
| `MAX_SUBSTITUTE_ATTEMPTS` | 5 | `guard.py:35` |
| `KNOWN_LIMITS` | 6 limites textuais | `guard.py:37-44` |
| `MAX_PATTERN_LENGTH` | 200 | `policy.py:11` |
| `ALLOWLIST_FILENAME` | `.pii_allowlist` | `allowlist.py:12` |
| Prévia | 2 primeiros caracteres + `***` | `domain.py:71-73` |

### Dependências

🟢 Faker (`pt_BR`). Nenhum outro módulo do `sintetica`.
