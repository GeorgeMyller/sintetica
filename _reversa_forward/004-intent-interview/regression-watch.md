# Regression Watch: intent-interview

> Identificador: `004-intent-interview`
> Data: `2026-10-12`
> Feature greenfield. Não há regras 🟢 para vigiar. O watch principal fica vazio. Os requisitos implementados ficam em "Observações", sem peso de regressão, até uma extração `/reversa` futura confirmá-los como 🟢.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|-------------------------|-----------------------------|---------------------|-------------------|

## Observações

| ID | Origem (arquivo, seção) | Regra esperada | Tipo de verificação | Sinal de violação |
|----|-------------------------|----------------|---------------------|-------------------|
| W001 | `_reversa_forward/004-intent-interview/requirements.md#4` RN-01 (Q20) | `datasets/<slug>/seeds/` e `started_at` existem antes da primeira pergunta | presença | `sintetica start` sem pasta, sem `seeds/` ou sem `started_at` |
| W002 | `requirements.md#4` RN-02 | Slug kebab-case ASCII, até 60 caracteres; colisão vira `-2`, `-3` | presença | Pasta existente sobrescrita ou slug com acento |
| W003 | `requirements.md#4` RN-04 (Q21) | Objetivo, estrutura e regras só vão ao disco depois do mascaramento; falha de política não grava nada | presença | Valor original de PII em `intent.json`, na saída ou nos avisos |
| W004 | `requirements.md#4` RN-06 (Q38) | "Não sei" em formato e volume vira JSONL e 10, com origem `padrao` | presença | Outro padrão, ou origem ausente |
| W005 | `requirements.md#4` RN-07 | Formatos CSV, JSON, JSONL; volume de 1 a 10.000; 3ª recusa seguida aplica o padrão | presença | Formato fora da lista aceito, ou volume fora do intervalo gravado |
| W006 | `requirements.md#4` RN-08 (Q39) | Guiado sempre confirma; Expresso só confirma com objetivo e estrutura indefinidos | presença | `schema build` indicado sem confirmação no Guiado |
| W007 | `requirements.md#4` RN-09 (Q40) | O resumo pronto indica `uv run sintetica schema build <slug>` | redação | Próximo passo diferente ou ausente com a intenção pronta |
| W008 | `roadmap.md#3` D-16, RF-17 | `intent.json` da entrevista é aceito por `sintetica.schema.intent.load_intent` e por `sintetica schema build` | presença | `tests/intent/test_contract_schema.py` falha |
| W009 | `data-delta.md#1` D-02 | Chaves de outras features em `intent.json` sobrevivem à regravação | presença | `finished_at` (ou outra chave extra) some após `intent set` |
| W010 | `interfaces/intent-cli.md#6` | Códigos 8, 9 e 10 exclusivos da entrevista | redação | Colisão com os códigos 2 a 7 das features 002 e 003 |

## Histórico de re-extrações

### Re-extração 2026-10-12 12:00

> Watch principal vazio (feature greenfield). Itens de "Observações" verificados de forma informativa, sem peso de regressão.

| ID | Veredito | Observação |
|----|----------|------------|
| W001 | 🟢 verde | regra presente em `_reversa_sdd/sdd/intent-interview.md` e `_reversa_sdd/domain.md` |
| W002 | 🟢 verde | regra presente em `_reversa_sdd/sdd/intent-interview.md` e `_reversa_sdd/domain.md` |
| W003 | 🟢 verde | regra presente em `_reversa_sdd/sdd/intent-interview.md` e `_reversa_sdd/domain.md` |
| W004 | 🟢 verde | regra presente em `_reversa_sdd/sdd/intent-interview.md` e `_reversa_sdd/domain.md` |
| W005 | 🟢 verde | regra presente em `_reversa_sdd/sdd/intent-interview.md` e `_reversa_sdd/domain.md` |
| W006 | 🟢 verde | regra presente em `_reversa_sdd/sdd/intent-interview.md` e `_reversa_sdd/domain.md` |
| W007 | 🟡 amarelo | Mudança deliberada da feature 008: o resumo cita `<cli_command()> schema build <slug>`; sem `SINTETICA_CMD`, o texto é idêntico (`sdd/intent-interview.md` RF-10, RF-15) |
| W008 | 🟢 verde | regra presente em `_reversa_sdd/sdd/intent-interview.md` e `_reversa_sdd/domain.md` |
| W009 | 🟢 verde | regra presente em `_reversa_sdd/sdd/intent-interview.md` e `_reversa_sdd/domain.md` |
| W010 | 🟢 verde | regra presente em `_reversa_sdd/sdd/intent-interview.md` e `_reversa_sdd/domain.md` |

| Data | Resultado | Observação |
|------|-----------|------------|

## Arquivadas

| ID | Motivo | Data |
|----|--------|------|
