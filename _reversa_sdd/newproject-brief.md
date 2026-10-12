# Brief inicial, /reversa-new

> Selo 🟡 PLANEJADO. Documento de entrada do time Code New Project Agents.

**Data:** 2026-10-09T17:07:00Z  
**Usuário:** George  

## Ideia original

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

---
Gerado para coordenação /reversa-new em 2026-10-09T17:07:00Z
