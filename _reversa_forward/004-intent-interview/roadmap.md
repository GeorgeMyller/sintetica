# Roadmap: intent-interview (entrevista de intenção e pasta do dataset)

> Identificador: `004-intent-interview`
> Data: `2026-10-12`
> Requirements: `_reversa_forward/004-intent-interview/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA
> Cenário: greenfield. Sem `architecture.md`, `c4-context.md`, `state-machines.md`, `dependencies.md` nem `code-analysis.md`. Adendos vigentes lidos: `addenda/001-pii-guard.md`, `addenda/002-llm-provider.md`, `addenda/003-schema-builder.md`.

## 1. Resumo da abordagem

🟡 A feature cria o pacote `sintetica.intent` e 2 grupos de comando: `sintetica start` e `sintetica intent (questions | set | show | confirm)`.
🟡 O agente do harness conduz a conversa (mesmo padrão da Q29). A cada resposta, ele chama `sintetica intent set`; o runtime mascara o texto com o `PiiGuard` (feature 001), valida, grava `intent.json` de forma atômica e devolve o resumo.
🟡 `sintetica start` resolve o slug, cria `datasets/<slug>/seeds/`, grava o `intent.json` inicial com `started_at` (Q20) e mostra o caminho absoluto, antes de qualquer pergunta.
🟡 O resumo indica o próximo comando (`sintetica schema build`) quando a intenção está completa e confirmada (Guiado) ou dispensada de confirmação (Expresso, exceto objetivo e estrutura indefinidos, Q39). A cadeia termina aí nesta feature (Q40).
🟡 O `intent.json` mantém o formato que o leitor tolerante do `schema-builder` (feature 003) já aceita; um teste de contrato garante isso.

## 2. Princípios aplicados

🟡 `.reversa/principles.md` não existe. Sem princípios formais para verificar.

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| n/a | Arquivo de princípios ausente | n/a |

🟡 Restrições do PRD tratadas como princípios de fato: privacidade por design (Q15, Q21), operação local, tipagem estrita, cobertura ≥ 80% (Q19). Todas são respeitadas.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Novo pacote `sintetica.intent` (`model.py`, `slug.py`, `answers.py`, `summary.py`, `service.py`) | Mesma organização por componente das features 001 a 003 | Estender `sintetica.schema.intent` | 🟡 |
| D-02 | Modelo `IntentModel` em Pydantic com `extra="allow"`: valida o que a entrevista grava e preserva chaves acrescentadas por features futuras (ex.: `finished_at`) | Pydantic já é dependência (feature 003); `allow` evita apagar dados de outros componentes | `extra="forbid"`; dataclasses | 🟡 |
| D-03 | `Item.status` ganha o valor `pendente` (ainda não respondido), além de `definido` e `indefinido`; `format` e `volume` ficam `null` até a resposta | O resumo precisa distinguir "não respondido" de "não sei" | Ausência da chave | 🟡 |
| D-04 | Slug: NFKD → ASCII, minúsculas, não alfanumérico → `-`, `-` repetido colapsado, sem `-` nas pontas, até 60 caracteres; vazio → `dataset-AAAAMMDD-HHMMSS` (UTC); pasta existente → `-2`, `-3`… | RN-02 | Recusar slug repetido | 🟡 |
| D-05 | `sintetica start [nome] [--mode guiado|expresso]` cria a pasta, `seeds/` e `intent.json` num único comando, e só depois imprime o caminho absoluto | RN-01, Q20 | 2 comandos (criar e iniciar) | 🟢 |
| D-06 | `sintetica intent set <slug>` com `--objective`, `--structure`, `--rules`, `--format`, `--volume` e `--unknown <item>` (repetível); vários itens numa chamada atendem o Expresso | RF-04, RF-05; "não sei" explícito evita adivinhar a intenção pelo texto | Detectar "não sei" no texto; entrada JSON | 🟡 |
| D-07 | Cada texto passa por `PiiGuard.for_dataset(dataset, <projeto>/.sintetica/policy.json).mask(...)` antes de gravar; `PolicyError` ou erro de escrita da allowlist encerram com código 9 sem gravar nada | RN-04, falha segura (adendo 001) | Mascarar só no envio externo | 🟢 |
| D-08 | Formato aceito sem diferenciar maiúsculas (`CSV`, `json`, `JsonL`); outro valor → código 8 com a lista dos 3 formatos | RN-07, RF-08 | Aceitar sinônimos (`planilha`) | 🟡 |
| D-09 | Volume fora de 1 a 10.000 → código 8 e soma 1 em `volume_rejections`; na 3ª recusa seguida, grava 10 com origem `padrao` e aviso; volume válido zera o contador | RN-07, RF-09 | Contador na skill | 🟡 |
| D-10 | Padrões da Q38: `--unknown format` → `jsonl` (origem `padrao`); `--unknown volume` → `10` (origem `padrao`) | RN-06, Q38 | — | 🟢 |
| D-11 | Regra de confirmação: Guiado exige `sintetica intent confirm`; Expresso dispensa, exceto com objetivo e estrutura `indefinido` ao mesmo tempo (Q39). A confirmação grava `confirmed_at` | RN-08 | Confirmar sempre | 🟢 |
| D-12 | O resumo indica `uv run sintetica schema build <slug>` só quando a intenção está completa e confirmada (ou dispensada); a cadeia para aí (Q40) | RN-09 | Orquestrador `sintetica run` | 🟢 |
| D-13 | `sintetica intent questions [--mode]` imprime as 5 perguntas em linguagem simples, com 1 exemplo por persona; no Expresso, num único bloco | RF-10 da spec, RNF de linguagem; a skill não precisa repetir o texto | Perguntas só no `SKILL.md` | 🟡 |
| D-14 | Códigos de saída novos: 8 (resposta inválida), 9 (mascaramento indisponível), 10 (falha de escrita); 2 continua "dataset ou intenção ausente" | Sem colisão com 3 a 5 (harness) e 6 a 7 (schema) | Reusar o código 2 | 🟡 |
| D-15 | Escrita atômica (temporário + `os.replace`) num utilitário novo `sintetica.fsutil.write_atomic` | RF-11, RF-16 | Importar `sintetica.schema.state.write_atomic` (acoplaria `intent` a `schema`) | 🟡 |
| D-16 | Teste de contrato: a intenção gravada pela entrevista é lida por `sintetica.schema.intent.load_intent` e aceita por `sintetica schema build` | RF-17 | Unificar os 2 leitores agora | 🟢 |
| D-17 | Textos longos no resumo truncados em 80 caracteres com `…`; o arquivo guarda o texto completo (mascarado) | Resumo legível no chat | Sem truncar | 🟡 |

> 🟢 nas decisões confirmadas por respostas do revisor (Q20, Q38, Q39, Q40) ou por código entregue (adendos 001 e 003).

## 4. Premissas

🟡 Nenhuma premissa vinda de `[DÚVIDA]`: o `requirements.md` está com 0 marcadores após o clarify.

| Premissa | Origem (`requirements.md` seção) | Risco se errada |
|----------|----------------------------------|-----------------|
| O agente do harness consegue passar textos com aspas e quebras de linha como argumentos de linha de comando | 4. RN-03 | Respostas truncadas; mitigação em R-02 |
| `.sintetica/policy.json` fica na raiz do projeto (`--project-dir`) | 2. Contexto (adendo 001) | Padrões extras de PII ignorados; a feature `cli-installer` confirma o caminho |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `sintetica.intent` | `_reversa_sdd/sdd/intent-interview.md` | componente-novo | Modelo, slug, respostas, resumo e serviço da entrevista |
| `sintetica.fsutil` | — | componente-novo | `write_atomic` compartilhável |
| `sintetica.cli` | `_reversa_sdd/addenda/003-schema-builder.md` (comando `sintetica`) | contrato-alterado | Subcomandos `start` e `intent`; os demais inalterados |
| `sintetica.pii` | `_reversa_sdd/addenda/001-pii-guard.md` | sem mudança | Consumido pela fachada `PiiGuard` |
| `sintetica.schema` | `_reversa_sdd/addenda/003-schema-builder.md` | sem mudança | Consumidor de `intent.json`; coberto pelo teste de contrato (D-16) |

Estrutura de arquivos prevista:

```
src/sintetica/fsutil.py
src/sintetica/intent/__init__.py
src/sintetica/intent/model.py      # IntentModel, Item, ITEM_NAMES, padrões (D-02, D-03, D-10)
src/sintetica/intent/slug.py       # resolve_slug (D-04)
src/sintetica/intent/answers.py    # aplicação das respostas, mascaramento, validação (D-06 a D-10)
src/sintetica/intent/summary.py    # resumo, completude, próximo passo (D-11, D-12, D-17)
src/sintetica/intent/questions.py  # texto das 5 perguntas (D-13)
src/sintetica/intent/service.py    # start, set, show, confirm, questions
src/sintetica/cli.py               # subcomandos start e intent (alterado)
tests/intent/…
docs/intent-interview.md
```

## 6. Delta no modelo de dados

- Resumo das mudanças: 🟡 `intent.json` com os campos da spec mais `pendente` em `Item.status`, `confirmed_at` e `volume_rejections`; `format`, `format_source`, `volume` e `volume_source` anuláveis até a resposta.
- Detalhe completo em: `_reversa_forward/004-intent-interview/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| `sintetica start` e `sintetica intent` | arquivo + CLI | `_reversa_forward/004-intent-interview/interfaces/intent-cli.md` |

## 8. Plano de migração

n/a. Arquivos novos; `sintetica.cli` só ganha subcomandos.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| R-01: PII digitada pelo usuário chega ao disco | alto | baixo | Mascaramento antes de qualquer escrita (D-07); teste que busca o valor original em todos os arquivos da pasta |
| R-02: Resposta com aspas ou quebra de linha se perde na passagem por argumento | médio | médio | Testes com aspas, quebra de linha e acentos; o `docs/intent-interview.md` orienta a skill a usar aspas simples do shell |
| R-03: Formato de `intent.json` diverge do leitor do `schema-builder` | médio | baixo | Teste de contrato D-16 |
| R-04: Slug com nome muito longo ou só símbolos | baixo | médio | D-04: limite de 60 caracteres e padrão por data |
| R-05: Duas entrevistas simultâneas com o mesmo nome | baixo | baixo | Criação da pasta com `mkdir(exist_ok=False)` em laço; a 2ª recebe `-2` |
| R-06: Falha no meio da gravação corrompe a intenção | médio | baixo | Escrita atômica (D-15) |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Re-extração reversa executada e sem regressão vermelha (recomendado, não obrigatório)
- [ ] `mypy --strict` e `ruff` sem erros no projeto
- [ ] Cobertura ≥ 80% em `sintetica.intent`
- [ ] Os 14 cenários Gherkin do `requirements.md` cobertos por testes
- [ ] Teste de contrato com o `schema-builder` passando (D-16)
- [ ] Os 326 testes das features 001 a 003 continuam passando

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-12 | Versão inicial gerada por `/reversa-plan` | reversa |
