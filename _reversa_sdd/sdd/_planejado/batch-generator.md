# Spec: batch-generator

> Selo 🟡 PLANEJADO em todos os itens. Fonte: `prd.md` (seções 3, 4, 8 e 9), `personas.md`, `questions.md` (Q8, Q10, Q17, Q21, Q22).

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-10-09
**Reviewers:** Antigravity (revisor do pipeline)

---

## 1. Resumo

🟡 O `batch-generator` é a skill `sintetica-generate`. Ela gera o lote completo com `asyncio`, valida cada registro pelo schema, mascara PII e grava o dataset em CSV, JSON ou JSONL. Lotes de até 100 registros rodam em primeiro plano; lotes maiores, até 10.000, rodam em background.

---

## 2. Contexto e Motivação

**Problema:**
🟡 Scripts manuais com LLM geram registros em série, sem validação e sem recuperação de falhas. Lotes de 1.000 a 10.000 registros ficam lentos e frágeis.

**Evidências:**
🟡 Q10 define lote de teste (≤ 100) e de produção (1.000 a 10.000, em background). PRD, métrica de conformidade ≥ 95%.

**Por que agora:**
🟡 É o passo 6 da jornada das 3 personas e a entrega principal do produto.

---

## 3. Goals (Objetivos)

- [ ] 🟡 G-01: Entregar ≥ 95% do volume pedido com registros válidos pelo schema.
- [ ] 🟡 G-02: Gerar lote de 100 registros em ≤ 5 min, para caber na meta de < 10 min do PRD.
- [ ] 🟡 G-03: Retomar um lote interrompido sem perder registros já gravados.
- [ ] 🟡 G-04: Gravar 0 registros sem passar pelo `pii-guard`.

**Métricas de sucesso:**
| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| 🟡 Registros válidos / volume pedido | 🟡 não existe | 🟡 ≥ 95% | 🟡 3 meses |
| 🟡 Tempo do lote de 100 registros | 🟡 não existe | 🟡 ≤ 5 min | 🟡 3 meses |
| 🟡 Registros perdidos após interrupção | 🟡 não existe | 🟡 0 | 🟡 MVP |

---

## 4. Non-Goals (Fora do Escopo)

- 🟡 NG-01: Não há geração acima de 10.000 registros por lote nesta versão.
- 🟡 NG-02: Não há formatos além de CSV, JSON e JSONL (ex.: Parquet, XLSX).
- 🟡 NG-03: Não há execução distribuída em várias máquinas.
- 🟡 NG-04: O `batch-generator` não calcula métricas de qualidade; isso é papel do `quality-evaluator`.

---

## 5. Usuários e Personas

**Usuário primário:** 🟡 `engenheiro-de-ml` (lotes de produção em background) e `dev-de-testes` e `analista-de-dados` (lotes de teste).
**Usuário secundário:** 🟡 O `quality-evaluator`, que lê o dataset final e `run.json`.

**Jornada atual (sem a feature):**
1. 🟡 O usuário roda um laço de chamadas ao LLM.
2. 🟡 Uma falha no meio perde o progresso.
3. 🟡 O usuário corrige registros malformados à mão.

**Jornada futura (com a feature):**
1. 🟡 O usuário aprova a amostra e o sistema inicia o lote.
2. 🟡 O sistema mostra o progresso ou roda em background.
3. 🟡 O sistema grava o dataset validado e chama o `quality-evaluator`.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | 🟡 O sistema deve ler `intent.json`, `schema.py` e `seeds/sample.<ext>` e recusar o início se a amostra não tiver o `schema_version` atual. | Must | 🟡 Com schema alterado após a amostra, o sistema recusa e indica `/sintetica-sample`. |
| RF-02 | 🟡 O sistema deve obter a estimativa de custo do `llm-provider` e iniciar apenas após a autorização exigida pelo teto (Q17). | Must | 🟡 Com estimativa de US$ 6,00 e resposta `não`, nenhum pedido é enviado. |
| RF-03 | 🟡 O sistema deve dividir o volume em blocos de 10 registros por pedido e enviá-los com concorrência limitada pelo `llm-provider`. | Must | 🟡 Volume de 1.000 gera 100 pedidos. |
| RF-04 | 🟡 O sistema deve validar cada registro com `Record`; inválidos devem ser pedidos de novo, em até 3 rodadas extras. | Must | 🟡 Após 3 rodadas, os inválidos restantes são descartados e contados em `run.json`. |
| RF-05 | 🟡 O sistema deve descartar duplicados exatos (hash SHA-256 do JSON canônico) e pedir substitutos dentro das mesmas 3 rodadas extras. | Should | 🟡 O dataset final tem 0 duplicados exatos. |
| RF-06 | 🟡 O sistema deve aplicar `pii-guard.mask` em cada registro válido antes de gravar. | Must | 🟡 Nenhum registro chega ao disco sem passar pelo `mask`. |
| RF-07 | 🟡 O sistema deve gravar os registros aceitos em `datasets/<slug>/output/records.partial.jsonl` a cada bloco concluído. | Must | 🟡 Após interromper o processo, o arquivo parcial contém todos os blocos concluídos. |
| RF-08 | 🟡 O sistema deve rodar em primeiro plano para volume ≤ 100 e em background para volume > 100. | Must | 🟡 Volume 1.000 devolve o controle ao chat em ≤ 5 s e mostra o comando de acompanhamento. |
| RF-09 | 🟡 O sistema deve atualizar `run.json` a cada bloco com aceitos, descartados, custo acumulado e status. | Must | 🟡 `uv run sintetica status <slug>` mostra esses valores. |
| RF-10 | 🟡 O sistema deve retomar um lote interrompido a partir de `records.partial.jsonl` com `uv run sintetica generate <slug> --resume`. | Must | 🟡 Após `--resume`, o total final é igual ao volume pedido, sem duplicar blocos. |
| RF-11 | 🟡 Ao terminar, o sistema deve converter o arquivo parcial para `output/dataset.<ext>` no formato pedido e chamar o `quality-evaluator`. | Must | 🟡 Formato CSV gera arquivo UTF-8, separador vírgula, cabeçalho na ordem do schema e aspas pela RFC 4180. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O `sample-preview` chama o `batch-generator` após a aprovação.
2. 🟡 O sistema verifica o `schema_version` e obtém a estimativa de custo.
3. 🟡 O sistema divide o volume em blocos e envia com concorrência.
4. 🟡 O sistema valida, remove duplicados, mascara e grava cada bloco.
5. 🟡 O sistema atualiza `run.json` a cada bloco.
6. 🟡 O sistema converte o arquivo parcial para o formato final.
7. 🟡 Resultado: o sistema chama o `quality-evaluator`.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Lote em background:**
1. 🟡 Volume > 100: o sistema inicia um processo separado e grava o PID em `run.json`.
2. 🟡 O sistema informa o comando `uv run sintetica status <slug>`; ao terminar, o processo chama o `quality-evaluator`.

**Fluxo Alternativo B — Retomada:**
1. 🟡 O usuário executa `--resume` após uma interrupção.
2. 🟡 O sistema conta os registros do arquivo parcial e gera apenas o restante.

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | 🟡 Runtime Python | 🟡 Python ≥ 3.10 com `uv` e `asyncio` | 🟡 Q18 |
| RNF-02 | 🟡 Qualidade de código | 🟡 `mypy --strict` e `ruff` sem erros | 🟡 PRD, seção 6 |
| RNF-03 | 🟡 Cobertura de testes | 🟡 ≥ 80% com `pytest-cov` | 🟡 Q19 |
| RNF-04 | 🟡 Desempenho | 🟡 ≤ 5 min para 100 registros | 🟡 G-02 |
| RNF-05 | 🟡 Durabilidade | 🟡 Gravação por bloco com `fsync` | 🟡 G-03 |
| RNF-06 | 🟡 Memória | 🟡 ≤ 500 MB para 10.000 registros de 1 KB | 🟡 Escrita em fluxo |

---

## 8. Design e Interface

**Componentes afetados:** 🟡 Skill `sintetica-generate`; comandos `uv run sintetica generate` e `uv run sintetica status`; pasta `datasets/<slug>/output/`; arquivo `run.json`.

**Comportamento esperado:**
🟡 Em primeiro plano, o sistema mostra uma linha de progresso por bloco. Em background, o sistema devolve o controle ao chat e o usuário consulta o status.

**Estados da UI:**
- 🟡 Estado vazio: não se aplica.
- 🟡 Estado de carregamento: "Bloco 7/10, 68 válidos, 2 descartados, US$ 0,00".
- 🟡 Estado de erro: status, causa e comando `--resume`.
- 🟡 Estado de sucesso: caminho absoluto do dataset e início do `quality-evaluator`.

---

## 9. Modelo de Dados

```
RunState {
  slug: string
  status: "em_andamento" | "concluido" | "incompleto" | "interrompido_custo" | "falha_provedor"
  pid: int | null               // só em background
  volume_requested: int
  accepted: int
  discarded_invalid: int
  discarded_duplicate: int
  cost_usd: decimal
  authorized_usd: decimal | null
  provider: string
  schema_version: string
  started_at: string
  finished_at: string | null
}
```

🟡 Status `incompleto`: `accepted` < 95% do volume pedido após as rodadas extras.

**Migrações necessárias:** 🟡 Não.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| 🟡 `llm-provider` | 🟡 Obrigatória | 🟡 Sem provedor disponível, o lote não inicia; mensagem do `llm-provider`. |
| 🟡 `pii-guard` | 🟡 Obrigatória | 🟡 O lote não grava registros e para com erro (fallback seguro). |
| 🟡 `schema-builder` (`schema.py`) | 🟡 Obrigatória | 🟡 Sem schema, o lote não inicia. |
| 🟡 `quality-evaluator` | 🟡 Obrigatória | 🟡 O dataset fica gravado; o usuário roda `/sintetica-eval` depois. |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| 🟡 EC-01: Falha do provedor | 🟡 Timeout ou 5xx após os retries do `llm-provider` | 🟡 O sistema grava os blocos concluídos, marca `falha_provedor` e mostra o comando `--resume`. |
| 🟡 EC-02: Teto de custo atingido | 🟡 Custo acumulado = valor autorizado | 🟡 Status `interrompido_custo`; dataset parcial convertido e avaliado. |
| 🟡 EC-03: Conformidade < 95% | 🟡 Mais de 5% de inválidos após 3 rodadas | 🟡 Status `incompleto`; o dataset é gravado e o relatório aponta a falha. |
| 🟡 EC-04: Processo morto | 🟡 Máquina desligada durante o background | 🟡 `status` detecta PID inexistente e sugere `--resume`. |
| 🟡 EC-05: Disco cheio | 🟡 Erro de escrita | 🟡 O sistema para, mantém o último bloco íntegro e mostra o caminho. |
| 🟡 EC-06: Lote duplicado | 🟡 Novo `generate` com lote em andamento | 🟡 O sistema recusa e mostra o status do lote atual. |

---

## 12. Segurança e Privacidade

- 🟡 **Autenticação:** chaves via `llm-provider`, nunca gravadas.
- 🟡 **Autorização:** custo acima do teto exige autorização (Q17).
- 🟡 **Dados sensíveis:** todo registro passa pelo `pii-guard` antes de ir ao disco (G-04).
- 🟡 **Auditoria:** `run.json` registra provedor, custo, autorização e contagens.

---

## 13. Plano de Rollout

- 🟡 **Estratégia:** versão `0.1.0`; testes de carga com 10.000 registros usando provedor simulado.
- 🟡 **Como reverter (rollback):** reinstalar a versão anterior; `records.partial.jsonl` continua legível.
- 🟡 **Monitoramento pós-deploy:** taxa de `incompleto` e `falha_provedor` reportada em issues.

---

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---------|---------|------|-------|
| OQ-01 | 🟡 Volumes de 101 a 999 não têm classe no PRD. Tratar como background (RF-08) está correto? | 🟡 Médio | 🟡 Antigravity | 🟡 Antes do `/reversa-plan` |
| OQ-02 | 🟡 O tamanho de bloco de 10 registros por pedido é adequado para conversas longas (JSONL)? | 🟡 Baixo | 🟡 Antigravity | 🟡 Antes do `/reversa-plan` |

---

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---------|--------------------------|---------|
| 🟡 Arquivo parcial JSONL por bloco | 🟡 Gravar só no fim | 🟡 Retomada sem perda (G-03). |
| 🟡 Mascarar no gerador e verificar no eval | 🟡 Só verificar no eval | 🟡 Privacidade por design; o eval confirma de forma independente. |
| 🟡 Limite de 100 para primeiro plano | 🟡 Limite de 1.000 | 🟡 Q10: lote de teste ≤ 100. |

---

## Apêndice

### Referências
- 🟡 `../prd.md`, seções 3, 4, 8 e 9.
- 🟡 `../questions.md`, Q8, Q10, Q17, Q21.

### Histórico de Revisões
| Versão | Data | Autor | Mudanças |
|--------|------|-------|---------|
| 1.0 | 2026-10-09 | reversa-spec-sdd | 🟡 Criação inicial |

---

## Relatório de avaliação (spec_scorer.py)

**Score total:** 100.0/100
**Iterações:** 2
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
