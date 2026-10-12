# Legacy Impact: intent-interview

> Identificador: `004-intent-interview`
> Data: `2026-10-12`
> Feature greenfield, sem legado pré-existente. Âncora: prd.md + specs SDD.
> Política de edição no momento da execução: `allowLegacyEdits: true`, `allowedPaths: []` (projeto inteiro liberado, sem restrição de caminho).

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/sintetica/cli.py` | Comando `sintetica` (`_reversa_sdd/addenda/003-schema-builder.md`) | delta-de-contrato-externo | MEDIUM | Subcomandos `start` e `intent (questions, set, show, confirm)` e códigos 8, 9 e 10; demais inalterados |
| `src/sintetica/fsutil.py` | Utilitário compartilhado | componente-novo | LOW | `write_atomic`; as cópias das features 002 e 003 continuam (dívida registrada) |
| `src/sintetica/intent/model.py` | `intent-interview` (`_reversa_sdd/sdd/intent-interview.md#9`) | componente-novo | HIGH | Formato de `intent.json`, lido pelo `schema-builder` e pelos componentes seguintes |
| `src/sintetica/intent/slug.py` | `intent-interview` (RF-02, EC-01) | componente-novo | LOW | Slug e criação da pasta sem corrida |
| `src/sintetica/intent/answers.py` | `intent-interview` (RF-05 a RF-08, RF-11) e `pii-guard` | componente-novo | HIGH | Validação e mascaramento antes de gravar (Q21) |
| `src/sintetica/intent/summary.py` | `intent-interview` (RF-09, RF-10, Q39, Q40) | componente-novo | MEDIUM | Regra de confirmação e próximo passo |
| `src/sintetica/intent/questions.py` | `intent-interview` (RNF-05) | componente-novo | LOW | Texto das 5 perguntas |
| `src/sintetica/intent/service.py`, `__init__.py` | `intent-interview` | componente-novo | MEDIUM | Orquestração e API pública |
| `tests/intent/*.py` | `intent-interview` | componente-novo | LOW | 55 testes, incluindo o contrato com o `schema-builder` |
| `docs/intent-interview.md` | `intent-interview` | componente-novo | LOW | Fluxo da skill `sintetica-start`, citação no shell, códigos |

## Diff conceitual por componente

**Comando `sintetica`.** Ganha `start` e `intent`, importados de forma tardia. Os códigos 8 (resposta inválida), 9 (mascaramento indisponível) e 10 (falha de escrita) somam-se aos 0 e 2 a 7 das features 002 e 003.

**intent-interview.** Componente novo, conforme `_reversa_sdd/sdd/intent-interview.md`, com estes desvios:
- `Item.status` ganhou `pendente`; `format` e `volume` (com as origens) são anuláveis até a resposta; `intent.json` ganhou `volume_rejections` e `confirmed_at` e preserva chaves de outras features.
- O agente conduz a conversa e chama `sintetica intent set` a cada resposta (padrão da Q29); "não sei" é explícito (`--unknown`).
- O encadeamento vai até `sintetica schema build` (Q40); no Expresso, só objetivo e estrutura indefinidos exigem confirmação (Q39).
- Padrões para "não sei": JSONL e 10 registros (Q38).

**pii-guard e schema-builder.** Sem mudança de código. A entrevista é o 1º componente a gravar em `.pii_allowlist`. O leitor de `intent.json` do `schema-builder` aceita a intenção sem ajuste (teste de contrato).

## Preservadas

Nenhuma. Feature greenfield, sem regras 🟢 extraídas de código anterior.

## Modificadas

Nenhuma. Feature greenfield, sem regras 🟢 extraídas de código anterior.
