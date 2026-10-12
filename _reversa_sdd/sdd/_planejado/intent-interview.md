# Spec: intent-interview

> Selo 🟡 PLANEJADO em todos os itens. Fonte: `prd.md` (seções 3, 4 e 9), `personas.md`, `questions.md` (Q10, Q13, Q20, Q21, Q22).

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-10-09
**Reviewers:** Antigravity (revisor do pipeline)

---

## 1. Resumo

🟡 O `intent-interview` é a skill `sintetica-start`. Ela cria a pasta do dataset antes da primeira pergunta e conduz uma entrevista sem jargão sobre objetivo, formato e volume. A saída é o arquivo `intent.json`, que alimenta o `schema-builder`. A skill também orquestra as etapas seguintes do pipeline nos modos Guiado e Expresso.

---

## 2. Contexto e Motivação

**Problema:**
🟡 Ferramentas como Faker, SDV e distilabel exigem código ou parâmetros de baixo nível. As 3 personas querem descrever o dataset em linguagem natural, dentro do harness que já usam.

**Evidências:**
🟡 PRD, seção 1: nenhuma alternativa roda como skill conversacional com entrevista guiada e tolerância a incertezas. Jornada de 7 passos aprovada na Q13 começa por esta skill.

**Por que agora:**
🟡 A entrevista é o ponto de entrada de todas as jornadas. Sem ela, nenhuma outra skill tem insumo.

---

## 3. Goals (Objetivos)

- [ ] 🟡 G-01: Criar `datasets/<slug>/seeds/` e mostrar o caminho absoluto antes da primeira pergunta, em 100% das execuções.
- [ ] 🟡 G-02: Concluir a entrevista do modo Expresso com no máximo 6 perguntas.
- [ ] 🟡 G-03: Aceitar "não sei" em qualquer pergunta sem interromper o fluxo.
- [ ] 🟡 G-04: Registrar o início da medição de tempo (Q20) no disparo do comando.

**Métricas de sucesso:**
| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| 🟡 Pasta criada antes da 1ª pergunta | 🟡 não existe | 🟡 100% das execuções | 🟡 MVP |
| 🟡 Perguntas no modo Expresso | 🟡 não existe | 🟡 ≤ 6 | 🟡 MVP |
| 🟡 Tempo da ideia ao dataset, lote ≤ 100 registros | 🟡 não existe | 🟡 < 10 min (medido de `/sintetica-start` ao relatório) | 🟡 3 meses |

---

## 4. Non-Goals (Fora do Escopo)

- 🟡 NG-01: A entrevista não pede parâmetros de baixo nível (temperatura, modelo, tamanho de chunk). Esses valores têm padrão nas outras specs.
- 🟡 NG-02: A entrevista não importa dados reais do usuário como base de geração (PRD, não-objetivo 4).
- 🟡 NG-03: A entrevista não gera schema nem registros. Ela só coleta e persiste a intenção.
- 🟡 NG-04: Não há retomada de entrevista interrompida nesta versão. O usuário inicia uma nova execução.

---

## 5. Usuários e Personas

**Usuário primário:** 🟡 As 3 personas do PRD. O `dev-de-testes` descreve entidades; o `engenheiro-de-ml` descreve tarefa e rótulos; o `analista-de-dados` descreve colunas e regras de negócio.
**Usuário secundário:** 🟡 O agente do harness, que executa a skill e chama o runtime Python.

**Jornada atual (sem a feature):**
1. 🟡 O usuário escreve um script com Faker ou um prompt avulso para um LLM.
2. 🟡 O usuário define campos, tipos e volume no código.
3. 🟡 O usuário não tem registro da intenção original.

**Jornada futura (com a feature):**
1. 🟡 O usuário executa `/sintetica-start` e vê o caminho absoluto da pasta do dataset.
2. 🟡 O usuário responde perguntas em linguagem natural.
3. 🟡 O sistema grava `intent.json` e segue para o `schema-builder`.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | 🟡 O sistema deve criar `datasets/<slug>/seeds/` antes de fazer a primeira pergunta e mostrar o caminho absoluto. | Must | 🟡 Na primeira mensagem da skill, o caminho absoluto aparece e a pasta já existe no disco. |
| RF-02 | 🟡 O sistema deve usar como slug o nome passado em `/sintetica-start <nome>`, normalizado em kebab-case ASCII. Sem nome, o sistema deve usar `dataset-<AAAAMMDD-HHMMSS>`. | Must | 🟡 `/sintetica-start Pedidos de Café` cria `datasets/pedidos-de-cafe/seeds/`. |
| RF-03 | 🟡 O sistema deve gravar `started_at` (ISO 8601, UTC) em `datasets/<slug>/intent.json` no disparo do comando (Q20). | Must | 🟡 `started_at` é anterior ao horário da primeira pergunta. |
| RF-04 | 🟡 O sistema deve aceitar o modo como argumento (`guiado` ou `expresso`). Sem argumento, o sistema deve usar o modo Guiado. | Must | 🟡 `/sintetica-start x expresso` grava `mode: "expresso"`. |
| RF-05 | 🟡 O sistema deve coletar 5 itens: objetivo, estrutura (entidades, campos, colunas ou rótulos), regras de negócio, formato (CSV, JSON ou JSONL) e volume (1 a 10.000). | Must | 🟡 `intent.json` contém as 5 chaves após a entrevista. |
| RF-06 | 🟡 O sistema deve gravar o selo 🟡 INDEFINIDO no item respondido com "não sei" e continuar a entrevista. | Must | 🟡 Resposta "não sei" para regras grava `rules: {"status": "indefinido"}` e a próxima pergunta aparece. |
| RF-07 | 🟡 O sistema deve aplicar padrões a formato e volume indefinidos: formato JSONL e volume 10. | Must | 🟡 Com "não sei" nos dois itens, `intent.json` grava `format: "jsonl"` e `volume: 10`, marcados como padrão. |
| RF-08 | 🟡 O sistema deve passar cada resposta pelo `pii-guard` antes de gravar. Se houver PII, o sistema deve avisar o usuário e gravar a versão mascarada (Q21). | Must | 🟡 Resposta com o e-mail `ana@empresa.com` é gravada com um e-mail Faker e o aviso aparece. |
| RF-09 | 🟡 No modo Guiado, o sistema deve mostrar um resumo da intenção e pedir confirmação antes de chamar o `schema-builder`. | Must | 🟡 O `schema-builder` só roda após resposta `sim`. |
| RF-10 | 🟡 No modo Expresso, o sistema deve fazer as perguntas em uma única mensagem e encadear schema, amostra, geração e avaliação sem novas confirmações, exceto a autorização de custo acima do teto (Q17). | Must | 🟡 Do envio das respostas ao relatório, a única pausa possível é a de custo. |
| RF-11 | 🟡 O sistema deve recusar volume fora de 1 a 10.000 e pedir um novo valor, com no máximo 2 novas tentativas antes de aplicar o padrão 10. | Should | 🟡 Volume 50.000 gera nova pergunta; após 2 recusas, grava 10. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O usuário executa `/sintetica-start pedidos guiado`.
2. 🟡 O sistema cria `datasets/pedidos/seeds/`, grava `started_at` e mostra o caminho absoluto.
3. 🟡 O sistema pergunta objetivo, estrutura, regras, formato e volume, uma pergunta por vez.
4. 🟡 O usuário responde em linguagem natural.
5. 🟡 O sistema passa as respostas pelo `pii-guard` e grava `intent.json`.
6. 🟡 O sistema mostra o resumo e o usuário confirma.
7. 🟡 Resultado: o sistema chama o `schema-builder` com o caminho de `intent.json`.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Modo Expresso:**
1. 🟡 O sistema envia as 5 perguntas em uma única mensagem.
2. 🟡 O usuário responde de uma vez; o sistema extrai os 5 itens e grava `intent.json`.
3. 🟡 O sistema encadeia as etapas seguintes sem confirmação (RF-10).

**Fluxo Alternativo B — Resposta ambígua:**
1. 🟡 O sistema não consegue extrair um item da resposta.
2. 🟡 O sistema faz 1 pergunta de esclarecimento; sem resposta útil, grava o selo INDEFINIDO.

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | 🟡 Runtime Python | 🟡 Python ≥ 3.10 com `uv` | 🟡 Q18 |
| RNF-02 | 🟡 Qualidade de código | 🟡 `mypy --strict` e `ruff` sem erros | 🟡 PRD, seção 6 |
| RNF-03 | 🟡 Cobertura de testes | 🟡 ≥ 80% com `pytest-cov` | 🟡 Q19 |
| RNF-04 | 🟡 Privacidade | 🟡 Respostas gravadas somente após o `pii-guard` | 🟡 Q21 |
| RNF-05 | 🟡 Linguagem | 🟡 Perguntas sem termos técnicos de ML ou estatística | 🟡 PRD, seção 4 |

---

## 8. Design e Interface

**Componentes afetados:** 🟡 Skill `sintetica-start` em `.agents/skills/` e `.claude/skills/`; comando Python `uv run sintetica intent`.

**Comportamento esperado:**
🟡 A conversa acontece no chat do harness. A primeira mensagem sempre traz o caminho absoluto. Cada pergunta traz 1 exemplo de resposta para a persona provável.

**Estados da UI:**
- 🟡 Estado vazio: antes da primeira resposta, a mensagem mostra o caminho e a primeira pergunta.
- 🟡 Estado de carregamento: não se aplica; a entrevista não chama LLM externo.
- 🟡 Estado de erro: falha de escrita mostra o caminho e a causa, e encerra a skill.
- 🟡 Estado de sucesso: o resumo da intenção aparece com os itens marcados como padrão ou INDEFINIDO.

---

## 9. Modelo de Dados

```
Intent {
  slug: string
  mode: "guiado" | "expresso"
  started_at: string                // ISO 8601 UTC (Q20)
  objective: Item
  structure: Item
  rules: Item
  format: "csv" | "json" | "jsonl"
  format_source: "usuario" | "padrao"
  volume: int                       // 1 a 10.000
  volume_source: "usuario" | "padrao"
  pii_masked: boolean               // true se o pii-guard alterou alguma resposta
}

Item {
  status: "definido" | "indefinido"
  text: string | null               // resposta já mascarada
}
```

**Migrações necessárias:** 🟡 Não.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| 🟡 `pii-guard` | 🟡 Obrigatória | 🟡 A entrevista não grava respostas e encerra com erro (privacidade por design). |
| 🟡 `schema-builder` | 🟡 Obrigatória | 🟡 `intent.json` fica salvo; o usuário pode chamar `/sintetica-schema` depois. |
| 🟡 Runtime Python (`uv`) | 🟡 Obrigatória | 🟡 Com `runtime_ready: false`, a skill mostra o comando de instalação e encerra. |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| 🟡 EC-01: Slug já existe | 🟡 `datasets/pedidos/` já existe | 🟡 O sistema cria `pedidos-2`, `pedidos-3`, e assim por diante, e mostra o caminho final. |
| 🟡 EC-02: Falha de escrita | 🟡 Sem permissão ou disco cheio | 🟡 O sistema mostra o caminho e a causa e encerra sem perguntar nada. |
| 🟡 EC-03: Tudo indefinido | 🟡 "Não sei" em todos os 5 itens | 🟡 O sistema aplica os padrões do RF-07, avisa que o schema será genérico e pede confirmação mesmo no modo Expresso. |
| 🟡 EC-04: Formato não suportado | 🟡 Usuário pede Parquet ou XLSX | 🟡 O sistema informa os 3 formatos suportados e pergunta de novo. |
| 🟡 EC-05: Falha do `pii-guard` | 🟡 Exceção ao carregar `policy.json` | 🟡 O sistema não grava a resposta, mostra o erro e encerra (fallback seguro). |
| 🟡 EC-06: PII na resposta | 🟡 CPF real digitado na descrição | 🟡 O sistema grava a versão mascarada e avisa (RF-08). |

---

## 12. Segurança e Privacidade

- 🟡 **Autenticação:** não se aplica. Execução local.
- 🟡 **Autorização:** não se aplica.
- 🟡 **Dados sensíveis:** as respostas passam pelo `pii-guard` antes de qualquer gravação ou envio (Q21).
- 🟡 **Auditoria:** `intent.json` registra se houve mascaramento (`pii_masked`), sem o valor original.

---

## 13. Plano de Rollout

- 🟡 **Estratégia:** entregue junto com o `cli-installer`, na versão `0.1.0`.
- 🟡 **Como reverter (rollback):** reinstalar a versão anterior do pacote; os arquivos `intent.json` existentes continuam válidos.
- 🟡 **Monitoramento pós-deploy:** issues no repositório; sem telemetria.

---

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---------|---------|------|-------|
| OQ-01 | 🟡 Os padrões de formato JSONL e volume 10 (RF-07) estão adequados? | 🟡 Médio | 🟡 Antigravity | 🟡 Antes do `/reversa-plan` |
| OQ-02 | 🟡 No caso EC-03, a confirmação no modo Expresso viola o critério "sem novas confirmações" do PRD? | 🟡 Baixo | 🟡 Antigravity | 🟡 Antes do `/reversa-plan` |

---

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---------|--------------------------|---------|
| 🟡 Slug por argumento ou timestamp | 🟡 Perguntar o nome antes de criar a pasta | 🟡 A pasta precisa existir antes da primeira pergunta (princípio do `mira-animator`). |
| 🟡 Mascarar respostas antes de gravar | 🟡 Mascarar só no envio à API | 🟡 Q21 e privacidade por design: nada com PII fica no disco. |
| 🟡 Modo Guiado como padrão | 🟡 Expresso como padrão | 🟡 Guiado expõe cada decisão ao usuário novo. |

---

## Apêndice

### Referências
- 🟡 `../prd.md`, seções 3, 4 e 9.
- 🟡 `../personas.md`, jornadas das 3 personas.
- 🟡 `../questions.md`, Q10, Q13, Q20, Q21.

### Histórico de Revisões
| Versão | Data | Autor | Mudanças |
|--------|------|-------|---------|
| 1.0 | 2026-10-09 | reversa-spec-sdd | 🟡 Criação inicial |

---

## Relatório de avaliação (spec_scorer.py)

**Score total:** 100.0/100
**Iterações:** 1
**Data:** 2026-10-09

| Dimensão | Score | Contribuição |
|---|---|---|
| Completude | 100% | 30.0 |
| Testabilidade | 100% | 25.0 |
| Clareza | 100% | 20.0 |
| Escopo | 100% | 15.0 |
| Edge Cases | 100% | 10.0 |

**Gaps críticos:**
- Nenhum.

**Sugestões:**
- Nenhuma do scorer. Resolver as Open Questions da seção 14 antes do `/reversa-plan`.
