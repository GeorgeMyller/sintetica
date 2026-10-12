# Legacy Impact: sample-preview

> Identificador: `005-sample-preview`
> Data: `2026-10-12`
> Feature greenfield, sem legado pré-existente. Âncora: prd.md + specs SDD.
> Política de edição no momento da execução: `allowLegacyEdits: true`, `allowedPaths: []` (projeto inteiro liberado, sem restrição de caminho).

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `src/sintetica/cli.py` | Comando `sintetica` (`_reversa_sdd/addenda/004-intent-interview.md`) | delta-de-contrato-externo | MEDIUM | Subcomando `sample (run, adjust, approve, show)` e códigos 11, 12 e 13; demais inalterados |
| `src/sintetica/schema/formats.py` | `schema-builder` (`_reversa_sdd/addenda/003-schema-builder.md`) | delta-de-contrato-externo | LOW | `to_json_text` ganhou `indent` opcional; com `None`, saída idêntica (teste) |
| `tests/schema/test_formats.py` | `schema-builder` | componente-novo | LOW | 1 teste novo para `indent` |
| `src/sintetica/sample/state.py` | `sample-preview` (`_reversa_sdd/sdd/sample-preview.md#9`) | componente-novo | MEDIUM | Estado da rodada e metadados da semente |
| `src/sintetica/sample/request.py` | `sample-preview` (RF-02, RF-03) | componente-novo | MEDIUM | Pedido com tentativa no texto para ter id único (R-01) |
| `src/sintetica/sample/review.py` | `sample-preview` (RF-03, RF-04) e `pii-guard` | componente-novo | HIGH | Validação, duplicados, mascaramento e revalidação antes de guardar qualquer registro |
| `src/sintetica/sample/render.py` | `sample-preview` (RF-05) | componente-novo | LOW | Tabela e blocos JSON |
| `src/sintetica/sample/service.py`, `__init__.py` | `sample-preview` (RF-06 a RF-09) e `llm-provider` | componente-novo | HIGH | Laço de tentativas, aprovação, Expresso; apaga a resposta bruta do agente depois de lida |
| `tests/sample/*.py` | `sample-preview` | componente-novo | LOW | 30 testes, de ponta a ponta com o `sintetica submit` real |
| `docs/sample-preview.md` | `sample-preview` | componente-novo | LOW | Fluxo da skill `sintetica-sample` |

## Diff conceitual por componente

**Comando `sintetica`.** Ganha `sample`, importado de forma tardia. Os códigos 11 (contrato não aprovado ou desatualizado), 12 (falha do provedor) e 13 (amostra não aprovável) somam-se aos 0 e 2 a 10.

**schema-builder.** `to_json_text(obj, indent=None)`: parâmetro novo e opcional; quem já chamava a função continua com a mesma saída.

**llm-provider (harness).** Sem mudança de código. A amostra apaga `requests/<id>.response.jsonl` depois de ler a resposta, para que só a versão mascarada fique no disco. O pedido (`requests/<id>.json`) continua no disco; ele só contém textos já mascarados (intenção, ajuste) e registros aceitos mascarados.

**sample-preview.** Componente novo, conforme `_reversa_sdd/sdd/sample-preview.md`, com estes desvios:
- A semente é `seeds/sample.jsonl` mais `seeds/sample.meta.json` (Q42), e não `sample.<ext>` com o `SampleFile` único.
- Tentativas contadas por rodada (3 no total), não por registro.
- Resposta que não é JSON é recusada pelo `submit` (feature 002) e não gasta tentativa.
- Amostra parcial: aprovável no Guiado com alerta; no Expresso, interrompe (Q43).
- Decisão nova da execução: a resposta bruta do agente é apagada após a leitura.

## Preservadas

Nenhuma. Feature greenfield, sem regras 🟢 extraídas de código anterior.

## Modificadas

Nenhuma. Feature greenfield, sem regras 🟢 extraídas de código anterior.
