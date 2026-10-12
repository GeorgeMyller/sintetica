# Adendo: sample-preview (amostra de 3 a 5 registros para aprovação)

> Identificador: `005-sample-preview`
> Data: `2026-10-12`
> Cenário: greenfield

## Vigência

Vigente desde 2026-10-12.
Superado pela re-extração de 2026-10-12.

## Resumo da entrega

O pacote `sintetica.sample` implementa a skill `sintetica-sample`: com o contrato aprovado e atual, `sintetica sample run` pede de 3 a 5 registros ao provedor da política (o agente do harness, no padrão), lê a resposta na chamada seguinte, valida cada registro pelo contrato, descarta inválidos e duplicados, troca dados pessoais por valores falsos, revalida e pede os faltantes, até 3 tentativas. O usuário aprova (`sample approve`), ajusta (`sample adjust`) ou volta ao contrato. A aprovação grava `seeds/sample.jsonl` e `seeds/sample.meta.json`. No Expresso, a amostra com N válidos é aprovada na mesma chamada; a parcial interrompe a automação.

A entrega acrescentou o parâmetro opcional `indent` a `sintetica.schema.formats.to_json_text` e o subcomando `sample` ao comando `sintetica`.

Ações concluídas: 18 de 18 (`progress.jsonl` com 18 registros). Verificação: 412 testes (381 das features 001 a 004 + 31 novos), cobertura de 96% em `sintetica.sample`, `mypy --strict` e `ruff` sem erros em 102 arquivos, 16 cenários Gherkin cobertos com o `sintetica submit` real.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/prd.md` | 4. Escopo (in), "Pipeline de agentes" item 3 | componente-novo | `sintetica-sample` implementado: amostra de 3 a 5 registros validada, mascarada e aprovada antes do lote. |
| `_reversa_sdd/prd.md` | 8. Riscos (premissa 1: qualidade da geração) | componente-novo | A mitigação por amostra existe; a amostra aprovada vira semente para a geração em lote. |
| `_reversa_sdd/sdd/sample-preview.md` | 6. Requisitos Funcionais (RF-01, RF-02) | componente-novo | Implementados. Leia RF-01 com a Q41 (padrão 3, `--n` de 3 a 5) e RF-02 como "provedor da política com o harness disponível" (protocolo `request`/`submit` da Q29). |
| `_reversa_sdd/sdd/sample-preview.md` | 6. Requisitos Funcionais (RF-03) | componente-novo | Leia as 3 tentativas como 3 por rodada, não por registro; cada tentativa pede só os faltantes, com id de pedido próprio. |
| `_reversa_sdd/sdd/sample-preview.md` | 6. Requisitos Funcionais (RF-04) | componente-novo | Implementado com `PiiGuard.mask` por campo e revalidação; valor falso que quebra a regra do campo descarta o registro. A resposta bruta do agente (`requests/<id>.response.jsonl`) é apagada depois de lida. |
| `_reversa_sdd/sdd/sample-preview.md` | 6. Requisitos Funcionais (RF-05, RF-06, RF-08) | componente-novo | Implementados: tabela para CSV, blocos JSON com decimal exato; opções aprovar, ajustar e voltar ao contrato; sugestão a partir da 4ª rodada de ajuste. |
| `_reversa_sdd/sdd/sample-preview.md` | 6. Requisitos Funcionais (RF-07) | componente-novo | Leia a semente como `seeds/sample.jsonl` mais `seeds/sample.meta.json` (Q42), não `sample.<ext>`. |
| `_reversa_sdd/sdd/sample-preview.md` | 6. Requisitos Funcionais (RF-09) | componente-novo | Leia RF-09 com a Q43: Expresso aprova sozinho só com N válidos; parcial interrompe e exige decisão; no Guiado, parcial é aprovável com pelo menos 1 registro e alerta. |
| `_reversa_sdd/sdd/sample-preview.md` | 9. Modelo de Dados | componente-novo | Leia `SampleFile` como 2 arquivos; `SampleMeta` ganhou `n_requested`, `n_records`, `partial` e `rounds`. O estado da rodada fica em `sample.state.json`. |
| `_reversa_sdd/sdd/sample-preview.md` | 11. Edge Cases (EC-02) | componente-novo | Resposta que não é JSON é recusada pelo `sintetica submit` (código 5) e não gasta tentativa. |
| `_reversa_sdd/sdd/sample-preview.md` | 14. Open Questions (OQ-01, OQ-02) | componente-novo | Resolvidas: OQ-01 pela Q41 (padrão 3) e OQ-02 pela Q29 (protocolo `request`/`submit`). |
| `_reversa_sdd/addenda/003-schema-builder.md` | API pública (`to_json_text`) | delta-de-contrato-externo | `to_json_text(obj, indent=None)`: parâmetro novo e opcional; com `None`, a saída é idêntica à anterior. |
| `_reversa_sdd/addenda/004-intent-interview.md` | Comando `sintetica` | delta-de-contrato-externo | O comando ganhou `sample (run, adjust, approve, show)` e os códigos 11 (contrato não aprovado ou desatualizado), 12 (falha do provedor) e 13 (amostra não aprovável). |
| `_reversa_sdd/addenda/002-llm-provider.md` | Protocolo do harness (`requests/`) | componente-novo | A amostra é o 1º consumidor do protocolo: grava pedidos únicos por tentativa e apaga cada resposta depois de lê-la. |
| `_reversa_sdd/sdd/batch-generator.md` | 6. Requisitos Funcionais (RF-01) | componente-novo | A semente existe: leia `seeds/sample.jsonl` (aceito por `--seeds`) e confira `schema_version` em `seeds/sample.meta.json` contra o contrato atual antes de iniciar o lote. |

## Regras sob vigilância

W001, W002, W003, W004, W005, W006, W007, W008, W009, W010. Todos em "Observações", sem peso de regressão (cenário greenfield). Detalhes em `_reversa_forward/005-sample-preview/regression-watch.md`.

## Fontes

- `_reversa_forward/005-sample-preview/legacy-impact.md`
- `_reversa_forward/005-sample-preview/regression-watch.md`
- `_reversa_forward/005-sample-preview/requirements.md`
- `_reversa_forward/005-sample-preview/data-delta.md`
- `_reversa_forward/005-sample-preview/interfaces/sample-cli.md`
- `_reversa_forward/005-sample-preview/progress.jsonl`
- `_reversa_forward/005-sample-preview/actions.md`
