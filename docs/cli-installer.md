# cli-installer

Instalador do sintetica: `npx sintetica install`. Ele detecta os harnesses de IA do projeto, instala as 5 skills, o runtime Python e o lançador, e cria a pasta de governança `.sintetica/`. Não faz chamadas de rede, não lê chaves de API e não instala Python nem `uv`.

## Uso

```bash
npx sintetica install            # na raiz do projeto
npx sintetica install --yes      # responde sim às confirmações
npx sintetica install --dir ../outro-projeto
```

- Exige Node.js 18 ou superior; abaixo disso, termina com código 1.
- Na pasta pessoal ou na raiz do sistema, pede confirmação antes de instalar.
- Depois, no harness, rode `/sintetica-start`.

## Arquivos criados

| Caminho | Conteúdo |
|---------|----------|
| `.agents/skills/sintetica-*/SKILL.md` e `.claude/skills/sintetica-*/SKILL.md` | As 5 skills (`start`, `schema`, `sample`, `generate`, `eval`), sempre nos 2 destinos universais |
| `.sintetica/runtime/sintetica-<versão>-py3-none-any.whl` | Runtime Python da mesma versão do pacote npm |
| `.sintetica/bin/sintetica` e `sintetica.cmd` | Lançador: `uvx --from <wheel> sintetica`; sem o wheel, `uv run sintetica` |
| `.sintetica/policy.json` | Política padrão: sem telemetria, mascaramento de PII, teto de US$ 5,00, prioridade harness → ollama → external |
| `.sintetica/state.json` | Versão, harnesses detectados e `runtime_ready` |
| `.sintetica/install-manifest.json` | Cada arquivo criado, com caminho relativo e SHA-256 |

Harnesses detectados (só informam o resumo e o `state.json`): Claude Code (`.claude/`), Antigravity (`.agents/` ou `.agent/`), Cursor (`.cursor/`), Gemini CLI (`.gemini/`), Codex (`.codex/` ou `AGENTS.md`).

## Regras de escrita

- Arquivo que já existe e não foi criado pelo instalador (ou foi editado depois): pergunta antes de substituir. Resposta não mantém o arquivo e pula a skill.
- Sem terminal interativo e sem `--yes`, a resposta é não, com aviso.
- `--yes` nunca substitui `.sintetica/policy.json` existente. `policy.json` inválido vira `policy.json.bak` e a política padrão é gravada.
- 2ª execução sem mudanças não grava nenhum arquivo. Versão nova substitui só os arquivos do manifest que não foram editados.
- Falha no meio (disco cheio, sem permissão) desfaz tudo desta execução e termina com código 1.

## Runtime Python

- O instalador verifica `uv` e Python 3.10 ou superior. Sem eles, instala as skills, grava `runtime_ready: false` e mostra o comando de instalação do `uv`.
- As skills chamam o lançador. Ele define `SINTETICA_CMD`, e as mensagens do runtime passam a citar `.sintetica/bin/sintetica` no lugar de `uv run sintetica`.
- Na 1ª execução, o `uvx` baixa as dependências Python (Pydantic, Faker, httpx) e as guarda em cache.

## Códigos de saída

| Código | Significado |
|--------|-------------|
| 0 | Instalação concluída (com ou sem avisos) |
| 1 | Node.js antigo, comando inválido, instalação cancelada ou falha de escrita |

## Desenvolvimento do pacote (`installer/`)

```bash
cd installer
npm install                 # typescript, c8 e @types/node (só desenvolvimento)
npm run typecheck           # tsc --checkJs --strict
npm run coverage            # node:test com cobertura ≥ 80% pelo c8
npm run build:runtime       # gera runtime/sintetica-<versão>-py3-none-any.whl (roda no prepack)
```

A versão do `package.json` precisa ser igual à do `pyproject.toml` (teste `tests/test_skills_commands.py`).
