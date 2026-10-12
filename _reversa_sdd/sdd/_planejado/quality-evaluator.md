# Spec: quality-evaluator

> Selo 🟡 PLANEJADO em todos os itens. Fonte: `prd.md` (seções 3, 8 e 9), `personas.md`, `questions.md` (Q6, Q9, Q16, Q20, Q22).

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-10-09
**Reviewers:** Antigravity (revisor do pipeline)

---

## 1. Resumo

🟡 O `quality-evaluator` é a skill `sintetica-eval`. Ela mede conformidade com o schema (≥ 95%), unicidade estrutural e semântica (≥ 90%, Q16) e PII detectada (0, Q9). Ela emite o relatório final, fecha a medição de tempo (Q20) e dá o veredito `APROVADO` ou `REPROVADO`.

---

## 2. Contexto e Motivação

**Problema:**
🟡 Sem medição, o usuário não sabe se o dataset serve para fine-tuning, testes ou validação de pipelines.

**Evidências:**
🟡 As 3 métricas do PRD (seção 3) dependem deste componente. Passo 7 da jornada das 3 personas: "ler o relatório de qualidade e PII".

**Por que agora:**
🟡 É o último passo do pipeline e a prova das métricas de sucesso.

---

## 3. Goals (Objetivos)

- [ ] 🟡 G-01: Medir conformidade, unicidade e PII em 100% dos datasets gerados.
- [ ] 🟡 G-02: Avaliar 10.000 registros de 1 KB em ≤ 120 s.
- [ ] 🟡 G-03: Registrar a duração de `/sintetica-start` até o relatório e sinalizar lotes ≤ 100 acima de 10 min.

**Métricas de sucesso:**
| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| 🟡 Conformidade com schema | 🟡 não existe | 🟡 ≥ 95% | 🟡 3 meses |
| 🟡 Unicidade estrutural e semântica | 🟡 não existe | 🟡 ≥ 90% cada | 🟡 3 meses |
| 🟡 Vazamentos de PII detectados | 🟡 não existe | 🟡 0 | 🟡 3 meses |
| 🟡 Tempo de avaliação de 10.000 registros | 🟡 não existe | 🟡 ≤ 120 s | 🟡 MVP |

---

## 4. Non-Goals (Fora do Escopo)

- 🟡 NG-01: Não há avaliação por LLM-juiz nesta versão; as métricas são determinísticas e locais.
- 🟡 NG-02: Não há correção automática do dataset; o avaliador só mede e reporta.
- 🟡 NG-03: Não há comparação com dados reais ou testes estatísticos de fidelidade (PRD, não-objetivo 4).
- 🟡 NG-04: Não há painel web; o relatório é Markdown e JSON (PRD, não-objetivo 1).

---

## 5. Usuários e Personas

**Usuário primário:** 🟡 As 3 personas, que leem o relatório antes de usar o dataset.
**Usuário secundário:** 🟡 Automação de CI do usuário, que lê `report.json` e o código de saída.

**Jornada atual (sem a feature):**
1. 🟡 O usuário abre o arquivo e confere amostras à mão.
2. 🟡 Duplicados e PII passam sem aviso.

**Jornada futura (com a feature):**
1. 🟡 O `batch-generator` chama o avaliador ao terminar.
2. 🟡 O usuário lê o veredito e as 3 métricas.
3. 🟡 O usuário usa o dataset ou ajusta a intenção.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | 🟡 O sistema deve calcular conformidade como registros válidos por `Record` divididos pelo volume pedido em `intent.json`. | Must | 🟡 Com 96 válidos de 100 pedidos, a conformidade é 96,0%. |
| RF-02 | 🟡 O sistema deve calcular unicidade estrutural como hashes distintos do JSON canônico divididos pelo total de registros. | Must | 🟡 100 registros com 5 cópias exatas dão 95,0%. |
| RF-03 | 🟡 O sistema deve calcular unicidade semântica: normalizar texto (minúsculas, sem pontuação, espaços únicos), gerar shingles de 3 palavras e marcar como quase-duplicado o registro com similaridade de Jaccard ≥ 0,8 com outro já visto. | Must | 🟡 2 frases que diferem só em pontuação contam como quase-duplicadas. |
| RF-04 | 🟡 O sistema deve usar MinHash com LSH para a unicidade semântica quando o total passar de 1.000 registros. | Should | 🟡 10.000 registros são avaliados em ≤ 120 s. |
| RF-05 | 🟡 O sistema deve chamar `pii-guard.scan` em cada campo de texto e contar como vazamento só os achados fora da allowlist. | Must | 🟡 1 e-mail real inserido no dataset gera 1 vazamento; valores Faker da allowlist geram 0. |
| RF-06 | 🟡 O sistema deve gravar `finished_at` e calcular a duração a partir de `started_at` de `intent.json` (Q20). | Must | 🟡 `report.json` contém a duração em minutos com 1 casa decimal. |
| RF-07 | 🟡 O sistema deve sinalizar `meta_tempo: false` quando o volume for ≤ 100 e a duração for ≥ 10 min. | Must | 🟡 Lote de 50 registros com 12 min gera o sinal. |
| RF-08 | 🟡 O sistema deve dar veredito `APROVADO` só quando conformidade ≥ 95%, as 2 unicidades ≥ 90% e vazamentos = 0. | Must | 🟡 Qualquer métrica fora do alvo gera `REPROVADO` com a lista das métricas que falharam. |
| RF-09 | 🟡 O sistema deve gravar `datasets/<slug>/report.md` e `datasets/<slug>/report.json` com as métricas, o veredito, a duração e os índices dos registros problemáticos. | Must | 🟡 Os 2 arquivos existem e têm os mesmos números. |
| RF-10 | 🟡 O relatório deve incluir a seção "Escopo e limites da detecção de PII", com os tipos cobertos e os limites retornados por `pii-guard.coverage()` (Q9). | Must | 🟡 A seção lista os 7 tipos, os padrões custom e os limites conhecidos. |
| RF-11 | 🟡 O comando `uv run sintetica eval <slug>` deve terminar com código 0 em `APROVADO` e código 2 em `REPROVADO`. | Should | 🟡 Um pipeline de CI falha com dataset reprovado. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O `batch-generator` chama o `quality-evaluator` com o slug.
2. 🟡 O sistema carrega `output/dataset.<ext>`, `schema.py`, `intent.json` e `run.json`.
3. 🟡 O sistema calcula conformidade, unicidades e PII.
4. 🟡 O sistema grava `finished_at` e calcula a duração.
5. 🟡 O sistema grava `report.md` e `report.json`.
6. 🟡 Resultado: o sistema mostra o veredito, as métricas e o caminho absoluto do relatório.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Avaliação avulsa:**
1. 🟡 O usuário executa `/sintetica-eval <slug>` sobre um dataset existente.
2. 🟡 O sistema avalia sem alterar `started_at` e grava a duração como "não medida" se `intent.json` não tiver `started_at`.

**Fluxo Alternativo B — Lote incompleto:**
1. 🟡 `run.json` tem status `incompleto` ou `interrompido_custo`.
2. 🟡 O sistema avalia o que existe e cita o status no relatório.

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | 🟡 Runtime Python | 🟡 Python ≥ 3.10 com `uv` | 🟡 Q18 |
| RNF-02 | 🟡 Qualidade de código | 🟡 `mypy --strict` e `ruff` sem erros | 🟡 PRD, seção 6 |
| RNF-03 | 🟡 Cobertura de testes | 🟡 ≥ 80% com `pytest-cov` | 🟡 Q19 |
| RNF-04 | 🟡 Desempenho | 🟡 ≤ 120 s para 10.000 registros de 1 KB | 🟡 G-02 |
| RNF-05 | 🟡 Determinismo | 🟡 Mesmo dataset gera o mesmo `report.json`, exceto `finished_at` | 🟡 Semente fixa no MinHash |
| RNF-06 | 🟡 Rede | 🟡 0 chamadas | 🟡 Q15 |

---

## 8. Design e Interface

**Componentes afetados:** 🟡 Skill `sintetica-eval`; comando `uv run sintetica eval`; arquivos `report.md` e `report.json`.

**Comportamento esperado:**
🟡 O chat mostra um bloco curto com veredito, 4 números (conformidade, unicidade estrutural, unicidade semântica, vazamentos) e a duração. O detalhe fica em `report.md`.

**Estados da UI:**
- 🟡 Estado vazio: dataset com 0 registros gera `REPROVADO` com conformidade 0%.
- 🟡 Estado de carregamento: "Avaliando N registros".
- 🟡 Estado de erro: arquivo ausente ou ilegível, com o caminho e a causa.
- 🟡 Estado de sucesso: veredito e caminho do relatório.

---

## 9. Modelo de Dados

```
Report {
  slug: string
  verdict: "APROVADO" | "REPROVADO"
  failed_metrics: list<string>
  conformity_pct: decimal
  structural_uniqueness_pct: decimal
  semantic_uniqueness_pct: decimal
  pii_leaks: int
  pii_coverage: { types: list<string>, custom_patterns: int, limits: list<string> }
  duration_min: decimal | null
  time_target_met: boolean | null   // só para volume ≤ 100
  run_status: string
  problem_indices: { invalid: list<int>, duplicates: list<int>, pii: list<int> }
  finished_at: string
}
```

**Migrações necessárias:** 🟡 Não.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| 🟡 `pii-guard` | 🟡 Obrigatória | 🟡 O sistema não emite veredito e encerra com erro (fallback seguro). |
| 🟡 `schema-builder` (`schema.py`) | 🟡 Obrigatória | 🟡 Sem schema, a conformidade não é calculada e o sistema encerra com erro. |
| 🟡 Biblioteca MinHash (ex.: `datasketch`) | 🟡 Opcional | 🟡 Sem ela, o sistema usa comparação par a par até 1.000 registros e recusa acima disso. |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| 🟡 EC-01: Dataset ausente | 🟡 `output/dataset.<ext>` não existe | 🟡 Mensagem com o caminho e sugestão de `--resume` do gerador. |
| 🟡 EC-02: Linha corrompida | 🟡 JSON inválido ou CSV com colunas a mais | 🟡 A linha conta como inválida e seu índice entra em `problem_indices.invalid`. |
| 🟡 EC-03: Registro sem campo de texto | 🟡 Schema só numérico | 🟡 A unicidade semântica é marcada "não aplicável" e não entra no veredito. |
| 🟡 EC-04: Falha ao ler a allowlist | 🟡 Arquivo ausente | 🟡 Todo achado conta como vazamento e o relatório cita a causa. |
| 🟡 EC-05: Schema alterado após a geração | 🟡 `schema_version` de `run.json` diferente do atual | 🟡 O relatório avisa a divergência e avalia com o schema atual. |

---

## 12. Segurança e Privacidade

- 🟡 **Autenticação:** não se aplica.
- 🟡 **Autorização:** não se aplica.
- 🟡 **Dados sensíveis:** o relatório mostra índice, campo, tipo e prévia mascarada de cada achado, nunca o valor completo.
- 🟡 **Auditoria:** `report.json` é o registro permanente da avaliação.

---

## 13. Plano de Rollout

- 🟡 **Estratégia:** versão `0.1.0`; testes com datasets de referência que têm métricas conhecidas.
- 🟡 **Como reverter (rollback):** reinstalar a versão anterior e rodar `/sintetica-eval` de novo; o dataset não é alterado.
- 🟡 **Monitoramento pós-deploy:** comparar vereditos com revisão manual em issues.

---

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---------|---------|------|-------|
| OQ-01 | 🟡 O limiar de Jaccard 0,8 em shingles de 3 palavras (RF-03) é a definição aceita de unicidade semântica da Q16? | 🟡 Alto | 🟡 Antigravity | 🟡 Antes do `/reversa-plan` |
| OQ-02 | 🟡 A premissa 1 do PRD cita "verificação semântica". As métricas determinísticas bastam, ou um LLM-juiz opcional é necessário? | 🟡 Médio | 🟡 Antigravity | 🟡 Antes do `/reversa-plan` |

---

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---------|--------------------------|---------|
| 🟡 Unicidade semântica por Jaccard e MinHash | 🟡 Embeddings | 🟡 Local, determinístico e sem modelo extra (Q15). |
| 🟡 Conformidade sobre o volume pedido | 🟡 Sobre os registros gerados | 🟡 Mede o que o usuário pediu; registros descartados contam contra a meta. |
| 🟡 Código de saída 2 em reprovação | 🟡 Código 1 | 🟡 Separa "reprovado" de "erro de execução" (código 1). |

---

## Apêndice

### Referências
- 🟡 `../prd.md`, seções 3, 8 e 9.
- 🟡 `../questions.md`, Q9, Q16, Q20.

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
