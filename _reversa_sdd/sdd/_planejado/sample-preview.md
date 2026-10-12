# Spec: sample-preview

> Selo 🟡 PLANEJADO em todos os itens. Fonte: `prd.md` (seções 4, 8 e 9), `personas.md`, `questions.md` (Q6, Q8, Q21, Q22).

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-10-09
**Reviewers:** Antigravity (revisor do pipeline)

---

## 1. Resumo

🟡 O `sample-preview` é a skill `sintetica-sample`. Ela gera de 3 a 5 registros válidos pelo schema aprovado e os mostra para aprovação visual. A amostra aprovada vira semente (`seeds/`) para o `batch-generator`. É a mitigação principal da premissa 1 do PRD (qualidade da geração via LLM).

---

## 2. Contexto e Motivação

**Problema:**
🟡 Gerar um lote completo sem ver exemplos gasta tempo e tokens em dados que o usuário pode rejeitar.

**Evidências:**
🟡 Q6, mitigação 1: "geração iterativa com amostragem inicial (3 a 5 registros)". Passo 5 da jornada das 3 personas.

**Por que agora:**
🟡 O `batch-generator` usa a amostra aprovada como exemplos de referência.

---

## 3. Goals (Objetivos)

- [ ] 🟡 G-01: Mostrar de 3 a 5 registros 100% válidos pelo schema.
- [ ] 🟡 G-02: Gerar a amostra sem chave de API, pelo `HarnessAgentProvider` (Q8).
- [ ] 🟡 G-03: Mostrar a amostra em ≤ 60 s após a aprovação do schema.

**Métricas de sucesso:**
| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| 🟡 Registros válidos na amostra mostrada | 🟡 não existe | 🟡 100% | 🟡 MVP |
| 🟡 Tempo até mostrar a amostra | 🟡 não existe | 🟡 ≤ 60 s | 🟡 MVP |
| 🟡 Amostras aprovadas em ≤ 3 rodadas | 🟡 não existe | 🟡 ≥ 80% | 🟡 3 meses |

---

## 4. Non-Goals (Fora do Escopo)

- 🟡 NG-01: A amostra não mede diversidade estatística; isso é papel do `quality-evaluator`.
- 🟡 NG-02: A amostra não tem mais de 5 registros. Volumes maiores usam o `batch-generator`.
- 🟡 NG-03: O usuário não edita registros da amostra à mão nesta versão; ele pede ajustes em linguagem natural.
- 🟡 NG-04: A amostra não altera o schema. Mudanças de schema voltam ao `schema-builder`.

---

## 5. Usuários e Personas

**Usuário primário:** 🟡 As 3 personas, no passo 5 da jornada (aprovar 3 a 5 registros, conversas ou linhas).
**Usuário secundário:** 🟡 O `batch-generator`, que lê `seeds/`.

**Jornada atual (sem a feature):**
1. 🟡 O usuário gera o lote inteiro e só depois descobre que o estilo não serve.
2. 🟡 O usuário apaga o lote e recomeça.

**Jornada futura (com a feature):**
1. 🟡 O sistema mostra 3 a 5 exemplos.
2. 🟡 O usuário aprova ou pede ajustes.
3. 🟡 O sistema grava a amostra como semente e segue para o lote.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | 🟡 O sistema deve gerar N registros, com N entre 3 e 5 e padrão 3. | Must | 🟡 Sem argumento, a amostra tem 3 registros; com `--n 5`, tem 5; com `--n 6`, o sistema recusa. |
| RF-02 | 🟡 O sistema deve usar o `HarnessAgentProvider` como padrão para a amostra. | Must | 🟡 Sem chave de API configurada, a amostra é gerada. |
| RF-03 | 🟡 O sistema deve validar cada registro com `Record` do `schema.py` e gerar de novo os inválidos, até 3 tentativas por registro. | Must | 🟡 A amostra mostrada nunca contém registro inválido. |
| RF-04 | 🟡 O sistema deve passar a amostra pelo `pii-guard` e mascarar PII detectada antes de mostrar. | Must | 🟡 Um registro com CPF não gerado por Faker aparece com o valor substituído. |
| RF-05 | 🟡 O sistema deve mostrar a amostra como tabela (CSV) ou JSON formatado (JSON e JSONL). | Must | 🟡 Formato CSV mostra tabela Markdown; formato JSONL mostra 1 bloco JSON por registro. |
| RF-06 | 🟡 O usuário deve poder responder `aprovar`, `ajustar <pedido>` ou `voltar ao schema`. | Must | 🟡 Cada resposta leva ao fluxo da seção 6.2 ou 6.3. |
| RF-07 | 🟡 O sistema deve gravar a amostra aprovada em `datasets/<slug>/seeds/sample.<ext>` com o `schema_version`. | Must | 🟡 O arquivo existe e o `schema_version` gravado é igual ao do schema atual. |
| RF-08 | 🟡 Após 3 rodadas de ajuste sem aprovação, o sistema deve sugerir voltar ao schema. | Should | 🟡 Na 4ª rodada, a sugestão aparece. |
| RF-09 | 🟡 No modo Expresso, o sistema deve aprovar a amostra sem confirmação quando 100% dos registros forem válidos. | Must | 🟡 No Expresso, o `batch-generator` inicia sem pergunta. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O `schema-builder` chama o `sample-preview` após a aprovação do schema.
2. 🟡 O sistema pede ao `HarnessAgentProvider` 3 registros.
3. 🟡 O sistema valida, passa pelo `pii-guard` e mostra a amostra.
4. 🟡 O usuário responde `aprovar`.
5. 🟡 O sistema grava `seeds/sample.<ext>`.
6. 🟡 Resultado: o sistema chama o `batch-generator`.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Ajuste:**
1. 🟡 O usuário responde `ajustar nomes mais variados`.
2. 🟡 O sistema gera nova amostra com o pedido como instrução extra e mostra de novo.

**Fluxo Alternativo B — Voltar ao schema:**
1. 🟡 O usuário responde `voltar ao schema`.
2. 🟡 O sistema chama o `schema-builder` com o schema atual aberto para ajuste.

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | 🟡 Runtime Python | 🟡 Python ≥ 3.10 com `uv` | 🟡 Q18 |
| RNF-02 | 🟡 Qualidade de código | 🟡 `mypy --strict` e `ruff` sem erros | 🟡 PRD, seção 6 |
| RNF-03 | 🟡 Cobertura de testes | 🟡 ≥ 80% com `pytest-cov` | 🟡 Q19 |
| RNF-04 | 🟡 Desempenho | 🟡 ≤ 60 s até mostrar a amostra | 🟡 G-03 |
| RNF-05 | 🟡 Custo | 🟡 US$ 0 no padrão (`HarnessAgentProvider`) | 🟡 Q8 |

---

## 8. Design e Interface

**Componentes afetados:** 🟡 Skill `sintetica-sample`; comando `uv run sintetica validate`; arquivo `seeds/sample.<ext>`.

**Comportamento esperado:**
🟡 O agente do harness gera os registros no chat e os envia por stdin ao comando de validação. O sistema mostra apenas os registros válidos e mascarados.

**Estados da UI:**
- 🟡 Estado vazio: não se aplica.
- 🟡 Estado de carregamento: o sistema informa "Gerando amostra de N registros".
- 🟡 Estado de erro: o sistema mostra quantos registros falharam e o motivo do primeiro erro.
- 🟡 Estado de sucesso: amostra com as 3 opções do RF-06.

---

## 9. Modelo de Dados

```
SampleFile {
  schema_version: string        // hash do schema.json aprovado
  approved_at: string           // ISO 8601
  provider: "harness" | "ollama" | "external"
  records: list<Record>         // 3 a 5 registros válidos
}
```

**Migrações necessárias:** 🟡 Não.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| 🟡 `llm-provider` (`HarnessAgentProvider`) | 🟡 Obrigatória | 🟡 Sem harness, o sistema tenta o próximo provedor da `provider_priority`. |
| 🟡 `schema-builder` (`schema.py`) | 🟡 Obrigatória | 🟡 Sem schema aprovado, a skill encerra e indica `/sintetica-schema`. |
| 🟡 `pii-guard` | 🟡 Obrigatória | 🟡 A amostra não é mostrada; o sistema encerra com erro. |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| 🟡 EC-01: Registro inválido após 3 tentativas | 🟡 Schema difícil para o LLM | 🟡 O sistema mostra os válidos, informa a falha e sugere `voltar ao schema`. |
| 🟡 EC-02: Saída não-JSON do agente | 🟡 O agente responde com texto livre | 🟡 O sistema descarta a resposta e conta como tentativa falha. |
| 🟡 EC-03: Amostra com registros idênticos | 🟡 2 ou mais registros iguais | 🟡 O sistema gera de novo os duplicados antes de mostrar. |
| 🟡 EC-04: Schema alterado após aprovação | 🟡 `schema_version` diferente de `seeds/sample.<ext>` | 🟡 O sistema invalida a amostra e gera uma nova. |
| 🟡 EC-05: Falha do provedor | 🟡 Timeout ou provedor indisponível | 🟡 O sistema usa o fallback da `provider_priority` e informa qual provedor usou. |

---

## 12. Segurança e Privacidade

- 🟡 **Autenticação:** não se aplica.
- 🟡 **Autorização:** não se aplica.
- 🟡 **Dados sensíveis:** a amostra passa pelo `pii-guard` antes de aparecer e antes de ser gravada.
- 🟡 **Auditoria:** `sample.<ext>` registra provedor e `schema_version`.

---

## 13. Plano de Rollout

- 🟡 **Estratégia:** versão `0.1.0`, junto com o `schema-builder`.
- 🟡 **Como reverter (rollback):** apagar `seeds/sample.<ext>` e rodar `/sintetica-sample` de novo.
- 🟡 **Monitoramento pós-deploy:** issues no repositório.

---

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---------|---------|------|-------|
| OQ-01 | 🟡 O padrão de 3 registros (RF-01) é melhor que 5 para mostrar variedade? | 🟡 Baixo | 🟡 Antigravity | 🟡 Antes do `/reversa-plan` |
| OQ-02 | 🟡 O `HarnessAgentProvider` envia os registros por stdin. Todos os 5 harnesses permitem que o agente execute esse comando? | 🟡 Médio | 🟡 Antigravity | 🟡 Antes do `/reversa-plan` |

---

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---------|--------------------------|---------|
| 🟡 Amostra aprovada vira semente em `seeds/` | 🟡 Descartar a amostra | 🟡 Exemplos aprovados orientam o estilo do lote. |
| 🟡 `HarnessAgentProvider` como padrão | 🟡 API externa | 🟡 Q8 e Q21: custo zero e sem envio externo. |

---

## Apêndice

### Referências
- 🟡 `../prd.md`, seções 4, 8 e 9.
- 🟡 `../questions.md`, Q6, Q8, Q21.

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
