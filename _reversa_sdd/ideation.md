# Ideation, sintetica

> Selo 🟡 PLANEJADO em todos os itens, sujeito a validação.

## Brief original
Criar o framework `sintetica` para geração de dados sintéticos orientada por intenção e entrevistas conversacionais com agentes de IA. O framework deve seguir os padrões arquiteturais de referência dos frameworks do Professor Sandeco (`reversa`, `mira-animator`, `@sandeco/itsfine`).

### 1. Pilares Arquiteturais Obrigatórios
- **Instalador Universal CLI**: Pacote Node.js executável via `npx sintetica install` com detecção automática de harnesses (Claude Code, Antigravity, Cursor, Gemini CLI, Codex).
- **Injeção de Skills**: Instalação de agentes e skills em `.agents/skills/` e `.claude/skills/`.
- **Governança e Estado**: Diretório `.sintetica/` com `state.json`, `install-manifest.json` e políticas de privacidade.
- **Modelo de Entrevista do Utilizador**:
  - Criação imediata do diretório do dataset (`datasets/<slug>/seeds/`) antes das perguntas.
  - Elicitação sem jargões (coleta objetivo, formato e volume sem exigir parâmetros de baixo nível).
  - Dois modos de execução: **Guiado** (passo a passo com confirmações) e **Expresso** (entrevista única upfront até a geração).
  - Tolerância a incertezas com selo `🟡 [INDEFINIDO]` para respostas "não sei".
- **Runtime e Engenharia Python**:
  - Gerenciador de pacotes e runtime: `uv` com `pyproject.toml`.
  - Padrões de código: Clean Architecture, OOP, tipagem estrita com `mypy`, formatação/lint com `ruff`.
  - Modelagem e Contratos: `Pydantic` v2 para schemas de dados sintéticos e validação estrutural.
  - Concorrência: `asyncio` para geração em lote de alta vazão.
  - Testes: `pytest` com alta cobertura.

### 2. Pipeline de Agentes do Framework Sintetica
1. `sintetica-start`: Orquestrador principal da entrevista de intenção.
2. `sintetica-schema`: Tradução dos requisitos em modelos estruturados Pydantic.
3. `sintetica-sample`: Geração de pequena amostra (3 a 5 registros) para aprovação visual.
4. `sintetica-generate`: Motor de geração em lote concorrente.
5. `sintetica-eval`: Verificador de qualidade, diversidade e ausência de dados sensíveis (PII).

### 3. Protocolo de Coordenação (Claude Code + Antigravity)
- **Executor Principal**: Claude Code conduz o pipeline `/reversa-new` e gera os artefatos.
- **Revisor e Auditor**: Antigravity revisa os artefatos gerados, valida contratos e responde dúvidas.
- **Canal de Dúvidas**: Qualquer dúvida ou decisão técnica deve ser registrada em `_reversa_sdd/questions.md` (`answer_mode: file`).

## Problema
🟡 Faltam dados sintéticos estruturados e rotulados. A falta aparece em três frentes: fine-tuning de LLMs, testes funcionais de software e validação de sistemas com dados tabulares ou conversacionais.
🟡 Dados reais são escassos, caros ou contêm PII.
🟡 Hoje, gerar dados sintéticos exige scripts ad hoc e parâmetros de baixo nível.
🟡 Quem sente: times que treinam, testam ou avaliam modelos e sistemas.
🟡 Quando sente: no início de um projeto de fine-tuning, avaliação ou teste.

## Valor entregue
🟡 O usuário descreve o dataset em linguagem natural durante uma entrevista guiada. Ele recebe, dentro do próprio harness de IA, o lote sintético gerado e validado por schemas Pydantic, com conformidade de tipos e métricas de qualidade.

## Alternativas existentes
🟡 **Faker:** gera valores falsos por campo. Exige código e não captura intenção semântica.
🟡 **SDV:** modela dados tabulares a partir de dados reais. Exige código, dados de origem e configuração de hiperparâmetros.
🟡 **Gretel:** serviço externo. Exige configuração e envia dados para fora do ambiente local.
🟡 **distilabel:** pipelines de dados sintéticos para LLM. Exige programação de pipeline.
🟡 **Scripts manuais com LLM:** sem validação de schema, sem controle de PII e sem reprodutibilidade.
🟡 **Lacuna comum:** nenhuma alternativa roda como skill conversacional nativa de harness, com entrevista guiada, validação contínua e tolerância a incertezas.

## Público-alvo (bruto)
🟡 Desenvolvedores de software, engenheiros de Machine Learning e analistas de dados. Eles usam assistentes de IA (Claude Code, Antigravity, Cursor, Gemini CLI, Codex) e precisam produzir dados sintéticos sob demanda sem programar geradores manuais.

## Métricas de sucesso
🟡 **Tempo da ideia ao dataset validado:** média < 10 minutos, para lotes de teste.
🟡 **Conformidade com schema Pydantic:** ≥ 95% dos registros gerados.
🟡 **Vazamento de PII:** 0 ocorrências detectadas pelo `sintetica-eval`.
🟡 Horizonte: 3 meses. Volume de "lote de teste" ainda não definido: 🟡 [INDEFINIDO, validar com usuário].

## Premissas a validar
🟡 1. **Qualidade da geração via LLM do harness:** a diversidade e a qualidade bastam para uso real.
   Mitigação: amostra inicial de 3 a 5 registros (`sintetica-sample`) e verificação semântica no `sintetica-eval`.
🟡 2. **Detecção local de PII:** é possível detectar PII com confiança sem serviço externo.
   Mitigação: sanitização local com regras heurísticas leves e bibliotecas locais (ex.: Faker para mascaramento e substituição).
🟡 3. **Formato único de skill:** os harnesses alvo aceitam o mesmo formato de skill sem adaptação por engine.
   Mitigação: distribuição pela especificação universal de Agent Skills (`.agents/skills/` e `.claude/skills/`).

## Notas
🟡 **Referências de padrão (Q7):**
- `reversa`: referência mestre de orquestração multiagente. Instalado neste projeto em `.reversa/` e `.claude/skills/`.
- `@sandeco/itsfine`: referência local em `/Volumes/SSD-EXTERNO/itsfine-lab`.
- `mira-animator`: pacote npm. Princípio adotado: **Criação Imediata de Diretório**. A pasta do dataset é criada e o caminho absoluto é exibido no início da entrevista.
🟡 **Tensão a resolver no PRD:** a métrica "zero vazamento de PII" depende de detecção heurística local (premissa 2). Uma heurística não garante zero. O PRD deve definir o critério de "vazamento detectado".
🟡 **Tensão a resolver no PRD:** o motor de geração (`sintetica-generate`) usa `asyncio` em Python. A fonte do LLM ainda não está definida: o próprio harness ou uma API chamada pelo runtime Python. 🟡 [INDEFINIDO, validar com usuário].
🟡 **Protocolo de coordenação:** Claude Code executa. Antigravity revisa. Dúvidas ficam em `_reversa_sdd/questions.md`.

---
Gerado por reversa-ideator em 2026-10-09T16:20:00Z
Fonte: newproject-brief.md, questions.md (Etapa 1, respostas do revisor Antigravity)
