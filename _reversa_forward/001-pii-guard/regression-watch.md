# Regression Watch: pii-guard

> Identificador: `001-pii-guard`
> Data: `2026-10-09`
> Feature greenfield. Não há regras 🟢 para vigiar: nada foi extraído de código existente. O watch principal fica vazio. Os requisitos implementados ficam em "Observações", sem peso de regressão, até uma extração `/reversa` futura confirmá-los como 🟢.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|-------------------------|-----------------------------|---------------------|-------------------|

## Observações

| ID | Origem (arquivo, seção) | Regra esperada | Tipo de verificação | Sinal de violação |
|----|-------------------------|----------------|---------------------|-------------------|
| W001 | `_reversa_sdd/sdd/pii-guard.md#6` RF-01, RF-02 | CPF e CNPJ só são detectados com dígitos verificadores válidos; dígitos repetidos são rejeitados | presença | `cpf_is_valid` ou `cnpj_is_valid` sem cálculo de módulo 11 |
| W002 | `_reversa_sdd/sdd/pii-guard.md#6` RF-03 | Cartão só é detectado com 13 a 19 dígitos e Luhn válido | presença | Detector de cartão sem `luhn_is_valid` |
| W003 | `_reversa_forward/001-pii-guard/requirements.md#4` RN-06 (Q25) | Telefone só é detectado com formatação ou prefixo `+55` | presença | `scan("Chave 11912345678")` retorna achado |
| W004 | `_reversa_sdd/sdd/pii-guard.md#6` RF-07, RF-08 (Q23) | Vazamento é só o achado cujo hash do valor normalizado não está em `.pii_allowlist` | presença | `leaks` de um texto mascarado retorna achados |
| W005 | `_reversa_sdd/sdd/pii-guard.md#6` RF-10 | O valor original de um achado nunca é gravado; a prévia mostra 2 caracteres + `***` | ausência | Valor original em `.pii_allowlist`, logs ou relatórios |
| W006 | `_reversa_forward/001-pii-guard/requirements.md#4` RN-01 | Detecção e mascaramento sem chamadas de rede | ausência | Importação de cliente HTTP em `sintetica.pii` |
| W007 | `_reversa_forward/001-pii-guard/requirements.md#4` RN-07 | Falha no módulo bloqueia gravação e envio (exceção propaga; política inválida gera `PolicyError`) | presença | `PiiGuard` captura exceção de política ou de escrita e segue |
| W008 | `_reversa_sdd/sdd/pii-guard.md#6` RF-11 (Q9) | `coverage()` lista os 7 tipos, os padrões extras e os limites conhecidos | presença | Relatório do `quality-evaluator` sem escopo e limites |
| W009 | `_reversa_forward/001-pii-guard/requirements.md#6` RNF de precisão (Q24) | 100% dos positivos e ≤ 5% de falsos positivos nos 280 casos de referência | presença | `tests/pii/test_reference_set.py` falha |
| W010 | `_reversa_forward/001-pii-guard/data-delta.md#2` | Hash da allowlist sobre o valor normalizado por tipo | redação | Mudança em `normalize.py` sem migração das allowlists existentes |

## Histórico de re-extrações

### Re-extração 2026-10-12 12:00

> Watch principal vazio (feature greenfield). Itens de "Observações" verificados de forma informativa, sem peso de regressão.

| ID | Veredito | Observação |
|----|----------|------------|
| W001 | 🟢 verde | regra presente em `_reversa_sdd/sdd/pii-guard.md` e `_reversa_sdd/domain.md` |
| W002 | 🟢 verde | regra presente em `_reversa_sdd/sdd/pii-guard.md` e `_reversa_sdd/domain.md` |
| W003 | 🟢 verde | regra presente em `_reversa_sdd/sdd/pii-guard.md` e `_reversa_sdd/domain.md` |
| W004 | 🟢 verde | regra presente em `_reversa_sdd/sdd/pii-guard.md` e `_reversa_sdd/domain.md` |
| W005 | 🟢 verde | regra presente em `_reversa_sdd/sdd/pii-guard.md` e `_reversa_sdd/domain.md` |
| W006 | 🟢 verde | regra presente em `_reversa_sdd/sdd/pii-guard.md` e `_reversa_sdd/domain.md` |
| W007 | 🟢 verde | regra presente em `_reversa_sdd/sdd/pii-guard.md` e `_reversa_sdd/domain.md` |
| W008 | 🟢 verde | regra presente em `_reversa_sdd/sdd/pii-guard.md` e `_reversa_sdd/domain.md` |
| W009 | 🟡 amarelo | Regra presente como RNF-03 de `sdd/pii-guard.md` (280 casos), sem o limiar explícito de 100% e ≤ 5%; os testes continuam aplicando o limiar |
| W010 | 🟢 verde | regra presente em `_reversa_sdd/sdd/pii-guard.md` e `_reversa_sdd/domain.md` |

| Data | Resultado | Observação |
|------|-----------|------------|

## Arquivadas

| ID | Motivo | Data |
|----|--------|------|
