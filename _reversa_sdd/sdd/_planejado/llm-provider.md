# Spec: llm-provider

> Selo 🟡 PLANEJADO em todos os itens. Fonte: `prd.md` (seções 4, 6, 7 e 8), `questions.md` (Q8, Q15, Q17, Q21, Q22).

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-10-09
**Reviewers:** Antigravity (revisor do pipeline)

---

## 1. Resumo

🟡 O `llm-provider` é a porta `LLMProvider` (Clean Architecture) e seus 2 adaptadores. O `ExternalAPIProvider` atende OpenAI, Anthropic, Gemini e Ollama local. O `HarnessAgentProvider` usa o próprio agente do harness. O componente também estima o custo e exige autorização acima de US$ 5,00 (Q17).

---

## 2. Contexto e Motivação

**Problema:**
🟡 A amostra e o lote têm necessidades diferentes. A amostra pede custo zero e nenhuma chave. O lote de 1.000 a 10.000 registros pede alta vazão em Python assíncrono.

**Evidências:**
🟡 Q8 define a porta e os 2 adaptadores. Q17 define o teto de custo. Q21 exige mascaramento antes de qualquer envio ao `ExternalAPIProvider`.

**Por que agora:**
🟡 `sample-preview` e `batch-generator` dependem desta porta.

---

## 3. Goals (Objetivos)

- [ ] 🟡 G-01: Oferecer 1 interface única para os 4 backends externos e o harness.
- [ ] 🟡 G-02: Garantir que 0 chamadas ao `ExternalAPIProvider` ocorram sem passar pelo `pii-guard` (Q21).
- [ ] 🟡 G-03: Pedir autorização em 100% dos lotes com custo estimado > US$ 5,00 (Q17).
- [ ] 🟡 G-04: Manter o erro da estimativa de custo em ≤ 25% do custo real.

**Métricas de sucesso:**
| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| 🟡 Chamadas externas sem mascaramento | 🟡 não existe | 🟡 0 | 🟡 MVP |
| 🟡 Lotes > US$ 5,00 sem autorização | 🟡 não existe | 🟡 0 | 🟡 MVP |
| 🟡 Erro da estimativa de custo | 🟡 não existe | 🟡 ≤ 25% | 🟡 3 meses |

---

## 4. Non-Goals (Fora do Escopo)

- 🟡 NG-01: Não há escolha automática do modelo mais barato. O usuário define o modelo por variável de ambiente ou usa o padrão.
- 🟡 NG-02: Não há proxy ou serviço hospedado do sintetica entre o usuário e a API (PRD, não-objetivo 5).
- 🟡 NG-03: Não há cache de respostas entre execuções nesta versão.
- 🟡 NG-04: Não há cobrança nem controle de saldo da conta do usuário na API; só a estimativa e o teto local.

---

## 5. Usuários e Personas

**Usuário primário:** 🟡 `engenheiro-de-ml`, que gera lotes de produção pelo `ExternalAPIProvider`.
**Usuário secundário:** 🟡 `dev-de-testes` e `analista-de-dados`, que usam o `HarnessAgentProvider` ou o Ollama em lotes de teste.

**Jornada atual (sem a feature):**
1. 🟡 O usuário escreve um cliente para cada API.
2. 🟡 O usuário descobre o custo só na fatura.

**Jornada futura (com a feature):**
1. 🟡 O sistema escolhe o provedor pela `provider_priority` de `policy.json`.
2. 🟡 O sistema mostra o custo estimado e pede autorização se passar do teto.
3. 🟡 O sistema gera os registros com mascaramento e controle de taxa.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | 🟡 O sistema deve expor a porta `LLMProvider` com `generate(request)` assíncrono, `estimate_cost(n_records, avg_tokens)`, `name` e `is_local`. | Must | 🟡 Os 2 adaptadores passam no mesmo conjunto de testes de contrato. |
| RF-02 | 🟡 O `ExternalAPIProvider` deve suportar os backends `openai`, `anthropic`, `gemini` e `ollama`, lendo as chaves de `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` e `GEMINI_API_KEY`, e o endereço de `OLLAMA_HOST` (padrão `http://localhost:11434`). | Must | 🟡 Com cada variável definida, o backend correspondente responde ao teste de fumaça. |
| RF-03 | 🟡 O sistema deve escolher o provedor pela ordem de `provider_priority` em `policy.json`, pulando os indisponíveis. | Must | 🟡 Com prioridade `harness, ollama, external` e Ollama desligado, lote > 100 registros usa `external`. |
| RF-04 | 🟡 O `HarnessAgentProvider` deve atender apenas pedidos de até 100 registros. | Must | 🟡 Pedido de 101 registros ao harness retorna erro `HarnessLimitExceeded`. |
| RF-05 | 🟡 O sistema deve passar todo o conteúdo do pedido pelo `pii-guard` (mascaramento) antes de enviar ao `ExternalAPIProvider`, quando `pii_premask` for `true` (Q21). | Must | 🟡 Um teste com e-mail real no prompt confirma que o payload enviado contém só o valor Faker. |
| RF-06 | 🟡 O sistema deve estimar o custo como `n_records × avg_tokens × preço por token`, com preços em `.sintetica/pricing.json`. Harness e Ollama custam US$ 0. | Must | 🟡 Para 1.000 registros, 500 tokens e US$ 0,00001 por token, a estimativa é US$ 5,00. |
| RF-07 | 🟡 O sistema deve pedir autorização explícita (`sim`) quando o custo estimado for maior que `cost_ceiling_usd` (padrão 5.00). | Must | 🟡 Estimativa de US$ 5,01 gera a pergunta; resposta diferente de `sim` cancela o lote. |
| RF-08 | 🟡 O sistema deve interromper a geração quando o custo acumulado atingir o valor autorizado e manter os registros já gerados. | Must | 🟡 Com teto atingido, o status do lote é `interrompido_custo` e os registros parciais permanecem. |
| RF-09 | 🟡 O sistema deve repetir pedidos com erro 429, 5xx ou timeout de 60 s, com espera exponencial (1 s, 2 s, 4 s) e no máximo 3 tentativas. | Must | 🟡 Um servidor simulado com 2 erros 503 seguidos de sucesso gera 3 chamadas e 1 resultado. |
| RF-10 | 🟡 O sistema não deve repetir pedidos com erro 401 ou 403; ele deve encerrar o lote com mensagem que cita a variável de ambiente da chave. | Must | 🟡 Chave inválida gera 1 chamada e a mensagem com o nome da variável. |
| RF-11 | 🟡 O sistema deve limitar a concorrência por provedor a 8 pedidos simultâneos por padrão, ajustável por `--concurrency`. | Should | 🟡 Com 100 pedidos, nunca há mais de 8 em voo. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O `batch-generator` pede 1.000 registros.
2. 🟡 O sistema escolhe o provedor pela `provider_priority`.
3. 🟡 O sistema estima o custo e, acima de US$ 5,00, pede autorização.
4. 🟡 O usuário responde `sim`.
5. 🟡 O sistema mascara o pedido e envia ao backend, com controle de concorrência.
6. 🟡 Resultado: o sistema devolve os registros e o custo real acumulado.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Lote de teste com harness:**
1. 🟡 Pedido de ≤ 100 registros com harness disponível.
2. 🟡 O sistema usa o `HarnessAgentProvider`, com custo US$ 0 e sem autorização.

**Fluxo Alternativo B — Ollama local:**
1. 🟡 `OLLAMA_HOST` responde.
2. 🟡 O sistema usa o backend `ollama`, com custo US$ 0.

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | 🟡 Runtime Python | 🟡 Python ≥ 3.10 com `uv` e `asyncio` | 🟡 Q18 |
| RNF-02 | 🟡 Qualidade de código | 🟡 `mypy --strict` e `ruff` sem erros | 🟡 PRD, seção 6 |
| RNF-03 | 🟡 Cobertura de testes | 🟡 ≥ 80% com `pytest-cov` | 🟡 Q19 |
| RNF-04 | 🟡 Segurança de chaves | 🟡 0 chaves em logs, arquivos ou relatórios | 🟡 Leitura só de variável de ambiente |
| RNF-05 | 🟡 Timeout por pedido | 🟡 60 s | 🟡 RF-09 |

---

## 8. Design e Interface

**Componentes afetados:** 🟡 Módulo Python `sintetica.providers`; arquivos `.sintetica/policy.json` e `.sintetica/pricing.json`.

**Comportamento esperado:**
🟡 O usuário só vê o provedor escolhido, a estimativa de custo e, se necessário, a pergunta de autorização.

**Estados da UI:**
- 🟡 Estado vazio: nenhum provedor disponível. O sistema lista as variáveis e o Ollama verificados.
- 🟡 Estado de carregamento: progresso informado pelo `batch-generator`.
- 🟡 Estado de erro: mensagem com o backend, o código HTTP e a ação corretiva.
- 🟡 Estado de sucesso: provedor usado e custo real acumulado.

---

## 9. Modelo de Dados

```
GenerationRequest {
  schema_json: dict             // JSON Schema de Record
  seeds: list<dict>             // amostra aprovada
  instructions: string          // intenção já mascarada
  n_records: int
}

GenerationResult {
  records: list<dict>           // ainda não validados
  input_tokens: int
  output_tokens: int
  cost_usd: decimal
}

CostEstimate {
  provider: string
  n_records: int
  avg_tokens: int               // medido na amostra
  usd: decimal
  requires_authorization: boolean
}
```

**Migrações necessárias:** 🟡 Não.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| 🟡 APIs OpenAI, Anthropic e Gemini | 🟡 Opcional | 🟡 O sistema pula para o próximo provedor; sem nenhum, encerra com a lista do estado vazio. |
| 🟡 Ollama local | 🟡 Opcional | 🟡 Mesmo fallback acima. |
| 🟡 Agente do harness | 🟡 Opcional | 🟡 Mesmo fallback acima, só para lotes ≤ 100. |
| 🟡 `pii-guard` | 🟡 Obrigatória para externo | 🟡 Sem `pii-guard`, o `ExternalAPIProvider` recusa o pedido. |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| 🟡 EC-01: Limite de taxa | 🟡 HTTP 429 | 🟡 Retry com espera exponencial (RF-09); após 3 falhas, o lote para com status `falha_provedor`. |
| 🟡 EC-02: Timeout | 🟡 Resposta > 60 s | 🟡 Retry (RF-09). |
| 🟡 EC-03: Chave inválida | 🟡 HTTP 401 ou 403 | 🟡 Sem retry; mensagem cita a variável (RF-10). |
| 🟡 EC-04: Preço ausente | 🟡 Modelo fora de `pricing.json` | 🟡 O sistema trata a estimativa como acima do teto e pede autorização. |
| 🟡 EC-05: Teto atingido no meio | 🟡 Custo real maior que o estimado | 🟡 Interrupção com registros parciais (RF-08). |
| 🟡 EC-06: Resposta malformada | 🟡 JSON inválido | 🟡 Conta como falha do pedido e entra no retry. |

---

## 12. Segurança e Privacidade

- 🟡 **Autenticação:** chaves de API lidas apenas de variáveis de ambiente.
- 🟡 **Autorização:** a autorização de custo é registrada em `run.json` com valor e horário.
- 🟡 **Dados sensíveis:** mascaramento obrigatório antes do envio externo (Q21). Chaves nunca aparecem em logs.
- 🟡 **Auditoria:** `run.json` registra provedor, tokens e custo por lote.

---

## 13. Plano de Rollout

- 🟡 **Estratégia:** versão `0.1.0` com os 4 backends; cada backend tem teste de contrato.
- 🟡 **Como reverter (rollback):** remover um backend da `provider_priority` em `policy.json`.
- 🟡 **Monitoramento pós-deploy:** comparar custo estimado e real em `run.json` (G-04).

---

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---------|---------|------|-------|
| OQ-01 | 🟡 Quais modelos padrão usar em cada backend? | 🟡 Médio | 🟡 Antigravity | 🟡 Antes do `/reversa-plan` |
| OQ-02 | 🟡 Quem mantém `pricing.json` atualizado, e com que frequência? | 🟡 Médio | 🟡 Antigravity | 🟡 Antes do `/reversa-plan` |
| OQ-03 | 🟡 O mascaramento (RF-05) também deve valer para o Ollama, que é local? | 🟡 Baixo | 🟡 Antigravity | 🟡 Antes do `/reversa-plan` |

---

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---------|--------------------------|---------|
| 🟡 Ollama dentro do `ExternalAPIProvider` | 🟡 Adaptador próprio | 🟡 Q8 lista Ollama no `ExternalAPIProvider`. |
| 🟡 Harness limitado a 100 registros | 🟡 Sem limite | 🟡 Q8: harness para amostras e prototipagem; Q10: lote de teste ≤ 100. |
| 🟡 Preço ausente conta como acima do teto | 🟡 Assumir custo zero | 🟡 Falha segura para o orçamento (Q17). |

---

## Apêndice

### Referências
- 🟡 `../prd.md`, seções 4, 6, 7 e 8.
- 🟡 `../questions.md`, Q8, Q17, Q21.

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
