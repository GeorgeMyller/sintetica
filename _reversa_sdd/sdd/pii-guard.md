# Spec: pii-guard

> Selo 🟢 CONFORME CÓDIGO em todos os itens, salvo marcação. Fonte: `src/sintetica/pii/`, testes `tests/pii/` (92 testes, 280 casos de referência).
> Consolida o adendo `addenda/001-pii-guard.md`. Versão planejada original em `sdd/_planejado/pii-guard.md`.

**Versão:** 2.0 (extraída do código)
**Status:** Implementado
**Autor:** reversa-writer
**Data:** 2026-10-12

---

## 1. Resumo

🟢 O `pii-guard` é o módulo `sintetica.pii`. Ele detecta dados pessoais em texto (CPF, CNPJ, e-mail, telefone, cartão, IPv4, IPv6 e padrões extras da política) e os troca por valores falsos do mesmo tipo e formato, 100% local. A fachada `PiiGuard` (`scan`, `mask`, `leaks`, `coverage`, `for_dataset`) é usada pela entrevista, pela amostra, pelo provedor (pré-mascaramento), pelo lote e pela avaliação.

## 2. Contexto

🟢 O usuário pode digitar dados reais, e os modelos podem gerar dados reais. A métrica do PRD é "0 vazamentos detectados" pelos detectores do sintetica (Q9). Os valores falsos inseridos de propósito não podem contar como vazamento (Q23, Q26).

## 3. Goals

- 🟢 G-01: Detectar os 7 tipos fixos com validação de dígitos, sem rede.
- 🟢 G-02: Trocar cada achado por um valor falso do mesmo formato e registrar o hash do falso.
- 🟢 G-03: Distinguir vazamento de valor falso pela allowlist.
- 🟢 G-04: Nunca expor o valor completo de um achado (prévia de 2 caracteres + `***`).

## 4. Non-Goals

- 🟢 NG-01: Nomes de pessoas e endereços em texto livre não são detectados.
- 🟢 NG-02: CNPJ alfanumérico não é detectado.
- 🟢 NG-03: Não há modelo de linguagem nem chamada de rede na detecção.

## 5. Usuários

🟢 Consumidores internos: `intent` (respostas), `sample` e `batch` (registros aceitos), `providers` (`MaskingProvider`), `quality` (`leaks`, `coverage`).

## 6. Requisitos Funcionais

| ID | Requisito | Critério de aceite | Fonte |
|----|-----------|--------------------|-------|
| RF-01 | 🟢 Detectar CPF e CNPJ com pontuação opcional, validando os dígitos (módulo 11) e rejeitando dígitos todos iguais | `529.982.247-25` e `52998224725` detectados; `111.111.111-11` não | `detectors.py:42-43`, `checksums.py:36-49` |
| RF-02 | 🟢 Detectar cartão de 13 a 19 dígitos (espaço ou hífen opcional) válido por Luhn | Número que falha no Luhn não é detectado | `detectors.py:46`, `67-69` |
| RF-03 | 🟢 Detectar telefone só com formatação (`(11) 9…`, `11 9…`, `11-9…`) ou prefixo `+55`, com 10 ou 11 dígitos e DDD ≥ 11; dígitos corridos não contam (Q25) | `11987654321` sozinho não é detectado | `detectors.py:52-76` |
| RF-04 | 🟢 Detectar e-mail, IPv4 e IPv6 (validados pelo `ipaddress`) | `1.2.3.4` detectado; `999.1.1.1` não | `detectors.py:48-94` |
| RF-05 | 🟢 Aceitar padrões extras de `pii_custom_patterns` em `.sintetica/policy.json`: lista de regex não vazias, até 200 caracteres, compiláveis; arquivo ausente = sem padrões | Padrão inválido gera `PolicyError(index)` | `policy.py:14-36` |
| RF-06 | 🟢 `scan(texto, campo)` devolve os achados sem sobreposição: maior trecho vence; empate por `CARD > CNPJ > CPF > PHONE > IPV6 > IPV4 > EMAIL > CUSTOM`; `field` preenchido quando informado | CPF dentro de um cartão não gera 2 achados | `guard.py:20-53`, `89-96` |
| RF-07 | 🟢 Textos acima de 1 MiB são lidos em janelas de 64 KiB com 64 caracteres de sobreposição; cada achado conta só na janela onde começa | Mesmo resultado que a leitura inteira para achados de até 64 caracteres | `guard.py:98-110` |
| RF-08 | 🟢 `mask(texto, campo)` troca cada achado do fim para o começo; pula o que já está na allowlist (idempotente); gera até 5 substitutos e aceita o 1º diferente do original e detectável de ponta a ponta; sem substituto, usa `*` do mesmo tamanho e conta 1 `fallback` | `MaskResult(texto, contagem por tipo, fallbacks)` | `guard.py:112-144` |
| RF-09 | 🟢 Substitutos com formato espelhado (Faker `pt_BR`): só os dígitos mudam e a pontuação fica; telefone mantém `+55` e o tipo (celular 9 + 8 dígitos, ou fixo); cartão começa com 4 e fecha pelo Luhn; padrão extra troca dígitos (ou letras, mantendo a caixa) | `529.982.247-25` vira outro CPF válido com a mesma máscara | `substitutes.py` |
| RF-10 | 🟢 Cada substituto aceito grava o SHA-256 do valor normalizado em `datasets/<slug>/.pii_allowlist` (1 por linha, `fsync`) | Normalização: dígitos (CPF, CNPJ, cartão, telefone sem `55`), e-mail minúsculo, IP canônico | `allowlist.py`, `normalize.py` |
| RF-11 | 🟢 `leaks(texto, campo)` devolve só os achados fora da allowlist | Valor falso registrado não é vazamento | `guard.py:146-151` |
| RF-12 | 🟢 `coverage()` devolve os 7 tipos, o número de padrões extras e 6 limites conhecidos | Usado na seção de escopo do relatório | `guard.py:37-44`, `153-154` |
| RF-13 | 🟢 Semente opcional para substitutos reprodutíveis em teste | `PiiGuard(..., seed=n)` | `guard.py:61`, `substitutes.py:20-23` |

## 7. Requisitos Não-Funcionais

| ID | Requisito | Evidência |
|----|-----------|-----------|
| RNF-01 | 🟢 0 chamadas de rede | Só `re`, `ipaddress`, `hashlib`, Faker |
| RNF-02 | 🟢 Nenhum tipo guarda o valor original de um achado | `domain.py:1`, `PiiFinding.preview` |
| RNF-03 | 🟢 Precisão no conjunto de referência: 280 casos (20 positivos e 20 negativos por tipo) | `tests/fixtures/pii_reference/`, Q24 |
| RNF-04 | 🟢 Allowlist durável (`flush` + `fsync` por hash) | `allowlist.py:37-46` |

## 8. Interface

```python
from sintetica.pii import PiiGuard, PiiType, PolicyError

guard = PiiGuard.for_dataset(Path("datasets/pedidos"), Path(".sintetica/policy.json"))
guard.scan("CPF 529.982.247-25", field="cliente")   # [PiiFinding(CPF, 4, 18, "cliente", "52***")]
guard.mask("CPF 529.982.247-25").text               # "CPF 123.456.789-09" (falso, válido)
guard.leaks(texto, field="cliente")                 # achados fora da allowlist
guard.coverage()                                    # Coverage(types, custom_patterns, limits)
guard.allowlist_available                           # False sem o arquivo .pii_allowlist
```

## 9. Modelo de Dados

🟢 `PiiType` (8 valores), `PiiFinding(type, start, end, field, preview)`, `MaskResult(text, counts, fallbacks)`, `Coverage(types, custom_patterns, limits)`, `PolicyError(index)`. Arquivo `.pii_allowlist`: 1 SHA-256 por linha. Detalhe em `data-dictionary.md#módulo-pii`.

## 10. Integrações e Dependências

| Dependência | Uso | Falha |
|-------------|-----|-------|
| 🟢 Faker `pt_BR` | Substitutos | Exceção do Faker conta como tentativa e vai ao log |
| 🟢 `.sintetica/policy.json` | Padrões extras | `PolicyError`: consumidores bloqueiam a gravação (código 9) |

## 11. Edge Cases

| Cenário | Comportamento |
|---------|---------------|
| 🟢 Valor já falso no texto | Não é trocado de novo (allowlist) |
| 🟢 5 substitutos inválidos | `***` do mesmo tamanho; `fallbacks + 1` |
| 🟢 Allowlist ausente | `allowlist_available = False`; em `leaks`, todo achado conta |
| 🟢 Padrão extra que casa vazio | Ignorado |
| 🟢 Número de versão `a.b.c.d` | Pode virar IPv4 (falso positivo aceito, limite documentado) |
| 🟢 CPF falso coincidir com um real | Possível (limite documentado) |

## 12. Segurança e Privacidade

- 🟢 Prévia com 2 caracteres + `***`; nenhum log ou exceção cita o valor.
- 🟢 A allowlist guarda só hashes de valores falsos.

## 13. Decisões (consolidadas)

| Decisão | Fonte |
|---------|-------|
| 🟢 Allowlist por hash do valor normalizado | Q23, Q26, ADR 005 |
| 🟢 Telefone só formatado | Q25 |
| 🟢 Conjunto de referência de 280 casos | Q24 |
| 🟢 Mascarar também antes do Ollama | Q30, ADR 004 |

## 14. Lacunas

- 🔴 Detecção de nomes e endereços fora do escopo; a métrica de vazamento cobre só os 7 tipos e os padrões extras.

## Histórico

| Versão | Data | Mudança |
|--------|------|---------|
| 1.0 | 2026-10-09 | Spec planejada (`_planejado/`) |
| 2.0 | 2026-10-12 | Reescrita conforme o código; adendo 001 consolidado |
