# Plano de Exploração — data_sintetic_generation

> Criado pelo Reversa em 2026-10-09
> Marque cada tarefa com ✅ quando concluída.
> Você pode editar este plano antes de iniciar: adicione, remova ou reordene tarefas conforme necessário.

---

## Decisões do usuário (2026-10-12)

- Nível de documentação: **completo**.
- Organização das specs: `module` (já gravada em `.reversa/config.toml`).
- O Redator atualiza as specs em `_reversa_sdd/sdd/` para refletir o código, com selo 🟢 CONFORME CÓDIGO, consolidando os adendos 001 a 008.
- Arqueologia de decisões pelos artefatos `_reversa_forward/` e `_reversa_sdd/questions.md`.
- Agentes independentes pulados.

## Fase 1: Reconhecimento 🔍

- ✅ **Scout** — Mapeamento de estrutura de pastas e tecnologias
- ✅ **Scout** — Análise de dependências e gerenciadores de pacotes
- ✅ **Scout** — Identificação de entry points, CI/CD e configurações

## Decisão de organização das specs 🗂️

> Entre o Scout e o Arqueólogo, o Reversa pergunta como você quer organizar as specs (por módulo, caso de uso, endpoint, híbrida, por features ou customizada). A escolha fica persistida em `.reversa/config.toml` na seção `[specs]` e não será reperguntada em execuções futuras. Para reapresentar o menu, remova manualmente a seção.

## Fase 2: Escavação 🏗️

> Módulos identificados pelo Scout em 2026-10-12.

- ✅ **Arqueólogo** — Análise do módulo `pii`
- ✅ **Arqueólogo** — Análise do módulo `providers`
- ✅ **Arqueólogo** — Análise do módulo `schema`
- ✅ **Arqueólogo** — Análise do módulo `intent`
- ✅ **Arqueólogo** — Análise do módulo `sample`
- ✅ **Arqueólogo** — Análise do módulo `batch`
- ✅ **Arqueólogo** — Análise do módulo `quality`
- ✅ **Arqueólogo** — Análise do módulo `installer` (pacote npm, skills e lançador)

## Fase 3: Interpretação 🧠

- ✅ **Detetive** — Arqueologia de decisões e ADRs retroativos (fonte: `_reversa_forward/` e `_reversa_sdd/questions.md`; o projeto não tem git)
- ✅ **Detetive** — Regras de negócio implícitas e máquinas de estado
- ✅ **Detetive** — Matriz de permissões (RBAC/ACL)
- ✅ **Arquiteto** — Diagramas C4 (Contexto, Containers, Componentes)
- ✅ **Arquiteto** — ERD completo e integrações externas
- ✅ **Arquiteto** — Spec Impact Matrix

## Fase 4: Geração 📝

- ✅ **Redator** — Specs SDD por componente (8 specs em `sdd/`, selo 🟢 CONFORME CÓDIGO)
- ⏭️ **Redator** — OpenAPI: não aplicável (sem API HTTP)
- ✅ **Redator** — User Stories (4 arquivos)
- ✅ **Redator** — Code/Spec Matrix

## Fase 5: Revisão ✅

- ✅ **Revisor** — Revisão cruzada de specs (sem Codex)
- ✅ **Revisor** — Resolução de lacunas com o usuário (Q53 a Q56 respondidas e processadas)
- ✅ **Revisor** — Relatório de confiança final

---

## Agentes Independentes

> Execute estes agentes quando os recursos estiverem disponíveis — podem rodar em qualquer fase.

- ⏭️ **Visor** — pulado por decisão do usuário (sem interface gráfica)
- ⏭️ **Data Master** — pulado por decisão do usuário (sem banco de dados)
- ⏭️ **Design System** — pulado por decisão do usuário (sem interface gráfica)
- ⏭️ **Tracer** — pulado por decisão do usuário (sem sistema publicado)

---

## Próximo passo

Após o Time de Descoberta concluir e o `_reversa_sdd/` estar populado, você pode disparar um dos fluxos seguintes:

- `/reversa-migrate`: orquestrador do **Time de Migração** (Paradigm Advisor → Curator → Strategist → Designer → Screen Translator → Inspector). Gera as specs do sistema novo. Saída em `_reversa_sdd/migration/` e `_reversa_sdd/screens/`.
- `/reversa-reconstructor`: gera plano bottom-up para reimplementar o software a partir das specs do legado (uma tarefa por sessão).
