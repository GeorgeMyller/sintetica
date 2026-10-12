# Roadmap: sample-preview (amostra de 3 a 5 registros para aprovação)

> Identificador: `005-sample-preview`
> Data: `2026-10-12`
> Requirements: `_reversa_forward/005-sample-preview/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA
> Cenário: greenfield. Sem `architecture.md`, `c4-context.md`, `state-machines.md`, `dependencies.md` nem `code-analysis.md`. Adendos vigentes lidos: `addenda/001-pii-guard.md` a `addenda/004-intent-interview.md`.

## 1. Resumo da abordagem

🟡 A feature cria o pacote `sintetica.sample` e o subcomando `sintetica sample (run | adjust | approve | show)`. Ela não cria provedor nem validador novos: monta um `GenerationRequest` a partir da intenção (004) e do `record.schema.json` (003), pede os registros por `build_provider(..., harness_available=True)` (002), valida com `load_record_model` (003) e mascara com o `PiiGuard` (001).
🟡 O fluxo segue o protocolo em 2 passos da Q29: `sample run` grava o pedido e devolve o comando `submit` quando o agente ainda não respondeu (`HarnessResponsePending`); a chamada seguinte de `sample run` lê a resposta, valida, mascara, descarta duplicados e, se faltarem registros, já grava o próximo pedido, até 3 tentativas.
🟡 O estado fica em `datasets/<slug>/sample.state.json`. A aprovação grava `seeds/sample.jsonl` e `seeds/sample.meta.json` (Q42). O Expresso aprova sozinho só com N válidos (Q43).
🟡 Cada tentativa traz o número da tentativa nas instruções, para que o pedido tenha um id novo: o `HarnessAgentProvider` devolve a resposta antiga quando o pedido é idêntico.

## 2. Princípios aplicados

🟡 `.reversa/principles.md` não existe. Sem princípios formais para verificar.

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| n/a | Arquivo de princípios ausente | n/a |

🟡 Restrições do PRD tratadas como princípios de fato: privacidade por design (Q21), custo zero no padrão (Q8), tipagem estrita, cobertura ≥ 80% (Q19). Todas são respeitadas.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Novo pacote `sintetica.sample` (`state.py`, `request.py`, `review.py`, `render.py`, `service.py`) | Mesma organização por componente das features 001 a 004 | Estender `sintetica.providers` | 🟡 |
| D-02 | Pré-condição: `schema.state.json` com `status = aprovado` e `schema_version` igual à versão de `schema.json`; senão, código 11 com o comando a rodar | RN-01, RF-01 | Aceitar contrato em revisão | 🟢 |
| D-03 | `GenerationRequest(schema_json = record.schema.json, seeds = registros já aceitos, instructions, n_records = faltantes)`; instruções montadas com objetivo, estrutura e regras definidos da intenção, o ajuste (se houver), "tentativa k de 3" e "não repita os exemplos" | RF-03; os aceitos como sementes evitam duplicados; "tentativa k" garante id novo a cada tentativa (§1) | Pedido sem sementes | 🟡 |
| D-04 | Provedor por `build_provider(k, dataset_dir, project_dir, harness_available=True)`, com o teto de custo padrão da política; `asyncio.run(provider.generate(...))` | RN-03, adendo 002 (harness é o padrão da política) | Instanciar `HarnessAgentProvider` direto (ignoraria a política) | 🟢 |
| D-05 | `HarnessResponsePending` vira o estado `aguardando_agente`, com o id e o comando `submit`; código 0, porque não é erro | RF-04; o agente segue o comando impresso | Código de erro | 🟡 |
| D-06 | Demais `ProviderError` (indisponível, credencial, esgotado, mascaramento) viram código 12 com a mensagem do provedor; o estado não muda | EC-05 da spec | Repassar a exceção | 🟡 |
| D-07 | Revisão de cada registro: `Record.model_validate`; inválido guarda só o 1º erro (caminho e mensagem), nunca o valor; duplicado exato detectado pelo JSON canônico de `to_json_obj`, contra os já aceitos e os do mesmo lote | RN-04, RF-05 | Comparação semântica (fica com o `quality-evaluator`) | 🟡 |
| D-08 | Mascaramento depois da validação: cada texto do registro passa por `PiiGuard.mask(texto, field=<caminho>)`; o registro mascarado é validado de novo; se deixar de ser válido, conta como inválido | RN-05, RF-07; valores falsos podem quebrar `pattern` | Mascarar antes de validar | 🟡 |
| D-09 | Até 3 tentativas por rodada (a 1ª conta); após a 3ª com faltantes: Guiado → `em_revisao` parcial com alerta e sugestão de voltar ao contrato; Expresso → `interrompida`, nada gravado em `seeds/` | RF-06, Q43 | Tentativas por registro | 🟢 |
| D-10 | Exibição: CSV → tabela Markdown com `csv_columns` e `to_csv_row` (com `|` escapado); JSON e JSONL → 1 bloco ```json por registro com decimais exatos | RF-08, Q37 | `model_dump_json` (decimal sai como texto) | 🟡 |
| D-11 | Acrescentar o parâmetro opcional `indent` a `sintetica.schema.formats.to_json_text` (padrão `None`, comportamento atual inalterado) para a exibição formatada | D-10 precisa de JSON formatado com decimal exato | Duplicar o serializador | 🟡 |
| D-12 | `sample adjust <slug> <texto>`: mascara o texto, zera aceitos e tentativas, soma 1 rodada e já executa o `run`; a partir da 4ª rodada, a saída sugere voltar ao contrato | RN-06, RF-09, RF-10 | Manter os aceitos no ajuste | 🟡 |
| D-13 | `sample approve <slug>`: exige estado `em_revisao` ou `interrompida`, contrato atual e ≥ 1 registro aceito; revalida cada aceito com o `Record` atual; grava `seeds/sample.jsonl` (`to_jsonl_line`) e `seeds/sample.meta.json`; parcial gera alerta e `partial: true` | RF-11, RF-14, Q42, Q43 | Gravar no formato do dataset | 🟢 |
| D-14 | Expresso com N válidos aprova na mesma chamada de `run` (mesma rotina do `approve`) | RF-13 | Exigir `approve` também no Expresso | 🟢 |
| D-15 | Mudança de versão do contrato: o `run` descarta o estado antigo com aviso e começa de novo; o `approve` recusa com código 11 | RF-12 | Revalidar os aceitos antigos | 🟡 |
| D-16 | Códigos de saída novos: 11 (contrato não aprovado ou desatualizado), 12 (falha do provedor), 13 (amostra não aprovável); reuso: 2 (dataset, intenção ou argumento), 9 (mascaramento indisponível), 10 (falha de escrita) | Sem colisão com 3 a 8 | Reusar o código 2 para tudo | 🟡 |
| D-17 | Ao aprovar, a saída indica a geração em lote como próximo passo, sem comando (a feature `batch-generator` liga o elo) | RN-09, Q40 | Comando fictício | 🟢 |

> 🟢 nas decisões confirmadas por respostas do revisor (Q29, Q40, Q41, Q42, Q43) ou por código entregue (adendos 002 e 003).

## 4. Premissas

🟡 Nenhuma premissa vinda de `[DÚVIDA]`: o `requirements.md` está com 0 marcadores após o clarify.

| Premissa | Origem (`requirements.md` seção) | Risco se errada |
|----------|----------------------------------|-----------------|
| A política padrão (`harness` primeiro) vale na maioria dos projetos; quem muda a prioridade aceita usar Ollama ou API externa na amostra | 4. RN-03 | Custo pequeno de amostra externa; limitado pelo teto da política |
| O agente consegue ler o arquivo do pedido (`requests/<id>.json`) e gerar o JSONL pedido | 4. RN-03 (Q29) | Mais tentativas; o limite de 3 contém o custo |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `sintetica.sample` | `_reversa_sdd/sdd/sample-preview.md` | componente-novo | Estado, pedido, revisão, exibição e serviço da amostra |
| `sintetica.schema.formats` | `_reversa_sdd/addenda/003-schema-builder.md` | contrato-alterado | `to_json_text` ganha `indent` opcional; chamadas atuais inalteradas |
| `sintetica.cli` | `_reversa_sdd/addenda/004-intent-interview.md` (comando `sintetica`) | contrato-alterado | Subcomando `sample`; demais inalterados |
| `sintetica.providers`, `sintetica.pii`, `sintetica.intent` | adendos 001, 002 e 004 | sem mudança | Consumidos pelas APIs públicas |

Estrutura de arquivos prevista:

```
src/sintetica/sample/__init__.py
src/sintetica/sample/state.py     # SampleState, leitura e gravação atômica
src/sintetica/sample/request.py   # montagem do GenerationRequest (D-03)
src/sintetica/sample/review.py    # validação, duplicados e mascaramento (D-07, D-08)
src/sintetica/sample/render.py    # tabela e blocos JSON (D-10)
src/sintetica/sample/service.py   # run, adjust, approve, show (D-02, D-04 a D-17)
src/sintetica/schema/formats.py   # indent opcional em to_json_text (D-11)
src/sintetica/cli.py              # subcomando sample
tests/sample/…
docs/sample-preview.md
```

## 6. Delta no modelo de dados

- Resumo das mudanças: 🟡 `datasets/<slug>/sample.state.json` novo; `seeds/sample.jsonl` e `seeds/sample.meta.json` na aprovação; pedidos e respostas do harness em `requests/` (formato da feature 002).
- Detalhe completo em: `_reversa_forward/005-sample-preview/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| `sintetica sample run | adjust | approve | show` | arquivo + CLI | `_reversa_forward/005-sample-preview/interfaces/sample-cli.md` |

## 8. Plano de migração

n/a. Arquivos novos; `to_json_text` ganha um parâmetro opcional; `sintetica.cli` só ganha o subcomando `sample`.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| R-01: Pedido idêntico entre tentativas devolve a resposta antiga e o laço não avança | alto | alto | "tentativa k de 3" e aceitos como sementes nas instruções (D-03); teste específico |
| R-02: Mascaramento quebra o `pattern` de um campo | médio | baixo | Revalidação após mascarar (D-08) |
| R-03: PII da resposta do agente aparece na saída ou no estado | alto | médio | Mascarar antes de guardar no estado e antes de exibir; teste que busca o valor original em todos os arquivos e saídas |
| R-04: Amostra aprovada fica presa a um contrato antigo | médio | médio | Versão no estado e na meta; `run` reinicia e `approve` recusa (D-15) |
| R-05: Mudança em `to_json_text` altera a saída de quem já usa | médio | baixo | `indent=None` mantém a saída byte a byte; testes da feature 003 continuam passando |
| R-06: Provedor externo escolhido pela política gera custo na amostra | baixo | baixo | `BudgetedProvider` com o teto da política (adendo 002) |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Re-extração reversa executada e sem regressão vermelha (recomendado, não obrigatório)
- [ ] `mypy --strict` e `ruff` sem erros no projeto
- [ ] Cobertura ≥ 80% em `sintetica.sample`
- [ ] Os 16 cenários Gherkin do `requirements.md` cobertos por testes, com o protocolo real do harness (`RequestStore` e `sintetica submit`)
- [ ] Os 381 testes das features 001 a 004 continuam passando

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-12 | Versão inicial gerada por `/reversa-plan` | reversa |
