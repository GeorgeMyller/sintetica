# Spec: schema-builder

> Selo 🟡 PLANEJADO em todos os itens. Fonte: `prd.md` (seções 3, 4 e 9), `personas.md`, `questions.md` (Q2, Q19, Q22).

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-10-09
**Reviewers:** Antigravity (revisor do pipeline)

---

## 1. Resumo

🟡 O `schema-builder` é a skill `sintetica-schema`. Ela traduz `intent.json` em um modelo Pydantic v2 e mostra o resultado para revisão. O schema aprovado é o contrato que valida cada registro na amostra, na geração e na avaliação.

---

## 2. Contexto e Motivação

**Problema:**
🟡 Scripts manuais com LLM não garantem schema. Sem contrato, a métrica de conformidade de ≥ 95% (PRD, seção 3) não pode ser medida.

**Evidências:**
🟡 Q2 define o valor entregue como "lote validado por schemas Pydantic". O passo 4 da jornada de todas as personas é revisar o schema proposto.

**Por que agora:**
🟡 `sample-preview`, `batch-generator` e `quality-evaluator` dependem do schema aprovado.

---

## 3. Goals (Objetivos)

- [ ] 🟡 G-01: Gerar um schema Pydantic v2 válido a partir de qualquer `intent.json`, inclusive com itens INDEFINIDO.
- [ ] 🟡 G-02: Mostrar o schema em uma tabela legível por quem não programa (campo, tipo, restrição, descrição).
- [ ] 🟡 G-03: Gerar código que passa em `mypy --strict` e `ruff` sem erros em 100% dos casos.

**Métricas de sucesso:**
| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| 🟡 Schemas gerados que importam sem erro | 🟡 não existe | 🟡 100% | 🟡 MVP |
| 🟡 Schemas aprovados em ≤ 2 rodadas de ajuste | 🟡 não existe | 🟡 ≥ 80% | 🟡 3 meses |

---

## 4. Non-Goals (Fora do Escopo)

- 🟡 NG-01: O `schema-builder` não infere schema a partir de dados reais ou de bancos do usuário (PRD, não-objetivo 4).
- 🟡 NG-02: O `schema-builder` não executa código Python arbitrário escrito pelo LLM. O código vem de um gerador determinístico.
- 🟡 NG-03: Não há suporte a imagem, áudio ou binários como tipo de campo (PRD, não-objetivo 2).
- 🟡 NG-04: Não há validação cruzada entre registros (ex.: chave estrangeira entre arquivos) nesta versão.

---

## 5. Usuários e Personas

**Usuário primário:** 🟡 `dev-de-testes` (compara com os modelos do sistema sob teste), `engenheiro-de-ml` (turnos, papéis e rótulos) e `analista-de-dados` (tipos e restrições por coluna).
**Usuário secundário:** 🟡 As skills `sintetica-sample`, `sintetica-generate` e `sintetica-eval`, que importam o schema.

**Jornada atual (sem a feature):**
1. 🟡 O usuário escreve classes Pydantic à mão ou não valida a saída do LLM.
2. 🟡 Erros de tipo aparecem só no uso do dataset.

**Jornada futura (com a feature):**
1. 🟡 O sistema propõe o schema a partir da intenção.
2. 🟡 O usuário revisa uma tabela e pede ajustes em linguagem natural.
3. 🟡 O sistema grava o schema aprovado e segue para a amostra.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | 🟡 O sistema deve ler `datasets/<slug>/intent.json` e produzir uma definição declarativa `schema.json` com nome, tipo, restrições e descrição de cada campo. | Must | 🟡 `schema.json` existe e valida contra o meta-schema `FieldSpec` (seção 9). |
| RF-02 | 🟡 O sistema deve gerar `schema.py` a partir de `schema.json` por um gerador determinístico, com a classe raiz `Record`. | Must | 🟡 Duas gerações a partir do mesmo `schema.json` produzem arquivos idênticos byte a byte. |
| RF-03 | 🟡 O sistema deve suportar os tipos: texto, inteiro, decimal, booleano, data, data-hora, enum, lista e objeto aninhado. | Must | 🟡 Um teste por tipo gera e importa o schema sem erro. |
| RF-04 | 🟡 O sistema deve suportar as restrições: obrigatório, mínimo, máximo, tamanho mínimo, tamanho máximo, padrão regex e valores permitidos. | Must | 🟡 Um registro que viola cada restrição falha na validação. |
| RF-05 | 🟡 Para formato JSONL conversacional, o sistema deve usar o modelo `Conversation` com `messages` (papel `system`, `user` ou `assistant` e conteúdo) e `labels`. | Must | 🟡 Intenção da persona `engenheiro-de-ml` gera `Record` com `messages` e `labels`. |
| RF-06 | 🟡 Para formato CSV, o sistema deve recusar objetos aninhados e listas, e propor achatamento com prefixo (ex.: `endereco_cidade`). | Must | 🟡 Intenção CSV com endereço aninhado gera campos achatados. |
| RF-07 | 🟡 O sistema deve mostrar o schema em tabela (campo, tipo, restrição, descrição) e aceitar ajustes em linguagem natural. | Must | 🟡 O pedido "idade entre 18 e 90" altera `ge` e `le` do campo `idade`. |
| RF-08 | 🟡 O sistema deve validar `schema.py` com import, `Record.model_json_schema()` e `mypy --strict` antes de mostrar ao usuário. | Must | 🟡 Um `schema.py` com erro de tipo nunca chega ao usuário. |
| RF-09 | 🟡 O sistema deve mapear item INDEFINIDO de estrutura para um campo de texto com descrição "a definir" e avisar o usuário. | Should | 🟡 `structure` indefinido gera ao menos 1 campo de texto e o aviso. |
| RF-10 | 🟡 O sistema deve gravar `schema_version` (hash SHA-256 de `schema.json`) para rastrear qual schema validou cada lote. | Should | 🟡 Alterar 1 campo muda o hash. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O `intent-interview` chama o `schema-builder` com o caminho de `intent.json`.
2. 🟡 O sistema produz `schema.json` a partir da intenção.
3. 🟡 O sistema gera `schema.py` e o valida (RF-08).
4. 🟡 O sistema mostra a tabela do schema ao usuário.
5. 🟡 O usuário aprova.
6. 🟡 Resultado: o sistema grava `schema_version` e chama o `sample-preview`.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Ajuste do usuário:**
1. 🟡 O usuário pede uma mudança em linguagem natural.
2. 🟡 O sistema altera `schema.json`, gera e valida de novo, e mostra a nova tabela com as diferenças marcadas.

**Fluxo Alternativo B — Modo Expresso:**
1. 🟡 O sistema gera e valida o schema.
2. 🟡 O sistema aprova sem confirmação e segue para a amostra (RF-10 do `intent-interview`).

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | 🟡 Runtime Python | 🟡 Python ≥ 3.10 com `uv` e Pydantic v2 | 🟡 Q18 |
| RNF-02 | 🟡 Qualidade do código gerado | 🟡 `mypy --strict` e `ruff` sem erros | 🟡 PRD, seção 6 |
| RNF-03 | 🟡 Cobertura de testes | 🟡 ≥ 80% com `pytest-cov` | 🟡 Q19 |
| RNF-04 | 🟡 Desempenho | 🟡 Geração e validação em ≤ 10 s, sem contar o LLM | 🟡 Cabe na meta de < 10 min |
| RNF-05 | 🟡 Limite de tamanho | 🟡 ≤ 100 campos por schema | 🟡 Ver OQ-01 |

---

## 8. Design e Interface

**Componentes afetados:** 🟡 Skill `sintetica-schema`; comando `uv run sintetica schema`; arquivos `schema.json` e `schema.py` em `datasets/<slug>/`.

**Comportamento esperado:**
🟡 O usuário vê uma tabela Markdown. Ele nunca precisa ler o código Python para aprovar, a menos que queira.

**Estados da UI:**
- 🟡 Estado vazio: não se aplica; o schema sempre tem ao menos 1 campo.
- 🟡 Estado de carregamento: o sistema informa "Gerando schema".
- 🟡 Estado de erro: o sistema mostra o campo e a regra que falharam.
- 🟡 Estado de sucesso: tabela do schema com a pergunta "Aprovar?".

---

## 9. Modelo de Dados

```
SchemaSpec {
  model_name: "Record"
  format: "csv" | "json" | "jsonl"
  fields: list<FieldSpec>
  schema_version: string        // SHA-256 de schema.json
}

FieldSpec {
  name: string                  // snake_case ASCII
  type: "text" | "int" | "decimal" | "bool" | "date" | "datetime" | "enum" | "list" | "object"
  required: boolean
  description: string
  constraints: {
    ge?: number, le?: number,
    min_length?: int, max_length?: int,
    pattern?: string, choices?: list<string>
  }
  items?: FieldSpec             // para "list"
  fields?: list<FieldSpec>      // para "object"
}
```

**Migrações necessárias:** 🟡 Não.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| 🟡 Pydantic v2 | 🟡 Obrigatória | 🟡 O comando falha com mensagem de dependência ausente e instrução `uv sync`. |
| 🟡 `mypy` | 🟡 Obrigatória | 🟡 Sem `mypy`, a validação RF-08 falha e o schema não é mostrado. |
| 🟡 LLM do harness | 🟡 Obrigatória | 🟡 O harness traduz a intenção em `schema.json`; sem ele, a skill não roda. |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| 🟡 EC-01: Nome de campo inválido | 🟡 Nome com acento, espaço ou palavra reservada do Python | 🟡 O sistema normaliza para snake_case ASCII e adiciona sufixo `_` a palavra reservada. |
| 🟡 EC-02: Restrições contraditórias | 🟡 Mínimo maior que máximo | 🟡 O sistema recusa o ajuste e mostra os 2 valores em conflito. |
| 🟡 EC-03: Falha na validação `mypy` | 🟡 Defeito no gerador | 🟡 O sistema não mostra o schema, grava o erro em `datasets/<slug>/errors.log` e encerra com erro. |
| 🟡 EC-04: Aninhamento em CSV | 🟡 Objeto ou lista com formato CSV | 🟡 O sistema aplica o achatamento do RF-06 e avisa. |
| 🟡 EC-05: Excesso de campos | 🟡 Mais de 100 campos | 🟡 O sistema recusa e pede para dividir o dataset. |
| 🟡 EC-06: Ajustes sem fim | 🟡 5 rodadas de ajuste sem aprovação | 🟡 O sistema sugere reiniciar a entrevista com `/sintetica-start`. |

---

## 12. Segurança e Privacidade

- 🟡 **Autenticação:** não se aplica.
- 🟡 **Autorização:** não se aplica.
- 🟡 **Dados sensíveis:** o schema contém apenas nomes e restrições de campos, sem valores.
- 🟡 **Segurança de código:** o LLM nunca escreve `schema.py` diretamente; o gerador determinístico impede injeção de código (NG-02).

---

## 13. Plano de Rollout

- 🟡 **Estratégia:** entregue na versão `0.1.0`, junto com o `intent-interview`.
- 🟡 **Como reverter (rollback):** `schema.json` é a fonte; reverter o gerador e gerar `schema.py` de novo.
- 🟡 **Monitoramento pós-deploy:** issues no repositório; `errors.log` por dataset.

---

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---------|---------|------|-------|
| OQ-01 | 🟡 O limite de 100 campos por schema (RNF-05) é adequado? | 🟡 Baixo | 🟡 Antigravity | 🟡 Antes do `/reversa-plan` |
| OQ-02 | 🟡 O limite de 5 rodadas de ajuste (EC-06) é adequado? | 🟡 Baixo | 🟡 Antigravity | 🟡 Antes do `/reversa-plan` |

---

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---------|--------------------------|---------|
| 🟡 `schema.json` declarativo e gerador determinístico | 🟡 LLM escreve `schema.py` diretamente | 🟡 Reprodutibilidade e segurança (NG-02). |
| 🟡 Classe raiz fixa `Record` | 🟡 Nome livre | 🟡 As outras skills importam sempre o mesmo nome. |
| 🟡 Achatamento em CSV | 🟡 Serializar objetos como JSON dentro da célula | 🟡 O `analista-de-dados` carrega o CSV direto em pipelines e dashboards. |

---

## Apêndice

### Referências
- 🟡 `../prd.md`, seções 3, 4 e 9.
- 🟡 `../personas.md`, passo 4 das jornadas.

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
