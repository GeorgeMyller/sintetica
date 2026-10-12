# Spec: pii-guard

> Selo 🟡 PLANEJADO em todos os itens. Fonte: `prd.md` (seções 3, 6 e 8), `questions.md` (Q6, Q9, Q15, Q21, Q22).

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-10-09
**Reviewers:** Antigravity (revisor do pipeline)

---

## 1. Resumo

🟡 O `pii-guard` é a biblioteca local de detecção e mascaramento de PII. Ela usa detectores determinísticos (CPF, CNPJ, e-mail, telefone, cartão, IPv4/IPv6 e padrões configuráveis) e troca os valores por equivalentes Faker. É usada pela entrevista, pela amostra, pelo `llm-provider` antes do envio externo (Q21) e pelo `quality-evaluator` (Q9).

---

## 2. Contexto e Motivação

**Problema:**
🟡 Dados sintéticos gerados por LLM podem conter PII real memorizada. O usuário também pode digitar dados reais na entrevista.

**Evidências:**
🟡 PRD, métrica "0 ocorrências de PII detectadas". Q9 define os detectores. Q21 exige mascaramento antes de qualquer envio ao `ExternalAPIProvider`. Premissa 2 do PRD: detecção local sem serviço externo.

**Por que agora:**
🟡 4 componentes dependem do `pii-guard`. Ele é pré-requisito da privacidade por design (Q15).

---

## 3. Goals (Objetivos)

- [ ] 🟡 G-01: Detectar 100% dos casos do conjunto de teste de referência para os 7 tipos de PII.
- [ ] 🟡 G-02: Manter falsos positivos ≤ 5% no conjunto de teste de dados sem PII.
- [ ] 🟡 G-03: Processar 10.000 registros de 1 KB em ≤ 30 s.
- [ ] 🟡 G-04: Rodar 100% local, com 0 chamadas de rede.

**Métricas de sucesso:**
| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| 🟡 Recall no conjunto de referência | 🟡 não existe | 🟡 100% | 🟡 MVP |
| 🟡 Taxa de falsos positivos | 🟡 não existe | 🟡 ≤ 5% | 🟡 MVP |
| 🟡 Tempo para 10.000 registros de 1 KB | 🟡 não existe | 🟡 ≤ 30 s | 🟡 MVP |

---

## 4. Non-Goals (Fora do Escopo)

- 🟡 NG-01: Não há detecção por modelo de NER ou ML. Só regras determinísticas (Q9).
- 🟡 NG-02: Não há detecção de nomes de pessoas e endereços livres nesta versão. O limite fica documentado no relatório.
- 🟡 NG-03: Não há garantia de anonimização formal, como privacidade diferencial (PRD, não-objetivo 6).
- 🟡 NG-04: Não há envio de dados a serviço externo de detecção (Q15).

---

## 5. Usuários e Personas

**Usuário primário:** 🟡 Os componentes `intent-interview`, `sample-preview`, `llm-provider`, `batch-generator` e `quality-evaluator`.
**Usuário secundário:** 🟡 As 3 personas, que configuram padrões extras em `policy.json` e leem os limites no relatório.

**Jornada atual (sem a feature):**
1. 🟡 O usuário confere à mão se o dataset tem dados pessoais.
2. 🟡 Dados reais vazam para APIs externas sem aviso.

**Jornada futura (com a feature):**
1. 🟡 Todo texto passa pelo `pii-guard` antes de ser gravado ou enviado.
2. 🟡 O relatório final mostra 0 ocorrências e os limites da cobertura.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | 🟡 O sistema deve detectar CPF com ou sem pontuação e validar os 2 dígitos verificadores. | Must | 🟡 `529.982.247-25` é detectado; `111.111.111-12` não é. |
| RF-02 | 🟡 O sistema deve detectar CNPJ com ou sem pontuação e validar os dígitos verificadores. | Must | 🟡 Um CNPJ válido é detectado; o mesmo com DV trocado não é. |
| RF-03 | 🟡 O sistema deve detectar e-mail, telefone brasileiro (com ou sem `+55` e DDD, 8 ou 9 dígitos), cartão de 13 a 19 dígitos com verificação de Luhn, IPv4 e IPv6. | Must | 🟡 Um teste por tipo, com 1 caso positivo e 1 negativo, passa. |
| RF-04 | 🟡 O sistema deve carregar padrões extras de `pii_custom_patterns` em `policy.json`. | Must | 🟡 Com o padrão `MAT-\d{6}`, o texto `MAT-123456` é detectado como `custom`. |
| RF-05 | 🟡 O sistema deve expor `scan(text)`, que retorna a lista de achados com tipo, início e fim. | Must | 🟡 `scan` de um texto com 1 e-mail retorna 1 achado do tipo `email`. |
| RF-06 | 🟡 O sistema deve expor `mask(text)`, que troca cada achado por um valor Faker `pt_BR` do mesmo tipo e formato. | Must | 🟡 Após `mask`, `scan` não encontra PII fora da allowlist. |
| RF-07 | 🟡 O sistema deve registrar o hash SHA-256 de cada valor Faker inserido em uma allowlist por dataset (`datasets/<slug>/.pii_allowlist`). | Must | 🟡 O hash de cada substituto está na allowlist. |
| RF-08 | 🟡 O sistema deve classificar um achado como vazamento apenas quando o hash do valor não estiver na allowlist. | Must | 🟡 Um CPF gerado pelo próprio `mask` não conta como vazamento. |
| RF-09 | 🟡 O sistema deve aceitar uma semente (`seed`) para que o mascaramento seja reproduzível. | Should | 🟡 Duas chamadas com a mesma semente e o mesmo texto produzem a mesma saída. |
| RF-10 | 🟡 O sistema nunca deve gravar o valor original de um achado em log, relatório ou arquivo. | Must | 🟡 Busca do valor original em todos os arquivos de `datasets/<slug>/` retorna 0 resultados. |
| RF-11 | 🟡 O sistema deve expor a lista de tipos cobertos e limites conhecidos, para o relatório do `quality-evaluator` (Q9). | Must | 🟡 `coverage()` retorna os 7 tipos, os padrões custom e os limites de NG-02. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 Um componente chama `mask(text)`.
2. 🟡 O sistema executa os detectores e valida dígitos verificadores e Luhn.
3. 🟡 O sistema troca cada achado por um valor Faker do mesmo tipo.
4. 🟡 O sistema grava o hash de cada substituto na allowlist.
5. 🟡 Resultado: o sistema devolve o texto mascarado e a contagem por tipo, sem os valores originais.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Só verificação:**
1. 🟡 O `quality-evaluator` chama `scan` em cada campo de texto.
2. 🟡 O sistema retorna os achados fora da allowlist como vazamentos.

**Fluxo Alternativo B — Valor com campo PII declarado no schema:**
1. 🟡 O schema tem um campo `cpf` que o usuário quer no dataset.
2. 🟡 O `batch-generator` aplica `mask` ao registro; o CPF gerado pelo LLM vira um CPF Faker registrado na allowlist.

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | 🟡 Runtime Python | 🟡 Python ≥ 3.10 com `uv` e Faker | 🟡 Q18 |
| RNF-02 | 🟡 Qualidade de código | 🟡 `mypy --strict` e `ruff` sem erros | 🟡 PRD, seção 6 |
| RNF-03 | 🟡 Cobertura de testes | 🟡 ≥ 80% com `pytest-cov`; 100% nos detectores | 🟡 Q19 |
| RNF-04 | 🟡 Desempenho | 🟡 ≤ 30 s para 10.000 registros de 1 KB | 🟡 G-03 |
| RNF-05 | 🟡 Rede | 🟡 0 chamadas | 🟡 G-04 |

---

## 8. Design e Interface

**Componentes afetados:** 🟡 Módulo Python `sintetica.pii`; arquivo `.sintetica/policy.json`; arquivo `datasets/<slug>/.pii_allowlist`.

**Comportamento esperado:**
🟡 Biblioteca sem interface própria. As mensagens ao usuário vêm dos componentes que a chamam.

**Estados da UI:**
- 🟡 Estado vazio: texto sem PII retorna lista vazia e texto inalterado.
- 🟡 Estado de carregamento: não se aplica.
- 🟡 Estado de erro: padrão custom inválido gera `PolicyError` com o índice do padrão.
- 🟡 Estado de sucesso: texto mascarado e contagem por tipo.

---

## 9. Modelo de Dados

```
PiiFinding {
  type: "cpf" | "cnpj" | "email" | "phone" | "card" | "ipv4" | "ipv6" | "custom"
  start: int
  end: int
  field: string | null          // nome do campo, quando aplicável
  preview: string               // 2 primeiros caracteres + "***"
}

MaskResult {
  text: string
  counts: dict<string, int>     // achados por tipo
}

Allowlist {
  hashes: set<string>           // SHA-256 dos valores Faker inseridos
}
```

**Migrações necessárias:** 🟡 Não.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| 🟡 Faker (locale `pt_BR`) | 🟡 Obrigatória | 🟡 `mask` falha; os componentes chamadores encerram com erro (fallback seguro). |
| 🟡 Módulo `ipaddress` (biblioteca padrão) | 🟡 Obrigatória | 🟡 Sempre disponível no Python ≥ 3.10. |
| 🟡 `.sintetica/policy.json` | 🟡 Opcional | 🟡 Sem o arquivo, o sistema usa só os 7 detectores padrão. |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| 🟡 EC-01: Sequência de 11 dígitos que não é CPF | 🟡 ID numérico com DV inválido | 🟡 Não é detectado (RF-01). |
| 🟡 EC-02: Número de versão parecido com IPv4 | 🟡 Texto `1.2.3.4` | 🟡 É detectado como IPv4. Falso positivo aceito e documentado nos limites. |
| 🟡 EC-03: Padrão custom inválido | 🟡 Regex que não compila | 🟡 `PolicyError` no carregamento; nenhum texto é processado (falha segura). |
| 🟡 EC-04: Falha do Faker | 🟡 Exceção ao gerar substituto | 🟡 O sistema troca o valor por `***` do mesmo tamanho e registra a falha. |
| 🟡 EC-05: Texto muito longo | 🟡 Campo > 1 MB | 🟡 O sistema processa em blocos de 64 KB com sobreposição de 64 caracteres. |
| 🟡 EC-06: Allowlist ausente | 🟡 Arquivo apagado | 🟡 Todo achado conta como vazamento; o relatório avisa a causa. |

---

## 12. Segurança e Privacidade

- 🟡 **Autenticação:** não se aplica.
- 🟡 **Autorização:** não se aplica.
- 🟡 **Dados sensíveis:** valores originais nunca são gravados (RF-10). A allowlist guarda só hashes.
- 🟡 **Auditoria:** contagem por tipo em cada chamada; sem valores.

---

## 13. Plano de Rollout

- 🟡 **Estratégia:** versão `0.1.0`; entregue antes dos componentes que dependem dele.
- 🟡 **Como reverter (rollback):** reinstalar a versão anterior; os padrões custom em `policy.json` continuam válidos.
- 🟡 **Monitoramento pós-deploy:** issues de falso positivo ou falso negativo viram casos no conjunto de teste de referência.

---

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---------|---------|------|-------|
| OQ-01 | 🟡 A allowlist de valores Faker (RF-07, RF-08) é o critério aceito para não contar campos PII intencionais como vazamento? | 🟡 Alto | 🟡 Antigravity | 🟡 Antes do `/reversa-plan` |
| OQ-02 | 🟡 Quem monta o conjunto de teste de referência de G-01 e G-02? | 🟡 Médio | 🟡 Antigravity | 🟡 Antes do `/reversa-plan` |

---

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---------|--------------------------|---------|
| 🟡 Validar DV de CPF e CNPJ e Luhn de cartão | 🟡 Só regex de formato | 🟡 Reduz falsos positivos em IDs numéricos. |
| 🟡 Allowlist por hash | 🟡 Lista de valores em texto | 🟡 Não guarda valores no disco. |
| 🟡 Biblioteca única para 4 componentes | 🟡 Detectores separados por componente | 🟡 Mesma regra em todo o pipeline; a métrica do eval é coerente com o mascaramento. |

---

## Apêndice

### Referências
- 🟡 `../prd.md`, seções 3, 6 e 8.
- 🟡 `../questions.md`, Q9, Q15, Q21.

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
