# Adendo: quality-evaluator (avaliação de qualidade do dataset)

> Identificador: `007-quality-evaluator`
> Data: `2026-10-12`
> Cenário: greenfield

## Vigência

Vigente desde 2026-10-12.
Superado pela re-extração de 2026-10-12.

## Resumo da entrega

O pacote `sintetica.quality` implementa a skill `sintetica-eval`. A avaliação lê `output/dataset.<ext>` em fluxo e valida cada registro pelo contrato atual. Ela mede 4 números:
- **conformidade:** válidos ÷ volume pedido pelo lote;
- **unicidade estrutural:** hash do JSON canônico;
- **unicidade semântica:** 3-gramas de palavras do texto livre, com Jaccard ≥ 0,8 (Q47);
- **vazamentos de PII:** achados do `PiiGuard` fora da allowlist.

A avaliação calcula a duração desde `started_at` e dá o veredito `APROVADO` ou `REPROVADO`. Ela grava `report.json` e `report.md` do mesmo objeto. Os 2 arquivos mostram só a prévia de cada achado de PII e trazem a seção de escopo e limites da detecção.

O comando `sintetica eval <slug>` termina com 0 em `APROVADO`, 17 em `REPROVADO` e 18 sem dataset final (Q48). O fim do `sintetica generate` roda a mesma avaliação em primeiro plano e em background, sem mudar o código do lote (Q49). O `sintetica status` mostra o veredito.

A busca de quase-duplicados é exata: par a par até 1.000 registros e filtro de prefixo acima disso (D-07, aprovada pelo revisor no lugar do MinHash).

Ações concluídas: 24 de 24 (`progress.jsonl` com 24 registros).

Verificação:
- 516 testes (471 das features 001 a 006 + 45 novos), mais 3 testes `perf` fora da suíte padrão;
- avaliação de 10.000 registros em 3,9 s (meta ≤ 120 s);
- cobertura de 97% em `sintetica.quality`;
- `mypy --strict` e `ruff` sem erros em 140 arquivos;
- 18 cenários Gherkin cobertos.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/prd.md` | 4. Escopo (in), "Pipeline de agentes" (`sintetica-eval`) | componente-novo | `sintetica-eval` implementado: veredito, 4 métricas, duração e relatório em Markdown e JSON. |
| `_reversa_sdd/prd.md` | 3. Métricas de sucesso (conformidade, PII, diversidade, tempo) | componente-novo | As 4 métricas agora são medidas: conformidade ≥ 95%, 0 vazamentos, unicidades ≥ 90% (Q16) e duração com meta de 10 min para até 100 registros. |
| `_reversa_sdd/prd.md` | 8. Riscos (premissa 1, "verificação semântica") | componente-novo | A verificação semântica é a unicidade por 3-gramas e Jaccard, determinística e local; não há LLM-juiz (OQ-02 resolvida pela NG-01). |
| `_reversa_sdd/sdd/quality-evaluator.md` | 6. Requisitos Funcionais (RF-01) | componente-novo | Implementado. Leia o volume pedido como `volume_requested` de `run.json`; sem ele, o volume da intenção, com aviso se divergirem. |
| `_reversa_sdd/sdd/quality-evaluator.md` | 6. Requisitos Funcionais (RF-02, RF-03) | componente-novo | Implementados. Leia RF-03 com a Q47: texto livre são os campos `text` (e o conteúdo das mensagens numa conversa); `enum`, números e datas ficam fora; texto com menos de 3 palavras vira 1 trecho. |
| `_reversa_sdd/sdd/quality-evaluator.md` | 6. Requisitos Funcionais (RF-04) e 10. Integrações (MinHash) | componente-novo | Leia "MinHash com LSH" como busca exata com filtro de prefixo (D-07), sem dependência nova; o resultado é igual ao par a par. A `datasketch` não é usada. |
| `_reversa_sdd/sdd/quality-evaluator.md` | 6. Requisitos Funcionais (RF-05) e 12. Segurança | componente-novo | Implementados com `PiiGuard.leaks` por campo, inclusive em linhas inválidas; o relatório mostra índice, campo, tipo e prévia. |
| `_reversa_sdd/sdd/quality-evaluator.md` | 6. Requisitos Funcionais (RF-06, RF-07) | componente-novo | Implementados. `finished_at` e a duração ficam só no relatório; a intenção não é alterada. A meta de tempo não entra no veredito. |
| `_reversa_sdd/sdd/quality-evaluator.md` | 6. Requisitos Funcionais (RF-08 a RF-10) | componente-novo | Implementados: veredito com as métricas que falharam em ordem fixa; `report.json` e `report.md` do mesmo objeto; seção "Escopo e limites da detecção de PII". |
| `_reversa_sdd/sdd/quality-evaluator.md` | 6. Requisitos Funcionais (RF-11) e 15. Decision Log | componente-novo | Leia o código de `REPROVADO` como 17, não 2 (Q48); dataset ausente ou ilegível dá 18. |
| `_reversa_sdd/sdd/quality-evaluator.md` | 6.2 Fluxo Principal e 6.3 Fluxos Alternativos | componente-novo | O lote chama a avaliação ao terminar (Q49); a avaliação avulsa é `sintetica eval`. Lote incompleto ou interrompido é avaliado com aviso. |
| `_reversa_sdd/sdd/quality-evaluator.md` | 9. Modelo de Dados | delta-de-dados | `Report` ganhou `volume_requested`, `records_read`, `valid_records`, `semantic_applicable`, `pii_findings`, `schema_version`, `warnings` e `problem_indices.near_duplicates`; índices a partir de 0. Detalhe em `data-delta.md`. |
| `_reversa_sdd/sdd/quality-evaluator.md` | 11. Edge Cases (EC-01 a EC-05) | componente-novo | Implementados. Com o lote em andamento, `sintetica eval` devolve 16. |
| `_reversa_sdd/sdd/quality-evaluator.md` | 14. Open Questions (OQ-01, OQ-02) | componente-novo | Resolvidas: OQ-01 pela Q27 e Q47; OQ-02 pela NG-01 (sem LLM-juiz). |
| `_reversa_sdd/addenda/006-batch-generator.md` | Saída do `generate` e do `status` | delta-de-contrato-externo | O fim do lote mostra o bloco da avaliação no lugar de "Próximo passo: avaliação de qualidade"; o `status` mostra "Avaliação: <veredito>". Os códigos do `generate` não mudam. |
| `_reversa_sdd/addenda/004-intent-interview.md` | Comando `sintetica` | delta-de-contrato-externo | O comando ganhou `eval` e os códigos 17 (`REPROVADO`) e 18 (dataset final ausente ou ilegível). |
| `_reversa_sdd/sdd/cli-installer.md` | 10. Integrações e Dependências | componente-novo | Os 9 comandos do runtime Python que as skills chamam já existem (`request`, `submit`, `schema`, `start`, `intent`, `sample`, `generate`, `status`, `eval`); falta o instalador injetar as skills. |

## Regras sob vigilância

W001, W002, W003, W004, W005, W006, W007, W008, W009, W010, W011, W012, W013. Todos estão em "Observações", sem peso de regressão (cenário greenfield). Detalhes em `_reversa_forward/007-quality-evaluator/regression-watch.md`.

## Fontes

- `_reversa_forward/007-quality-evaluator/legacy-impact.md`
- `_reversa_forward/007-quality-evaluator/regression-watch.md`
- `_reversa_forward/007-quality-evaluator/requirements.md`
- `_reversa_forward/007-quality-evaluator/roadmap.md`
- `_reversa_forward/007-quality-evaluator/data-delta.md`
- `_reversa_forward/007-quality-evaluator/interfaces/eval-cli.md`
- `_reversa_forward/007-quality-evaluator/progress.jsonl`
- `_reversa_forward/007-quality-evaluator/actions.md`
