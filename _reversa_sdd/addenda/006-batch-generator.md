# Adendo: batch-generator (geração do lote completo)

> Identificador: `006-batch-generator`
> Data: `2026-10-12`
> Cenário: greenfield

## Vigência

Vigente desde 2026-10-12.
Superado pela re-extração de 2026-10-12.

## Resumo da entrega

O pacote `sintetica.batch` implementa a skill `sintetica-generate`. Com o contrato aprovado e atual e a amostra aprovada para a mesma versão, `sintetica generate <slug>` gera o lote (1 a 10.000 registros).

O comando escolhe o provedor pelo volume total e estima o custo pelo tamanho médio da amostra. Acima do teto, ele para sem enviar pedidos até receber `--authorize-usd`. Cada registro é validado pelo contrato. Inválidos e duplicados exatos (SHA-256) são descartados e repostos em até 3 rodadas extras. Dados pessoais viram valores falsos, e o registro é revalidado. Cada bloco é gravado com `fsync` em `output/records.partial.jsonl` antes de `output/run.json` mudar.

Há 3 modos de execução:
- **Harness:** lotes de até 100 registros, com 1 pedido por rodada (Q44).
- **Primeiro plano:** lotes de até 100 registros com provedor automático, em blocos adaptativos de até 10 registros (Q46).
- **Processo separado:** lotes acima de 100 registros, com trava de arquivo, `sintetica status` e `--resume` (Q45).

No fim, o lote gera `output/dataset.<ext>`, em lista JSON, JSONL ou CSV pela RFC 4180, e indica a avaliação de qualidade como próximo passo.

A entrega também mudou a feature 005:
- tornou públicas `first_error` e `mask_value` em `sintetica.sample.review`;
- extraiu `intent_lines` em `sintetica.sample.request`;
- trocou o próximo passo da aprovação da amostra pelo comando `generate`.

Ações concluídas: 30 de 30 (`progress.jsonl` com 30 registros).

Verificação:
- 471 testes (412 das features 001 a 005 + 59 novos), mais 1 teste `perf` fora da suíte padrão;
- cobertura de 92% em `sintetica.batch`;
- `mypy --strict` e `ruff` sem erros em 123 arquivos;
- 17 cenários Gherkin cobertos, com o `sintetica submit` real e processo real em background.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/prd.md` | 4. Escopo (in), "Pipeline de agentes" item 4 | componente-novo | `sintetica-generate` implementado: lote concorrente com `asyncio`, validado, mascarado e gravado por bloco. |
| `_reversa_sdd/prd.md` | 3. Métricas de sucesso (conformidade ≥ 95%) | componente-novo | A meta vira o critério de status: `concluido` com ≥ 95% do volume; abaixo disso, `incompleto`. |
| `_reversa_sdd/prd.md` | 3. Métricas de sucesso (lote de produção) | componente-novo | Lotes acima de 100 registros rodam num processo separado; o comando volta em ≤ 5 s. |
| `_reversa_sdd/sdd/batch-generator.md` | 6. Requisitos Funcionais (RF-01) | componente-novo | Implementado. Leia a semente como `seeds/sample.jsonl` com `schema_version` em `seeds/sample.meta.json`; amostra ausente ou de outra versão gera o código 14. |
| `_reversa_sdd/sdd/batch-generator.md` | 6. Requisitos Funcionais (RF-02) | componente-novo | Implementado como no padrão da feature 002: o comando para com o código 15 e o valor; o agente pergunta e roda de novo com `--authorize-usd`. Preço desconhecido também exige autorização. |
| `_reversa_sdd/sdd/batch-generator.md` | 6. Requisitos Funcionais (RF-03) | componente-novo | Leia "blocos de 10" como bloco adaptativo de até 10, perto de 4.000 tokens de saída, com `--block-size` (Q46). O provedor é escolhido pelo volume total; o harness recebe 1 pedido por rodada (Q44). |
| `_reversa_sdd/sdd/batch-generator.md` | 6. Requisitos Funcionais (RF-04, RF-05, RF-06) | componente-novo | Implementados: 1ª rodada mais até 3 extras só com os faltantes; duplicados por SHA-256 em memória; mascaramento e revalidação antes do disco; a resposta bruta do harness é apagada. |
| `_reversa_sdd/sdd/batch-generator.md` | 6. Requisitos Funcionais (RF-07, RF-09, RF-10) | componente-novo | Implementados. O arquivo parcial é a fonte da verdade; a retomada é `sintetica generate <slug> --resume` e reconta o arquivo. `sintetica status <slug>` mostra o progresso. |
| `_reversa_sdd/sdd/batch-generator.md` | 6. Requisitos Funcionais (RF-08) e 6.3 Fluxo Alternativo A | componente-novo | Implementado com processo em sessão própria (`python -m sintetica.batch.worker`), PID em `run.json` e trava de arquivo `output/run.lock` (Q45). |
| `_reversa_sdd/sdd/batch-generator.md` | 6. Requisitos Funcionais (RF-11) e 6.2 Fluxo Principal, passo 7 | componente-novo | A conversão final está implementada. O lote não chama o `quality-evaluator`: só indica a avaliação como próximo passo (Q40). |
| `_reversa_sdd/sdd/batch-generator.md` | 9. Modelo de Dados | delta-de-dados | `RunState` ganhou os status `iniciando` e `aguardando_agente` e os campos `mode`, `format`, `round`, `block_size`, `avg_tokens`, `estimate_usd`, `provider_reason`, `pending_request_id`, `pending_command`, `stop_cause` e `updated_at`. Detalhe em `data-delta.md`. |
| `_reversa_sdd/sdd/batch-generator.md` | 11. Edge Cases (EC-01 a EC-06) | componente-novo | Implementados. Em todo status final, o arquivo final é gerado. EC-04 usa a trava de arquivo, não só o PID. EC-06 e lote existente geram o código 16, com sugestão de `--resume` ou `--new`. |
| `_reversa_sdd/sdd/batch-generator.md` | 14. Open Questions (OQ-01, OQ-02) | componente-novo | Resolvidas: OQ-01 pela Q28 (acima de 100, background) e OQ-02 pela Q46 (bloco adaptativo). |
| `_reversa_sdd/sdd/quality-evaluator.md` | 6. Requisitos Funcionais e 9. Modelo de Dados | componente-novo | A entrada existe: `output/dataset.<ext>` e `output/run.json` com `status` (`concluido`, `incompleto`, `interrompido_custo`, `falha_provedor`). O lote não chama o avaliador; a feature `quality-evaluator` liga esse elo. |
| `_reversa_sdd/addenda/005-sample-preview.md` | API pública e saída da aprovação | delta-de-contrato-externo | `first_error` e `mask_value` públicos; `intent_lines` nova; a aprovação mostra `Próximo passo: uv run sintetica generate <slug>`. |
| `_reversa_sdd/addenda/004-intent-interview.md` | Comando `sintetica` | delta-de-contrato-externo | O comando ganhou `generate` (`--resume`, `--new`, `--authorize-usd`, `--block-size`) e `status`, e os códigos 14 (amostra ausente ou de outra versão), 15 (custo exige autorização) e 16 (lote em andamento, interrompido ou existente). |
| `_reversa_sdd/addenda/002-llm-provider.md` | `build_provider` e protocolo do harness | componente-novo | O lote é o 1º consumidor de `authorized_usd` e `per_request_estimate`; na retomada, o teto passado desconta o custo já gasto. |

## Regras sob vigilância

W001, W002, W003, W004, W005, W006, W007, W008, W009, W010, W011, W012, W013, W014. Todos estão em "Observações", sem peso de regressão (cenário greenfield). Detalhes em `_reversa_forward/006-batch-generator/regression-watch.md`.

## Fontes

- `_reversa_forward/006-batch-generator/legacy-impact.md`
- `_reversa_forward/006-batch-generator/regression-watch.md`
- `_reversa_forward/006-batch-generator/requirements.md`
- `_reversa_forward/006-batch-generator/roadmap.md`
- `_reversa_forward/006-batch-generator/data-delta.md`
- `_reversa_forward/006-batch-generator/interfaces/generate-cli.md`
- `_reversa_forward/006-batch-generator/progress.jsonl`
- `_reversa_forward/006-batch-generator/actions.md`
