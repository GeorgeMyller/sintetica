# Spec: cli-installer

> Selo 🟡 PLANEJADO em todos os itens. Fonte: `prd.md` (seções 4, 6, 7 e 9), `questions.md` (Q15, Q17, Q18, Q21, Q22).

**Versão:** 1.0
**Status:** Rascunho
**Autor:** reversa-spec-sdd
**Data:** 2026-10-09
**Reviewers:** Antigravity (revisor do pipeline)

---

## 1. Resumo

🟡 O `cli-installer` é o pacote Node.js que o usuário executa com `npx sintetica install`. Ele detecta os harnesses de IA do projeto, injeta as 5 skills do sintetica e cria o diretório de governança `.sintetica/`. É o primeiro passo da jornada das 3 personas.

---

## 2. Contexto e Motivação

**Problema:**
🟡 O sintetica funciona como skill dentro de harnesses (Claude Code, Antigravity, Cursor, Gemini CLI, Codex). Sem um instalador, o usuário precisa copiar pastas de skills à mão para cada harness e criar os arquivos de governança sozinho.

**Evidências:**
🟡 O padrão de referência (`reversa`, instalado neste projeto) usa um instalador `npx` que injeta skills em `.agents/skills/` e `.claude/skills/`. O PRD exige o mesmo padrão (seção 4, "Distribuição e instalação").

**Por que agora:**
🟡 Todas as outras specs dependem das skills instaladas e de `.sintetica/policy.json`. O instalador é pré-requisito do MVP.

---

## 3. Goals (Objetivos)

- [ ] 🟡 G-01: Instalar o sintetica em um projeto com um único comando, em ≤ 30 s, sem contar o download do pacote npm.
- [ ] 🟡 G-02: Deixar as 5 skills disponíveis em 100% dos harnesses detectados.
- [ ] 🟡 G-03: Criar `.sintetica/` com a política de privacidade padrão (Q15, Q17, Q21).
- [ ] 🟡 G-04: Nunca sobrescrever arquivo pré-existente do usuário sem confirmação explícita.

**Métricas de sucesso:**
| Métrica | Baseline atual | Target | Prazo |
|---------|---------------|--------|-------|
| 🟡 Tempo de instalação (sem download) | 🟡 não existe instalador | 🟡 ≤ 30 s | 🟡 MVP |
| 🟡 Harnesses detectados com skills injetadas | 🟡 0% | 🟡 100% | 🟡 MVP |
| 🟡 Arquivos do usuário sobrescritos sem confirmação | 🟡 não se aplica | 🟡 0 | 🟡 MVP |

---

## 4. Non-Goals (Fora do Escopo)

- 🟡 NG-01: O instalador não instala Python, `uv` nem Node.js. Ele apenas verifica as versões e avisa.
- 🟡 NG-02: Não há instalação global (`npm install -g`). O alvo é sempre o diretório do projeto atual.
- 🟡 NG-03: Não há telemetria de instalação. Nenhum dado sai da máquina (Q15).
- 🟡 NG-04: Não há interface gráfica. Toda a interação ocorre no terminal (PRD, não-objetivo 1).
- 🟡 NG-05: Comando de desinstalação fica fora desta versão. O `install-manifest.json` registra os arquivos para uma remoção futura.

---

## 5. Usuários e Personas

**Usuário primário:** 🟡 As 3 personas do PRD (`dev-de-testes`, `engenheiro-de-ml`, `analista-de-dados`). Todas executam o instalador na raiz do próprio projeto.
**Usuário secundário:** 🟡 Os agentes dos harnesses, que leem as skills injetadas.

**Jornada atual (sem a feature):**
1. 🟡 O usuário procura as skills em um repositório.
2. 🟡 Copia as pastas para cada harness à mão.
3. 🟡 Cria a configuração de privacidade sozinho, ou não cria.

**Jornada futura (com a feature):**
1. 🟡 O usuário executa `npx sintetica install` na raiz do projeto.
2. 🟡 O instalador mostra os harnesses detectados e os caminhos criados.
3. 🟡 O usuário executa `/sintetica-start` no harness.

---

## 6. Requisitos Funcionais

### 6.1 Requisitos Principais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | 🟡 O sistema deve verificar a versão do Node.js e abortar se ela for menor que 18.0.0 (Q18). | Must | 🟡 Com Node.js 16, o comando termina com código de saída 1 e mostra a versão encontrada e a mínima. |
| RF-02 | 🟡 O sistema deve detectar harnesses pelos marcadores do projeto: `.claude/` (Claude Code), `.agents/` ou `.agent/` (Antigravity), `.cursor/` (Cursor), `.gemini/` (Gemini CLI), `.codex/` ou `AGENTS.md` (Codex). | Must | 🟡 Com `.claude/` e `.cursor/` presentes, o resumo lista exatamente Claude Code e Cursor. |
| RF-03 | 🟡 O sistema deve copiar as skills `sintetica-start`, `sintetica-schema`, `sintetica-sample`, `sintetica-generate` e `sintetica-eval` para `.agents/skills/<skill>/` e `.claude/skills/<skill>/`. | Must | 🟡 Após a instalação, as 10 pastas existem e cada uma contém `SKILL.md`. |
| RF-04 | 🟡 O sistema deve criar `.sintetica/state.json`, `.sintetica/install-manifest.json` e `.sintetica/policy.json`. | Must | 🟡 Os 3 arquivos existem e são JSON válido. |
| RF-05 | 🟡 O sistema deve registrar em `install-manifest.json` cada arquivo criado, com caminho relativo e hash SHA-256. | Must | 🟡 O número de entradas do manifest é igual ao número de arquivos criados. |
| RF-06 | 🟡 O sistema deve gravar em `policy.json` os valores padrão: `telemetry: false`, `pii_premask: true`, `cost_ceiling_usd: 5.00`, `provider_priority: ["harness", "ollama", "external"]`, `pii_custom_patterns: []`. | Must | 🟡 O conteúdo de `policy.json` é igual ao padrão definido neste requisito. |
| RF-07 | 🟡 O sistema deve pedir confirmação `sim/não` antes de sobrescrever qualquer arquivo que já exista e não conste no manifest. | Must | 🟡 Com `.claude/skills/sintetica-start/SKILL.md` criado pelo usuário, o instalador pergunta e, com resposta `não`, mantém o arquivo intacto. |
| RF-08 | 🟡 O sistema deve verificar Python ≥ 3.10 e `uv` no PATH. Se faltar algum, o sistema deve concluir a instalação das skills, gravar `runtime_ready: false` em `state.json` e mostrar o comando de instalação recomendado. | Must | 🟡 Sem `uv` no PATH, o código de saída é 0, `runtime_ready` é `false` e o aviso aparece. |
| RF-09 | 🟡 O sistema deve ser idempotente: uma segunda execução sem mudanças não altera nenhum arquivo. | Should | 🟡 Os hashes do manifest são iguais antes e depois da segunda execução. |
| RF-10 | 🟡 O sistema deve mostrar um resumo final com harnesses detectados, caminhos absolutos criados e o próximo comando (`/sintetica-start`). | Must | 🟡 O resumo contém as 3 informações. |
| RF-11 | 🟡 O sistema deve aceitar a flag `--yes` para responder `sim` a todas as confirmações, sem nunca sobrescrever `policy.json` já existente. | Could | 🟡 Com `--yes` e `policy.json` editado pelo usuário, o arquivo continua com o conteúdo do usuário. |

### 6.2 Fluxo Principal (Happy Path)

1. 🟡 O usuário executa `npx sintetica install` na raiz do projeto.
2. 🟡 O sistema verifica Node.js ≥ 18.0.0.
3. 🟡 O sistema detecta os harnesses pelos marcadores.
4. 🟡 O sistema copia as 5 skills para `.agents/skills/` e `.claude/skills/`.
5. 🟡 O sistema cria `.sintetica/` com os 3 arquivos.
6. 🟡 O sistema verifica Python e `uv` e grava `runtime_ready` em `state.json`.
7. 🟡 Resultado: o sistema mostra o resumo e termina com código de saída 0.

### 6.3 Fluxos Alternativos

**Fluxo Alternativo A — Nenhum harness detectado:**
1. 🟡 O sistema não encontra nenhum marcador.
2. 🟡 O sistema instala nos 2 destinos padrão (`.agents/skills/` e `.claude/skills/`) e avisa que nenhum harness foi detectado.

**Fluxo Alternativo B — Reinstalação com versão nova:**
1. 🟡 O manifest existe e aponta para uma versão anterior do sintetica.
2. 🟡 O sistema substitui apenas os arquivos listados no manifest e atualiza os hashes.

---

## 7. Requisitos Não-Funcionais

| ID | Requisito | Valor alvo | Observação |
|----|-----------|-----------|------------|
| RNF-01 | 🟡 Runtime do instalador | 🟡 Node.js ≥ 18.0.0 | 🟡 Q18 |
| RNF-02 | 🟡 Desempenho | 🟡 ≤ 30 s sem download | 🟡 Disco local |
| RNF-03 | 🟡 Privacidade | 🟡 0 chamadas de rede além do download do npm | 🟡 Q15 |
| RNF-04 | 🟡 Portabilidade | 🟡 macOS, Linux e Windows | 🟡 Caminhos com separador do sistema |
| RNF-05 | 🟡 Cobertura de testes | 🟡 ≥ 80% de linhas | 🟡 Q19 adaptada ao Node.js. Ver OQ-02 |

---

## 8. Design e Interface

**Componentes afetados:** 🟡 Comando `npx sintetica install`, pastas `.agents/skills/`, `.claude/skills/` e `.sintetica/`.

**Comportamento esperado:**
🟡 Saída de texto no terminal, uma linha por etapa, com prefixo `✓` (concluída), `!` (aviso) ou `✗` (erro).

**Estados da UI:**
- 🟡 Estado vazio: nenhum harness detectado. O sistema mostra o aviso do fluxo alternativo A.
- 🟡 Estado de carregamento: o sistema mostra a etapa atual (ex.: "Copiando skills…").
- 🟡 Estado de erro: o sistema mostra a causa e a ação corretiva, e termina com código 1.
- 🟡 Estado de sucesso: o sistema mostra o resumo do RF-10.

---

## 9. Modelo de Dados

```
InstallManifest {
  sintetica_version: string      // versão do pacote instalado
  installed_at: string           // ISO 8601
  files: list<{ path: string, sha256: string }>
}

State {
  version: string
  harnesses: list<string>        // ex.: ["claude-code", "cursor"]
  runtime_ready: boolean         // Python ≥ 3.10 e uv presentes
}

Policy {
  telemetry: boolean             // padrão false
  pii_premask: boolean           // padrão true (Q21)
  cost_ceiling_usd: number       // padrão 5.00 (Q17)
  provider_priority: list<string>
  pii_custom_patterns: list<string>
}
```

**Migrações necessárias:** 🟡 Não. Primeira versão.

---

## 10. Integrações e Dependências

| Dependência | Tipo | Impacto se indisponível |
|-------------|------|------------------------|
| 🟡 Registro npm | 🟡 Obrigatória | 🟡 `npx` falha antes do instalador rodar. Mensagem do próprio npm. |
| 🟡 Node.js ≥ 18 | 🟡 Obrigatória | 🟡 Aborta com código 1 (RF-01). |
| 🟡 Python ≥ 3.10 e `uv` | 🟡 Opcional na instalação | 🟡 Instala as skills e grava `runtime_ready: false` (RF-08). |

---

## 11. Edge Cases e Tratamento de Erros

| Cenário | Trigger | Comportamento esperado |
|---------|---------|----------------------|
| 🟡 EC-01: Sem permissão de escrita | 🟡 Diretório somente leitura | 🟡 O sistema aborta com código 1 e mostra o caminho sem permissão. Nenhum arquivo parcial permanece. |
| 🟡 EC-02: Falha no meio da cópia | 🟡 Disco cheio ou processo interrompido | 🟡 O sistema remove os arquivos criados nesta execução (rollback pelo manifest temporário) e termina com código 1. |
| 🟡 EC-03: Arquivo do usuário com mesmo nome | 🟡 Skill homônima criada pelo usuário | 🟡 O sistema pede confirmação (RF-07). Resposta `não` mantém o arquivo e pula essa skill com aviso. |
| 🟡 EC-04: `policy.json` inválido em reinstalação | 🟡 JSON corrompido | 🟡 O sistema renomeia para `policy.json.bak` e grava a política padrão, com aviso. |
| 🟡 EC-05: Diretório fora de projeto | 🟡 Execução em `$HOME` ou `/` | 🟡 O sistema pede confirmação explícita antes de continuar. |

---

## 12. Segurança e Privacidade

- 🟡 **Autenticação:** não se aplica. Execução local pelo usuário do sistema operacional.
- 🟡 **Autorização:** usa as permissões de arquivo do usuário atual.
- 🟡 **Dados sensíveis:** o instalador não lê nem grava chaves de API.
- 🟡 **Auditoria:** o `install-manifest.json` é o registro do que foi criado.

---

## 13. Plano de Rollout

- 🟡 **Estratégia:** publicação no npm com versão semântica, começando em `0.1.0`.
- 🟡 **Como reverter (rollback):** o usuário apaga os arquivos listados em `install-manifest.json`. Uma versão com defeito é marcada com `npm deprecate`.
- 🟡 **Monitoramento pós-deploy:** issues no repositório. Não há telemetria (NG-03).

---

## 14. Open Questions

| # | Pergunta | Impacto | Dono | Prazo |
|---|---------|---------|------|-------|
| OQ-01 | 🟡 Os marcadores de harness do RF-02 estão corretos para Antigravity e Codex? | 🟡 Médio | 🟡 Antigravity | 🟡 Antes do `/reversa-plan` |
| OQ-02 | 🟡 Qual ferramenta mede a cobertura do código Node.js (ex.: `c8`)? A Q19 cita só `pytest-cov`. | 🟡 Baixo | 🟡 Antigravity | 🟡 Antes do `/reversa-plan` |

---

## 15. Decisões Tomadas (Decision Log)

| Decisão | Alternativas consideradas | Racional |
|---------|--------------------------|---------|
| 🟡 Instalar sempre em `.agents/skills/` e `.claude/skills/` | 🟡 Um destino por harness | 🟡 PRD, premissa 3: formato universal de Agent Skills. |
| 🟡 Ausência de Python ou `uv` gera aviso, não erro | 🟡 Abortar a instalação | 🟡 O `HarnessAgentProvider` gera amostras sem runtime Python. |
| 🟡 Política padrão restritiva | 🟡 API externa como padrão | 🟡 Q15 e Q21: privacidade por design. |

---

## Apêndice

### Referências
- 🟡 `../prd.md`, seções 4, 6, 7 e 9.
- 🟡 `../questions.md`, Q15, Q17, Q18, Q19, Q21, Q22.

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
