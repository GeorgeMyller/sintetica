# Roadmap: cli-installer (instalador `npx sintetica install`)

> Identificador: `008-cli-installer`
> Data: `2026-10-12`
> Requirements: `_reversa_forward/008-cli-installer/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA
> Cenário: greenfield. Sem `architecture.md`, `c4-context.md`, `state-machines.md`, `dependencies.md` nem `code-analysis.md`. Adendos vigentes lidos: `addenda/001-pii-guard.md` a `addenda/007-quality-evaluator.md`.

## 1. Resumo da abordagem

🟡 A feature cria o pacote Node.js `installer/` (nome npm `sintetica`), em JavaScript ESM com tipos em JSDoc (Q52), sem dependências de produção. O comando `npx sintetica install` monta a lista de arquivos desejados, decide a ação de cada um (criar, pular, substituir, perguntar, preservar) e grava tudo com escrita atômica e diário de desfazer.
🟡 Os arquivos instalados são:
- as 5 skills em `.agents/skills/<skill>/SKILL.md` e `.claude/skills/<skill>/SKILL.md` (Q51);
- o wheel do runtime Python em `.sintetica/runtime/` e o lançador `.sintetica/bin/sintetica` (e `.cmd`) (Q50);
- `.sintetica/policy.json`, `state.json` e `install-manifest.json`.
🟡 O runtime Python ganha `sintetica.command`: as mensagens que citam um comando usam o prefixo de quem chamou (variável `SINTETICA_CMD`, definida pelo lançador), com `uv run sintetica` como padrão (RF-16).
🟡 O conteúdo das 5 skills sai dos `docs/*.md` das features 004 a 007. Um teste Python confere que todo comando citado existe na CLI.

## 2. Princípios aplicados

🟡 `.reversa/principles.md` não existe. Sem princípios formais para verificar.

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| n/a | Arquivo de princípios ausente | n/a |

🟡 Restrições do PRD tratadas como princípios de fato:
- nunca sobrescrever arquivo do usuário sem confirmação (G-04);
- privacidade por design: 0 chamadas de rede no instalador, sem telemetria (Q15);
- skills no formato universal, sem adaptação por engine (PRD, seção 6);
- tipagem estrita e cobertura ≥ 80% (Q19, Q52).

Todas são respeitadas.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Pasta `installer/` na raiz: `package.json` (`name: sintetica`, `type: module`, `bin`, `engines.node >= 18`, `files`), `bin/sintetica.js`, `src/*.js`, `skills/<skill>/SKILL.md`, `runtime/` (wheel gerado na publicação), `test/*.test.js`, `tsconfig.json` (`allowJs`, `checkJs`, `strict`, `noEmit`) | Q52; código publicado = código verificado | Pacote separado em outro repositório | 🟢 |
| D-02 | `bin/sintetica.js` usa só sintaxe aceita por Node antigo, confere a versão com `checkNode(process.versions.node)` e só depois importa o resto (`import()` dinâmico) | RF-01: Node 16 precisa ler o arquivo para mostrar o erro | Checar dentro de módulos ESM modernos | 🟡 |
| D-03 | Argumentos: `install [--yes] [--dir <caminho>]`; `--dir` padrão = diretório atual. Comando ausente ou desconhecido mostra a ajuda e termina com 1 | Spec §6.2; `--dir` permite testes sem `chdir` | Só o diretório atual | 🟡 |
| D-04 | Detecção pelos marcadores da Q51; resultado ordenado e gravado em `state.json` (`claude-code`, `antigravity`, `cursor`, `gemini-cli`, `codex`) | RN-02 | Detectar pelo PATH | 🟢 |
| D-05 | Plano de arquivos: lista de `{caminho, conteúdo, modo}` e, para cada um, a ação: `criar` (ausente), `igual` (mesmo SHA-256: nada a fazer), `substituir` (no manifest e sem edição), `perguntar` (existe fora do manifest, ou editado depois da instalação), `preservar` (`policy.json` válido), `recuperar` (`policy.json` inválido → `.bak` + padrão) | RN-03, RN-05, RF-09, RF-14, Fluxo B | Sobrescrever o que está no manifest mesmo editado | 🟢 |
| D-06 | Confirmação por `readline` na entrada padrão. `--yes` responde sim, exceto para `policy.json`. Sem terminal interativo e sem `--yes`, a resposta é não, com aviso que sugere `--yes`. Resposta não numa skill pula as 2 cópias daquela skill | RN-03, EC-03; o agente do harness pode rodar sem terminal | Travar esperando a entrada | 🟡 |
| D-07 | Escrita atômica (arquivo temporário no mesmo diretório e `rename`) com diário de desfazer: arquivo criado → apagar; substituído → restaurar o conteúdo antigo; `.bak` → renomear de volta. Erro → desfaz tudo, mostra o caminho e termina com 1 | RN-07, EC-01, EC-02 | Copiar direto, sem diário | 🟢 |
| D-08 | `install-manifest.json`: `{sintetica_version, installed_at, files: [{path, sha256}]}`, caminhos relativos com `/`, ordenados, sem o próprio manifest. Gravado só se o conteúdo mudar (mantém `installed_at` e a data do arquivo numa 2ª execução igual) | RN-05, RF-09 | Gravar sempre | 🟢 |
| D-09 | `state.json`: `{version, harnesses, runtime_ready}` (modelo da spec); gravado só se mudar | RF-04, RF-08 | Guardar versões de Python e `uv` | 🟡 |
| D-10 | Runtime: `uv --version` pelo `spawnSync` sem shell; Python ≥ 3.10 por `uv python find ">=3.10"` quando há `uv`, senão por `python3 --version`/`python --version`. `runtime_ready = uv e Python ok`. Sem eles, aviso `!` com o comando de instalação do `uv` para o sistema (só exibido, nunca executado) | RN-06, RN-09 | Instalar o `uv` | 🟢 |
| D-11 | Lançador `.sintetica/bin/sintetica` (sh, modo 755) e `sintetica.cmd`: definem `SINTETICA_CMD=.sintetica/bin/sintetica` e rodam `uvx --from <wheel> sintetica "$@"`; sem o wheel, `uv run sintetica "$@"` (Q50) | RN-06 | Lançador em Node | 🟢 |
| D-12 | O wheel entra no pacote pela publicação: script `build:runtime` (`uv build --wheel --out-dir installer/runtime`) no `prepack`. O instalador procura `runtime/sintetica-<versão>-*.whl`; sem ele (cópia de desenvolvimento), instala só o lançador e avisa. Teste confere que a versão do `package.json` é igual à do `pyproject.toml` | Q50; versão única | Wheel versionado no repositório | 🟡 |
| D-13 | `sintetica.command.cli_command()` lê `SINTETICA_CMD` (padrão `uv run sintetica`). As 40 mensagens com `uv run sintetica` nas features 002 a 007 passam a usar a função; sem a variável, a saída é idêntica à atual | RF-16; os testes das features anteriores continuam valendo | Pedir que a skill traduza as mensagens | 🟡 |
| D-14 | 5 skills com frontmatter `name` e `description` e corpo em passos: quando usar, comandos do lançador na ordem, protocolo `request`/`submit` (Q29) onde se aplica, códigos de saída e regras de privacidade. Fonte: `docs/*.md` das features 004 a 007 | RN-10, RF-15 | Gerar as skills no instalador | 🟡 |
| D-15 | Teste Python `tests/test_skills_commands.py`: lê `installer/skills/*/SKILL.md`, extrai cada `.sintetica/bin/sintetica <comando> [subcomando]` e confere no parser de `sintetica.cli` | RF-15 | Conferir à mão | 🟢 |
| D-16 | Fora de projeto: diretório igual a `os.homedir()` ou à raiz do sistema → pergunta; `--yes` confirma; não → nada é criado, código 1 | RN-08, EC-05 | Recusar sempre | 🟡 |
| D-17 | Saída: 1 linha por etapa com `✓`, `!` ou `✗`; resumo final com harnesses, caminhos absolutos e o próximo passo `/sintetica-start` | RF-10, spec §8 | Saída em JSON | 🟢 |
| D-18 | Ferramentas (Q52): `npm run typecheck` (`tsc -p .`), `npm test` (`node --test test/`), `npm run coverage` (`c8 --check-coverage --lines 80 node --test test/`). Dependências só de desenvolvimento: `typescript`, `c8`, `@types/node` | RN-11 | `vitest` | 🟢 |
| D-19 | Testes do runtime com executáveis falsos (`uv`, `python3`) num diretório temporário no início do `PATH`; Node antigo testado pela função `checkNode`; falha de escrita simulada por injeção do sistema de arquivos no instalador | Testabilidade sem rede | Rodar com o `uv` real | 🟡 |

> 🟢 nas decisões confirmadas por respostas do revisor (Q15, Q19, Q29, Q50, Q51, Q52) ou por código entregue (adendos 001 a 007).

## 4. Premissas

🟡 Nenhuma premissa vinda de `[DÚVIDA]`: o `requirements.md` está com 0 marcadores após o clarify.

| Premissa | Origem (`requirements.md` seção) | Risco se errada |
|----------|----------------------------------|-----------------|
| `uvx --from <wheel>` resolve as dependências do wheel pelo PyPI na 1ª execução e as guarda em cache | 4. RN-06 | Sem rede na 1ª execução, o runtime não sobe; o aviso do lançador mostra a causa |
| O processo em background do lote (`sys.executable -m sintetica.batch.worker`) roda no ambiente do `uvx` | 4. RN-06 | O lote acima de 100 registros falha; teste do lançador com `generate` de 150 registros |
| As skills rodam com o diretório atual na raiz do projeto, onde o caminho relativo `.sintetica/bin/sintetica` vale | 4. RN-10 | A skill instrui o agente a rodar na raiz |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `installer/` (pacote npm `sintetica`) | `_reversa_sdd/sdd/cli-installer.md` | componente-novo | Instalador, skills e lançador |
| `sintetica.command` | `_reversa_sdd/addenda/002-llm-provider.md` a `007-quality-evaluator.md` | contrato-alterado | Prefixo dos comandos citados nas mensagens; padrão inalterado |
| `sintetica.cli` e serviços 002 a 007 | adendos 002 a 007 | contrato-alterado | 40 mensagens passam a usar `cli_command()` |

Estrutura de arquivos prevista:

```
installer/package.json
installer/tsconfig.json
installer/bin/sintetica.js      # verificação do Node e chamada do instalador (D-02)
installer/src/args.js           # argumentos (D-03)
installer/src/detect.js         # harnesses (D-04)
installer/src/runtime.js        # uv, Python, lançador e wheel (D-10 a D-12)
installer/src/plan.js           # arquivos desejados e ações (D-05)
installer/src/files.js          # escrita atômica, SHA-256 e diário de desfazer (D-07)
installer/src/prompt.js         # confirmações (D-06, D-16)
installer/src/install.js        # orquestração, manifest, state e resumo (D-08, D-09, D-17)
installer/skills/sintetica-*/SKILL.md
installer/test/*.test.js
src/sintetica/command.py        # cli_command() (D-13)
tests/test_skills_commands.py   # comandos citados nas skills (D-15)
docs/cli-installer.md
```

## 6. Delta no modelo de dados

- Resumo das mudanças: 🟡 `.sintetica/` ganha `runtime/` e `bin/`; `state.json` e `install-manifest.json` seguem a spec.
- Detalhe completo em: `_reversa_forward/008-cli-installer/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| `npx sintetica install`, lançador e `SINTETICA_CMD` | CLI + arquivo | `_reversa_forward/008-cli-installer/interfaces/installer-cli.md` |

## 8. Plano de migração

n/a. Arquivos novos. A troca das 40 mensagens não muda a saída sem `SINTETICA_CMD`.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| R-01: Sobrescrever arquivo do usuário | alto | baixo | Ação `perguntar` para todo arquivo fora do manifest ou editado; teste por cenário |
| R-02: Instalação parcial após falha | alto | baixo | Diário de desfazer (D-07); teste com falha na 3ª escrita |
| R-03: Mensagem do runtime cita um comando que não funciona no projeto do usuário | médio | médio | `SINTETICA_CMD` pelo lançador (D-13); teste pelos 2 caminhos |
| R-04: Skill cita comando que não existe | médio | médio | Teste D-15 contra o parser da CLI |
| R-05: Windows sem teste real | médio | médio | Caminhos por `path.join`, manifest com `/`, `.cmd` gerado; teste de unidade do conteúdo do `.cmd` |
| R-06: Ferramentas de desenvolvimento (`typescript`, `c8`) exigem `npm install` com rede | baixo | alto | Só no desenvolvimento; o instalador publicado não tem dependências |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Re-extração reversa executada e sem regressão vermelha (recomendado, não obrigatório)
- [ ] `tsc --checkJs --strict` sem erros e cobertura ≥ 80% pelo `c8` em `installer/`
- [ ] `mypy --strict` e `ruff` sem erros no projeto Python
- [ ] Os 17 cenários Gherkin do `requirements.md` cobertos por testes
- [ ] Os 516 testes das features 001 a 007 continuam passando

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-12 | Versão inicial gerada por `/reversa-plan` | reversa |
