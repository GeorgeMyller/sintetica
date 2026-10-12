# Requirements: cli-installer (instalador `npx sintetica install`)

> Identificador: `008-cli-installer`
> Data: `2026-10-12`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA
> Cenário: greenfield. Fontes planejadas, mais os adendos vigentes `addenda/001-pii-guard.md` a `addenda/007-quality-evaluator.md`, que descrevem código entregue.

## 1. Resumo executivo

🟡 O `cli-installer` é o pacote Node.js que o usuário roda com `npx sintetica install` na raiz do próprio projeto.
🟡 Ele detecta os harnesses de IA, instala as 5 skills do sintetica (`sintetica-start`, `sintetica-schema`, `sintetica-sample`, `sintetica-generate`, `sintetica-eval`) e cria a pasta de governança `.sintetica/` com a política de privacidade padrão.
🟡 Ele verifica o runtime Python (Python ≥ 3.10 e `uv`) e avisa quando falta, sem bloquear a instalação das skills.
🟡 Esta feature também escreve o conteúdo das 5 skills (`SKILL.md`). As features 003 a 007 deixaram as skills de fora e documentaram o fluxo em `docs/`.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/sdd/cli-installer.md#6. Requisitos Funcionais` | RF-01 a RF-11: versão do Node, detecção de harnesses, cópia das skills, `.sintetica/`, manifest com SHA-256, política padrão, confirmação antes de sobrescrever, verificação de Python e `uv`, idempotência, resumo, `--yes` | 🟡 |
| `_reversa_sdd/sdd/cli-installer.md#11. Edge Cases e Tratamento de Erros` | Sem permissão, falha no meio da cópia com rollback, arquivo do usuário com o mesmo nome, `policy.json` inválido, diretório fora de projeto | 🟡 |
| `_reversa_sdd/sdd/cli-installer.md#9. Modelo de Dados` | `InstallManifest`, `State`, `Policy` | 🟡 |
| `_reversa_sdd/prd.md#4. Escopo (in)` | Distribuição por `npx`; skills em `.agents/skills/` e `.claude/skills/` no formato universal; runtime Python com `uv` | 🟡 |
| `_reversa_sdd/questions.md#Q15`, `#Q17`, `#Q18`, `#Q19`, `#Q21` | Sem telemetria; teto de US$ 5,00; Node ≥ 18 e Python ≥ 3.10; cobertura ≥ 80%; mascaramento antes de API externa | 🟡 |
| `_reversa_sdd/addenda/001-pii-guard.md#Impacto por artefato da extração` | `pii_custom_patterns` em `.sintetica/policy.json`, até 200 caracteres por padrão | 🟢 |
| `_reversa_sdd/addenda/002-llm-provider.md#Impacto por artefato da extração` | `pii_premask`, `cost_ceiling_usd` e `provider_priority` lidos de `.sintetica/policy.json`; preços em `.sintetica/pricing.json` | 🟢 |
| `_reversa_sdd/addenda/004-intent-interview.md` a `addenda/007-quality-evaluator.md` | Comandos do runtime que as skills chamam: `start`, `intent`, `schema`, `sample`, `request`, `submit`, `generate`, `status`, `eval`; fluxos documentados em `docs/*.md` | 🟢 |

> As 3 últimas linhas recebem 🟢 porque descrevem código entregue nas features 001 a 007.

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| `dev-de-testes` | Começar em poucos minutos | 🟡 Roda `npx sintetica install` e depois `/sintetica-start` no Claude Code. |
| `engenheiro-de-ml` | Usar no projeto de fine-tuning, com Cursor e Claude Code | 🟡 Vê os 2 harnesses detectados e as skills instaladas uma vez para os 2. |
| `analista-de-dados` | Instalar sem Python configurado | 🟡 Recebe as skills, o aviso de runtime ausente e o comando para instalar o `uv`. |
| Agente do harness | Encontrar e seguir as skills | 🟡 Lê `SKILL.md` e chama os comandos do runtime na ordem certa. |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** 🟡 O instalador só roda com Node.js ≥ 18.0.0; abaixo disso, termina com código 1 e mostra a versão encontrada e a mínima.
   - Origem: `_reversa_sdd/sdd/cli-installer.md#6` (RF-01), `_reversa_sdd/questions.md#Q18`
   - Tipo: nova
2. **RN-02:** 🟡 O instalador detecta os harnesses pelos marcadores: Claude Code `.claude/`; Antigravity `.agents/` ou `.agent/`; Cursor `.cursor/`; Gemini CLI `.gemini/`; Codex `.codex/` ou `AGENTS.md`. A detecção só informa o resumo e `state.json`. As 5 skills vão sempre para os destinos universais `.agents/skills/` e `.claude/skills/`, com qualquer harness detectado ou nenhum.
   - Origem: `#6` (RF-02, RF-03), `#6.3` (Fluxo A), `#14` (OQ-01), `_reversa_sdd/prd.md#4`, `_reversa_sdd/questions.md#Q51`
   - Tipo: nova
3. **RN-03:** 🟡 O instalador nunca sobrescreve um arquivo do usuário sem confirmação. Arquivo que já existe e não consta no manifest exige `sim/não`; resposta `não` mantém o arquivo e pula a skill com aviso. `--yes` responde `sim`, mas nunca sobrescreve `policy.json` existente.
   - Origem: `#6` (RF-07, RF-11), `#11` (EC-03), `#3` (G-04)
   - Tipo: nova
4. **RN-04:** 🟡 `.sintetica/policy.json` nasce com a política padrão: `telemetry: false`, `pii_premask: true`, `cost_ceiling_usd: 5.00`, `provider_priority: ["harness", "ollama", "external"]`, `pii_custom_patterns: []`. A política lida pelo runtime Python (features 001 e 002) aceita esse arquivo sem ajuste. `policy.json` inválido numa reinstalação vira `policy.json.bak` e a padrão é gravada, com aviso.
   - Origem: `#6` (RF-06), `#11` (EC-04), `addenda/001-pii-guard.md`, `addenda/002-llm-provider.md`, Q15, Q17, Q21
   - Tipo: nova
5. **RN-05:** 🟡 Cada arquivo criado entra em `.sintetica/install-manifest.json` com caminho relativo e SHA-256. Uma reinstalação substitui só os arquivos do manifest que não foram editados; uma 2ª execução sem mudanças não altera nenhum arquivo.
   - Origem: `#6` (RF-05, RF-09), `#6.3` (Fluxo B), `#9`
   - Tipo: nova
6. **RN-06:** 🟡 O pacote npm leva o pacote Python `sintetica` pronto (wheel da mesma versão). O instalador copia o wheel para `.sintetica/runtime/` e cria o lançador `.sintetica/bin/sintetica` (e `sintetica.cmd` no Windows), que roda `uvx --from <wheel> sintetica`; sem o wheel (ambiente de desenvolvimento), o lançador usa `uv run sintetica`. As skills chamam o lançador; o `pyproject.toml` do usuário não muda. A falta de Python ≥ 3.10 ou de `uv` não bloqueia a instalação: grava `runtime_ready: false` em `state.json` e mostra o comando de instalação.
   - Origem: `#6` (RF-08), `#4` (NG-01), `#15`, `_reversa_sdd/prd.md#4` (Runtime Python), `addenda/004-intent-interview.md` a `addenda/007-quality-evaluator.md`, `_reversa_sdd/questions.md#Q50`
   - Tipo: nova
7. **RN-07:** 🟡 Falha no meio da instalação desfaz os arquivos criados nesta execução e termina com código 1; nenhum arquivo parcial fica no projeto.
   - Origem: `#11` (EC-01, EC-02)
   - Tipo: nova
8. **RN-08:** 🟡 Fora de um projeto (`$HOME` ou raiz do sistema), o instalador pede confirmação explícita antes de continuar.
   - Origem: `#11` (EC-05)
   - Tipo: nova
9. **RN-09:** 🟡 O instalador não faz nenhuma chamada de rede e não lê nem grava chaves de API.
   - Origem: `#4` (NG-03), `#7` (RNF-03), `#12`, Q15
   - Tipo: nova
10. **RN-10:** 🟡 As 5 skills seguem o formato universal de Agent Skills e instruem o agente com os comandos do runtime entregues nas features 004 a 007, na ordem do pipeline, incluindo o protocolo `request`/`submit` do harness (Q29) e os códigos de saída de cada comando.
    - Origem: `_reversa_sdd/prd.md#4` (Pipeline de agentes), `docs/intent-interview.md`, `docs/schema-builder.md`, `docs/sample-preview.md`, `docs/batch-generator.md`, `docs/quality-evaluator.md`
    - Tipo: nova
11. **RN-11:** 🟡 O instalador é JavaScript em módulos ES, com tipos em JSDoc verificados por `tsc --checkJs --strict`, testes com o `node:test` embutido e cobertura ≥ 80% medida pelo `c8`. Não há dependências de produção; `typescript`, `c8` e `@types/node` são só de desenvolvimento.
    - Origem: `#7` (RNF-05), `#14` (OQ-02), `_reversa_sdd/questions.md#Q19`, `#Q52`
    - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O sistema deve verificar a versão do Node.js pela RN-01. | Must | Com versão 16 simulada, o código de saída é 1 e a saída mostra 16 e 18.0.0. | 🟡 |
| RF-02 | O sistema deve detectar os harnesses pela RN-02, listá-los no resumo e gravá-los em `state.json`. | Must | Com `.claude/` e `.cursor/` presentes, o resumo e `state.json` listam exatamente Claude Code e Cursor. | 🟡 |
| RF-03 | O sistema deve instalar as 5 skills em `.agents/skills/<skill>/` e `.claude/skills/<skill>/`. | Must | Após a instalação, as 10 pastas existem e cada uma tem `SKILL.md`. | 🟡 |
| RF-04 | O sistema deve criar `.sintetica/state.json`, `install-manifest.json` e `policy.json` como JSON válido. | Must | Os 3 arquivos existem e são JSON válido. | 🟡 |
| RF-05 | O sistema deve registrar cada arquivo criado no manifest pela RN-05. | Must | O número de entradas do manifest é igual ao de arquivos criados. | 🟡 |
| RF-06 | O sistema deve gravar a política padrão pela RN-04, aceita pelo runtime Python. | Must | `policy.json` é igual ao padrão; o runtime lê o arquivo sem erro. | 🟡 |
| RF-07 | O sistema deve pedir confirmação pela RN-03. | Must | Com um `SKILL.md` do usuário e resposta `não`, o arquivo fica intacto e a skill é pulada com aviso. | 🟡 |
| RF-08 | O sistema deve instalar o wheel e o lançador e verificar Python e `uv` pela RN-06. | Must | Sem `uv` no PATH, o código é 0, `runtime_ready` é `false` e o aviso traz o comando de instalação; com `uv`, `.sintetica/bin/sintetica --help` roda o runtime. | 🟡 |
| RF-09 | O sistema deve ser idempotente pela RN-05. | Should | Os hashes e as datas de modificação são iguais antes e depois da 2ª execução. | 🟡 |
| RF-10 | O sistema deve mostrar o resumo final com harnesses, caminhos absolutos e o próximo comando (`/sintetica-start`), com prefixos `✓`, `!` e `✗`. | Must | O resumo tem as 3 informações. | 🟡 |
| RF-11 | O sistema deve aceitar `--yes` pela RN-03. | Could | Com `--yes` e `policy.json` editado, o conteúdo do usuário continua. | 🟡 |
| RF-12 | O sistema deve desfazer a instalação parcial pela RN-07. | Must | Com falha simulada na 3ª cópia, nenhum arquivo novo permanece e o código é 1. | 🟡 |
| RF-13 | O sistema deve pedir confirmação fora de projeto pela RN-08. | Must | Em `$HOME`, sem confirmação, nada é criado. | 🟡 |
| RF-14 | O sistema deve trocar `policy.json` inválido pela padrão, guardando o antigo em `policy.json.bak`. | Must | Com `policy.json` corrompido, o `.bak` guarda o conteúdo antigo e o novo é o padrão. | 🟡 |
| RF-15 | O pacote deve conter as 5 skills com o conteúdo da RN-10, chamando o lançador `.sintetica/bin/sintetica`. | Must | Cada `SKILL.md` tem nome, descrição e os comandos do runtime da sua etapa; um teste confere que todo comando citado existe na CLI Python. | 🟡 |
| RF-16 | As mensagens do runtime Python que citam um comando devem usar o comando de quem chamou: o lançador informa o próprio caminho, e o padrão continua `uv run sintetica`. | Must | Pelo lançador, a mensagem de retomada do lote cita `.sintetica/bin/sintetica generate <slug> --resume`; pelo `uv run`, cita `uv run sintetica`. | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | Instalação em ≤ 30 s, sem contar o download do pacote. | `_reversa_sdd/sdd/cli-installer.md#7` (RNF-02) | 🟡 |
| Privacidade | 0 chamadas de rede; sem telemetria; sem chaves de API. | `#7` (RNF-03), Q15 | 🟡 |
| Portabilidade | macOS, Linux e Windows, com caminhos pelo separador do sistema. | `#7` (RNF-04) | 🟡 |
| Runtime | Node.js ≥ 18.0.0, sem dependências de produção além da biblioteca padrão do Node. | Q18; reduz a superfície de instalação | 🟡 |
| Qualidade | `tsc --checkJs --strict` sem erros e cobertura ≥ 80% de linhas pelo `c8` (RN-11). | `#7` (RNF-05), Q19, Q52 | 🟡 |
| Testabilidade | Toda a suíte roda sem rede, em diretórios temporários, com o PATH e a versão do Node simulados. | Padrão das features 001 a 007 | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Instalação limpa com Claude Code e Cursor
  Dado um projeto com .claude/ e .cursor/
  Quando o usuário roda npx sintetica install
  Então o resumo lista Claude Code e Cursor
  E as 5 skills existem em .agents/skills/ e .claude/skills/
  E .sintetica/ tem state.json, install-manifest.json e policy.json
  E o código de saída é 0

Cenário: Node.js antigo
  Dado o Node.js 16
  Quando o usuário roda o instalador
  Então o código de saída é 1 e a saída mostra a versão encontrada e a mínima
  E nenhum arquivo é criado

Cenário: Nenhum harness detectado
  Dado um projeto sem marcadores de harness
  Quando o usuário roda o instalador
  Então as skills são instaladas nos 2 destinos padrão
  E o resumo avisa que nenhum harness foi detectado

Cenário: Política padrão aceita pelo runtime
  Dado uma instalação concluída
  Quando o runtime Python lê .sintetica/policy.json
  Então a leitura não dá erro e o teto de custo é 5.00

Cenário: Manifest completo
  Dado uma instalação concluída
  Quando o manifest é lido
  Então cada arquivo criado aparece com caminho relativo e SHA-256 correto

Cenário: Arquivo do usuário com o mesmo nome
  Dado um .claude/skills/sintetica-start/SKILL.md criado pelo usuário
  Quando o instalador pergunta e o usuário responde não
  Então o arquivo do usuário fica intacto e a skill é pulada com aviso

Cenário: --yes preserva a política do usuário
  Dado um policy.json editado pelo usuário
  Quando o instalador roda com --yes
  Então policy.json mantém o conteúdo do usuário

Cenário: Runtime Python ausente
  Dado um PATH sem uv
  Quando o usuário roda o instalador
  Então o código de saída é 0
  E state.json tem runtime_ready false
  E a saída mostra o comando de instalação

Cenário: Segunda execução sem mudanças
  Dado uma instalação concluída
  Quando o instalador roda de novo
  Então nenhum arquivo muda

Cenário: Reinstalação com versão nova
  Dado um manifest de uma versão anterior
  Quando o instalador da versão nova roda
  Então só os arquivos do manifest são substituídos e os hashes são atualizados

Cenário: Falha no meio da cópia
  Dado uma falha de escrita na 3ª cópia
  Quando o instalador roda
  Então os arquivos criados nesta execução são removidos e o código é 1

Cenário: Sem permissão de escrita
  Dado um diretório somente leitura
  Quando o instalador roda
  Então o código é 1 e a saída mostra o caminho sem permissão

Cenário: policy.json corrompido
  Dado um policy.json com JSON inválido
  Quando o instalador roda
  Então o conteúdo antigo vai para policy.json.bak e a política padrão é gravada, com aviso

Cenário: Execução fora de projeto
  Dado o diretório $HOME
  Quando o instalador roda sem confirmação
  Então nada é criado

Cenário: Lançador do runtime
  Dado uma instalação concluída com uv no PATH
  Quando o agente roda .sintetica/bin/sintetica --help
  Então o runtime Python responde pelo wheel instalado
  E o pyproject.toml do usuário não muda

Cenário: Mensagens citam o lançador
  Dado o runtime chamado pelo lançador
  Quando um comando sugere outro comando na saída
  Então a sugestão começa com .sintetica/bin/sintetica

Cenário: Skills citam comandos que existem
  Dado as 5 skills do pacote
  Quando cada comando sintetica citado é conferido na CLI Python
  Então todos existem
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-03 a RF-07, RF-10, RF-12 a RF-15 | Must | Instalação segura e skills utilizáveis. |
| RF-02 | Must | RN-02 (OQ-01, Q51). |
| RF-08, RF-16 | Must | RN-06 (Q50): sem o runtime, as skills não funcionam. |
| RF-09 | Should | A spec marca como Should. |
| RF-11 | Could | A spec marca como Could. |

## 9. Esclarecimentos

### Sessão 2026-10-12

> Respostas do Antigravity em `_reversa_sdd/questions.md` (Etapa 14).

- **Q:** Como o runtime Python chega ao projeto do usuário? (Q50)
  **R:** Wheel dentro do pacote npm, copiado para `.sintetica/runtime/`, e lançador `.sintetica/bin/sintetica` com `uvx --from <wheel> sintetica`; sem o wheel, `uv run sintetica` (desenvolvimento). Atualizou RN-06, RF-08 e criou RF-16.
- **Q:** Os marcadores e destinos dos harnesses estão corretos? (Q51)
  **R:** Marcadores da spec para detecção e `state.json`; destinos sempre `.agents/skills/` e `.claude/skills/`. Atualizou RN-02 e RF-02.
- **Q:** Qual linguagem, verificação estática e ferramenta de cobertura do instalador? (Q52)
  **R:** JavaScript ESM com JSDoc e `tsc --checkJs --strict`, `node:test`, `c8` e zero dependências de produção. Atualizou RN-11 e o RNF de qualidade.

## 10. Lacunas

Nenhuma dúvida aberta. As 3 dúvidas foram resolvidas pelas Q50 a Q52.

- 🟡 Fora do escopo, sem dúvida: publicar no npm; comando de desinstalação (NG-05).

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-12 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-12 | Respostas Q50 a Q52 integradas por `/reversa-clarify`: RN-02, RN-06, RN-11, RF-02, RF-08, RF-15, RF-16 novo e 2 cenários novos | reversa |
