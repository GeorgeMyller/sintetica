# Adendo: intent-interview (entrevista de intenção e pasta do dataset)

> Identificador: `004-intent-interview`
> Data: `2026-10-12`
> Cenário: greenfield

## Vigência

Vigente desde 2026-10-12.
Superado pela re-extração de 2026-10-12.

## Resumo da entrega

O pacote `sintetica.intent` implementa a entrevista de intenção, ponto de entrada da skill `sintetica-start`. O comando `sintetica start` cria `datasets/<slug>/seeds/` e o `intent.json` inicial com `started_at` antes de qualquer pergunta, e mostra o caminho absoluto. O agente do harness conduz a conversa e registra cada resposta com `sintetica intent set`; o runtime mascara objetivo, estrutura e regras com o `PiiGuard` antes de gravar, valida formato e volume, aplica os padrões de "não sei" e devolve o resumo. `sintetica intent confirm` registra a confirmação, e o resumo indica `sintetica schema build` quando a intenção está pronta. `sintetica intent questions` traz as 5 perguntas sem jargão.

A entrega também criou o utilitário `sintetica.fsutil.write_atomic`.

Ações concluídas: 19 de 19 (`progress.jsonl` com 19 registros). Verificação: 381 testes (326 das features 001 a 003 + 55 novos), cobertura de 99% em `sintetica.intent` e 100% em `sintetica.fsutil`, `mypy --strict` e `ruff` sem erros em 90 arquivos, teste de contrato com o `schema-builder` passando.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/prd.md` | 3. Métricas de sucesso (tempo da ideia ao dataset) | componente-novo | O início da medição (Q20) agora existe: `started_at` em UTC, gravado por `sintetica start` antes da primeira pergunta. |
| `_reversa_sdd/prd.md` | 4. Escopo (in), "Entrevista de intenção" | componente-novo | Pasta imediata, entrevista sem jargão, modos Guiado e Expresso e selo INDEFINIDO implementados pelos comandos `sintetica start` e `sintetica intent`. |
| `_reversa_sdd/sdd/intent-interview.md` | 6. Requisitos Funcionais (RF-01 a RF-04) | componente-novo | Implementados. Leia a skill como orquestradora: o agente conduz a conversa e o runtime grava por comandos (padrão da Q29). Slug com até 60 caracteres. |
| `_reversa_sdd/sdd/intent-interview.md` | 6. Requisitos Funcionais (RF-05 a RF-07) | componente-novo | Leia "não sei" como `--unknown <item>` explícito. Padrões da Q38: JSONL e 10 registros, marcados como `(padrão)`. Volume aceita separador de milhar. |
| `_reversa_sdd/sdd/intent-interview.md` | 6. Requisitos Funcionais (RF-08) | componente-novo | Implementado com `PiiGuard.mask` antes de gravar; política inválida ou allowlist sem gravação geram o código 9 sem gravar nada. |
| `_reversa_sdd/sdd/intent-interview.md` | 6. Requisitos Funcionais (RF-09, RF-10) | componente-novo | Leia RF-10 com as Q39 e Q40: no Expresso, só objetivo e estrutura indefinidos exigem confirmação; a cadeia vai até `sintetica schema build` e as próximas features acrescentam os elos seguintes. Resposta nova em item confirmado exige nova confirmação. |
| `_reversa_sdd/sdd/intent-interview.md` | 6. Requisitos Funcionais (RF-11) | componente-novo | Leia a 3ª tentativa como a 3ª recusa seguida: as 2 primeiras retornam o código 8; a 3ª grava o padrão 10 com aviso. |
| `_reversa_sdd/sdd/intent-interview.md` | 9. Modelo de Dados | componente-novo | Leia `Item.status` com o valor novo `pendente`; `format`, `volume` e as origens são anuláveis até a resposta; `intent.json` ganhou `volume_rejections` e `confirmed_at` e preserva chaves gravadas por outras features. |
| `_reversa_sdd/sdd/intent-interview.md` | 14. Open Questions (OQ-01, OQ-02) | componente-novo | Resolvidas: OQ-01 pela Q38 (JSONL e 10) e OQ-02 pela Q39 (confirmação só com objetivo e estrutura indefinidos). |
| `_reversa_sdd/addenda/003-schema-builder.md` | Comando `sintetica` | delta-de-contrato-externo | O comando ganhou `start` e `intent (questions, set, show, confirm)` e os códigos 8 (resposta inválida), 9 (mascaramento indisponível) e 10 (falha de escrita). `sintetica schema build` aceita a intenção da entrevista sem ajuste, mas ainda não verifica `confirmed_at`. |
| `_reversa_sdd/addenda/001-pii-guard.md` | Fachada `PiiGuard` | componente-novo | A entrevista é o 1º componente a gravar em `datasets/<slug>/.pii_allowlist`; os valores falsos inseridos nela são reconhecidos pela geração e pela avaliação. |
| `_reversa_sdd/sdd/sample-preview.md`, `batch-generator.md`, `quality-evaluator.md` | 10. Integrações e Dependências | componente-novo | `intent.json` existe e pode ser lido com `sintetica.intent.load_intent_model`; o `quality-evaluator` lê `started_at` e pode gravar chaves próprias (ex.: `finished_at`) sem perdê-las numa nova resposta da entrevista. |

## Regras sob vigilância

W001, W002, W003, W004, W005, W006, W007, W008, W009, W010. Todos em "Observações", sem peso de regressão (cenário greenfield). Detalhes em `_reversa_forward/004-intent-interview/regression-watch.md`.

## Fontes

- `_reversa_forward/004-intent-interview/legacy-impact.md`
- `_reversa_forward/004-intent-interview/regression-watch.md`
- `_reversa_forward/004-intent-interview/requirements.md`
- `_reversa_forward/004-intent-interview/data-delta.md`
- `_reversa_forward/004-intent-interview/interfaces/intent-cli.md`
- `_reversa_forward/004-intent-interview/progress.jsonl`
- `_reversa_forward/004-intent-interview/actions.md`
