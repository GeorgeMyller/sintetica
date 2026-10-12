# Spec: cli-installer

> Selo 🟢 CONFORME CÓDIGO em todos os itens, salvo marcação. Fonte: `installer/` (pacote npm `sintetica`), `src/sintetica/command.py`, testes `installer/test/` (37), `tests/test_command.py`, `tests/test_skills_commands.py`, `tests/test_launcher.py`.
> Consolida o adendo `008-cli-installer.md`. Versão planejada em `sdd/_planejado/cli-installer.md`.

**Versão:** 2.0 (extraída do código)
**Status:** Implementado
**Autor:** reversa-writer
**Data:** 2026-10-12

---

## 1. Resumo

🟢 O `cli-installer` é o pacote npm `sintetica` (`installer/`). `npx sintetica install` confere o Node.js, detecta os harnesses, instala as 5 skills em `.agents/skills/` e `.claude/skills/`, o wheel do runtime Python em `.sintetica/runtime/` e o lançador `.sintetica/bin/sintetica`, e cria `.sintetica/policy.json`, `state.json` e `install-manifest.json`. Nunca substitui arquivo do usuário sem confirmação, desfaz tudo se falhar e não usa a rede.

## 2. Contexto

🟢 As skills precisam do runtime no projeto do usuário, que pode nem ter `pyproject.toml` (Q50). O PRD exige o formato universal de skills, sem adaptação por harness (Q51).

## 3. Goals

- 🟢 G-01: Instalação com 1 comando, idempotente.
- 🟢 G-02: 0 arquivos do usuário substituídos sem confirmação.
- 🟢 G-03: Runtime pronto para rodar por `uvx`, na mesma versão do pacote npm.

## 4. Non-Goals

- 🟢 NG-01: Não instala Python, `uv` nem Node; só verifica e avisa.
- 🟢 NG-02: Sem desinstalação; sem telemetria; sem instalação global.

## 5. Usuários

🟢 As 3 personas; o agente do harness (lê as skills e usa o lançador).

## 6. Requisitos Funcionais

| ID | Requisito | Critério de aceite | Fonte |
|----|-----------|--------------------|-------|
| RF-01 | 🟢 Node < 18.0.0: `✗` com a versão encontrada e a mínima; código 1; a checagem roda antes de importar módulos modernos | — | `bin/sintetica.js`, `src/args.js:18-34` |
| RF-02 | 🟢 Argumentos: `install [--yes\|-y] [--dir <caminho>]`; comando ausente, desconhecido ou opção inválida mostram a ajuda e terminam com 1 | — | `src/args.js:43-66` |
| RF-03 | 🟢 Pasta inexistente = 1; pasta pessoal ou raiz do sistema exige confirmação (`--yes` confirma); recusa = 1 sem criar nada | — | `src/install.js:115-128`, `src/prompt.js:39-43` |
| RF-04 | 🟢 Detecção (só informa resumo e `state.json`): Claude Code `.claude`; Antigravity `.agents`/`.agent`; Cursor `.cursor`; Gemini CLI `.gemini`; Codex `.codex`/`AGENTS.md`; `.claude`/`.agents` com só as skills do sintetica não contam, salvo se o `state.json` anterior já listava o harness | Q51 | `src/detect.js` |
| RF-05 | 🟢 Arquivos desejados: 10 skills (5 × 2 destinos), lançador `sh` (755) e `.cmd`, wheel `sintetica-<versão>-py3-none-any.whl` (se empacotado) e a política padrão | — | `src/plan.js:31-60` |
| RF-06 | 🟢 Ação por arquivo: `criar`, `igual` (mesmo SHA-256, nada gravado), `substituir` (no manifest com o hash atual), `perguntar` (fora do manifest ou editado), `preservar` (`policy.json` válido), `recuperar` (`policy.json` inválido → `.bak` + padrão, com aviso) | — | `src/plan.js:80-91`, `src/install.js:147-156` |
| RF-07 | 🟢 Confirmação: 1 pergunta por skill (as 2 cópias) e por arquivo; `--yes` = sim (nunca para a política, que nunca é perguntada); sem terminal interativo = não, com aviso sugerindo `--yes`; não = pula as 2 cópias com aviso | — | `src/prompt.js:13-31`, `src/install.js:180-212` |
| RF-08 | 🟢 Escrita atômica (temporário, `chmod`, `rename`) com diário de desfazer; qualquer erro desfaz tudo desta execução e termina com 1, citando caminho e código (`ENOSPC`, `EACCES`) | — | `src/files.js`, `src/install.js:142-170` |
| RF-09 | 🟢 Runtime: `uv --version` e Python ≥ 3.10 (`uv python find ">=3.10"`, ou `python3`/`python --version`) por `spawnSync` sem shell; sem eles: `runtime_ready: false` e aviso com o comando de instalação do `uv` por sistema (só exibido) | Código 0 | `src/runtime.js:39-81` |
| RF-10 | 🟢 Lançador: define `SINTETICA_CMD` com o próprio caminho e roda `uvx --from <wheel> sintetica`; sem o wheel, `uv run sintetica`; `.cmd` em ASCII com CRLF | Q50 | `src/runtime.js:107-145` |
| RF-11 | 🟢 `state.json` (`version`, `harnesses`, `runtime_ready`) e `install-manifest.json` (`sintetica_version`, `installed_at` sem milissegundos, `files` ordenados com SHA-256, sem o próprio manifest) gravados só se mudarem | 2ª execução igual não grava nada | `src/install.js:158-266` |
| RF-12 | 🟢 Resumo com `✓`/`!`/`✗`: Node, harnesses, skills, runtime, avisos, governança, caminhos absolutos e o próximo passo `/sintetica-start` | — | `src/install.js:172-178` |
| RF-13 | 🟢 Manifest ilegível vira aviso; arquivos existentes são tratados como do usuário | — | `src/install.js:54-67` |
| RF-14 | 🟢 As 5 skills (`installer/skills/sintetica-*/SKILL.md`) têm frontmatter `name`/`description` e citam só comandos existentes da CLI, pelo lançador | Teste contra o parser da CLI | `tests/test_skills_commands.py` |
| RF-15 | 🟢 Runtime Python: `cli_command()` devolve `SINTETICA_CMD` ou `uv run sintetica`; as 40 mensagens que citam comandos a usam | Pelo lançador: `.sintetica/bin/sintetica generate <slug> --resume` | `src/sintetica/command.py` |
| RF-16 | 🟢 Pacote: `npm run build:runtime` (no `prepack`) gera o wheel com `uv build`; versão do `package.json` igual à do `pyproject.toml` | Teste de versão | `installer/package.json`, `tests/test_skills_commands.py` |

## 7. Requisitos Não-Funcionais

| ID | Requisito | Evidência |
|----|-----------|-----------|
| RNF-01 | 🟢 Node ≥ 18; sem dependências de produção | `package.json` |
| RNF-02 | 🟢 0 chamadas de rede | Só `node:fs`, `path`, `crypto`, `child_process`, `readline`, `os`, `url` |
| RNF-03 | 🟢 `tsc --checkJs --strict`; cobertura ≥ 80% pelo `c8` (medido 99,6%) | Q52 |
| RNF-04 | 🟡 Windows experimental: lançador `.cmd` com teste só de conteúdo (Q53) | `installer/test/runtime.test.js` |

## 8. Interface

```
npx sintetica install [--yes] [--dir <caminho>]
.sintetica/bin/sintetica <comando> [argumentos]       # macOS e Linux
.sintetica\bin\sintetica.cmd <comando> [argumentos]   # Windows
```

| Código | Significado |
|--------|-------------|
| 0 | Instalação concluída (com ou sem avisos) |
| 1 | Node antigo, comando inválido, pasta inexistente, cancelamento ou falha de escrita |

## 9. Modelo de Dados

🟢 `InstallManifest`, `State`, `Policy` (`telemetry: false`, `pii_premask: true`, `cost_ceiling_usd: 5.00`, `provider_priority: ["harness", "ollama", "external"]`, `pii_custom_patterns: []`). Detalhe em `data-dictionary.md#módulo-installer`.

## 10. Integrações

| Dependência | Tipo |
|-------------|------|
| 🟢 npm (`npx`) | Distribuição |
| 🟢 `uv`/`uvx` e PyPI | Runtime do lançador (dependências baixadas na 1ª execução) |
| 🟢 Runtime Python | Recebe `SINTETICA_CMD` |

## 11. Edge Cases

| Cenário | Comportamento |
|---------|---------------|
| 🟢 `.claude` vazio | Conta como Claude Code |
| 🟢 Skill do usuário com o mesmo nome | Pergunta; não = mantém e pula |
| 🟢 Skill instalada e editada | Tratada como do usuário |
| 🟢 `policy.json` corrompido | `.bak` + padrão |
| 🟢 Disco cheio no meio | Desfaz tudo; código 1 |
| 🟢 Versão nova | Substitui só o que está no manifest sem edição |

## 12. Segurança

- 🟢 Processos externos sem shell; não lê nem grava chaves de API.

## 13. Decisões (consolidadas)

| Decisão | Fonte |
|---------|-------|
| 🟢 Wheel embutido + lançador `uvx` | Q50, ADR 015 |
| 🟢 2 destinos universais | Q51 |
| 🟢 JavaScript ESM com JSDoc, `node:test`, `c8` | Q52 |
| 🟢 Node ≥ 18 | Q18 |

## 14. Lacunas

- 🟡 Ramo Windows experimental: sem teste real até existir um runner Windows em CI (Q53).
- 🟡 Publicação no npm fora do escopo atual.

## Histórico

| Versão | Data | Mudança |
|--------|------|---------|
| 1.0 | 2026-10-09 | Spec planejada (`_planejado/`) |
| 2.0 | 2026-10-12 | Reescrita conforme o código; adendo 008 consolidado |
