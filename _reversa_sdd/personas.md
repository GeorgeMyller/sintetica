# Personas e Jornadas

> Selo 🟡 PLANEJADO em todos os itens.

## Persona 1: dev-de-testes
- **Perfil:** 🟡 Desenvolvedor de software que precisa de massa de dados realista para testes funcionais e de integração.
- **Contexto:** 🟡 Escreve testes de integração no IDE com um assistente de IA (Claude Code, Antigravity, Cursor). Não tem dados realistas sem PII para alimentar os testes.
- **Nível técnico:** 🟡 avançado, em programação; intermediário em modelagem de dados.
- **Dor principal:** 🟡 Gerar massa de teste exige scripts ad hoc com Faker ou cópia de dados de produção, com risco de expor PII.
- **Objetivo final:** 🟡 Entregar software confiável sem expor dados de produção.

### Jornada principal
1. 🟡 Instalar o sintetica no repositório com `npx sintetica install`.
2. 🟡 Iniciar a entrevista com `/sintetica-start` e ver o caminho absoluto de `datasets/<slug>/seeds/`.
3. 🟡 Descrever as entidades do sistema, o formato (JSON ou CSV) e o volume da massa de teste.
4. 🟡 Revisar o schema Pydantic proposto contra os modelos do sistema sob teste.
5. 🟡 Aprovar a amostra de 3 a 5 registros.
6. 🟡 Gerar o lote completo para a suíte de testes.
7. 🟡 Ler o relatório de qualidade e PII e carregar o dataset nos fixtures de teste.

---

## Persona 2: engenheiro-de-ml
- **Perfil:** 🟡 Engenheiro de Machine Learning que precisa de dataset conversacional rotulado para fine-tuning de LLM.
- **Contexto:** 🟡 Prepara um fine-tuning e tem poucos exemplos rotulados. Usa um assistente de IA no terminal ou no IDE.
- **Nível técnico:** 🟡 avançado, em ML e Python.
- **Dor principal:** 🟡 Faltam exemplos rotulados diversos. Scripts manuais com LLM não garantem schema, diversidade nem ausência de PII.
- **Objetivo final:** 🟡 Melhorar o modelo com dados diversos e de qualidade comprovada.

### Jornada principal
1. 🟡 Instalar o sintetica no projeto de treinamento com `npx sintetica install`.
2. 🟡 Iniciar a entrevista com `/sintetica-start` e ver o caminho absoluto de `datasets/<slug>/seeds/`.
3. 🟡 Descrever a tarefa do modelo, os rótulos, o formato conversacional (ex.: JSONL de mensagens) e o volume.
4. 🟡 Revisar o schema Pydantic proposto para turnos, papéis e rótulos.
5. 🟡 Aprovar a amostra de 3 a 5 conversas.
6. 🟡 Gerar o lote completo em background pelo motor assíncrono.
7. 🟡 Ler o relatório de qualidade, diversidade e PII e usar o dataset no fine-tuning.

---

## Persona 3: analista-de-dados
- **Perfil:** 🟡 Analista de dados que precisa de dados tabulares para validar pipelines e dashboards.
- **Contexto:** 🟡 Valida um pipeline ou dashboard antes de receber dados reais. Usa um assistente de IA como apoio.
- **Nível técnico:** 🟡 intermediário, em Python; avançado em SQL e planilhas.
- **Dor principal:** 🟡 Precisa esperar acesso a dados reais sensíveis para validar o sistema. Gerar tabelas coerentes à mão é lento.
- **Objetivo final:** 🟡 Validar o sistema cedo, sem depender de acesso a dados sensíveis.

### Jornada principal
1. 🟡 Instalar o sintetica no projeto de análise com `npx sintetica install`.
2. 🟡 Iniciar a entrevista com `/sintetica-start` e ver o caminho absoluto de `datasets/<slug>/seeds/`.
3. 🟡 Descrever as colunas, as regras de negócio, o formato tabular (CSV) e o volume em linguagem natural.
4. 🟡 Revisar o schema Pydantic proposto com tipos e restrições de cada coluna.
5. 🟡 Aprovar a amostra de 3 a 5 linhas.
6. 🟡 Gerar o lote completo.
7. 🟡 Ler o relatório de qualidade e PII e carregar o CSV no pipeline ou dashboard.

---

## Notas de rastreabilidade
- 🟡 Personas, contextos, níveis e objetivos aprovados pelo revisor Antigravity (questions.md, Q11 e Q12).
- 🟡 Jornada base de 7 passos aprovada sem alterações (Q13). O passo 3 e o passo 7 foram adaptados ao formato de dado de cada persona.
- 🟡 Passo 6 da persona 2: lotes de produção (1.000 a 10.000 registros) rodam em background pelo `ExternalAPIProvider` (Q8, Q10).

---
Gerado por reversa-researcher em 2026-10-09T16:17:00Z
Fonte: ideation.md, questions.md (Q11 a Q13)
