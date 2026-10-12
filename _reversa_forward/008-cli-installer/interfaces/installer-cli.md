# Interface: `npx sintetica install` e o lançador do runtime

> Tipo: CLI + arquivo. Origem: RN-01 a RN-11, RF-01 a RF-16, D-02 a D-17. Confidência: 🟡.

## 1. `npx sintetica install`

```
npx sintetica install [--yes] [--dir <caminho>]
```

| Situação | Resultado | Código de saída |
|----------|-----------|-----------------|
| Node.js < 18.0.0 | `✗` com a versão encontrada e a mínima; nada criado | 1 |
| Comando ausente ou desconhecido | Ajuda | 1 |
| Diretório = `$HOME` ou raiz, sem confirmação | Nada criado | 1 |
| Falha de escrita ou permissão | `✗` com o caminho; arquivos desta execução desfeitos | 1 |
| Instalação concluída (com ou sem avisos) | Resumo | 0 |
| Runtime ausente (`uv` ou Python ≥ 3.10) | `!` com o comando de instalação; `runtime_ready: false` | 0 |

Saída:

```
✓ Node.js 22.16.0
✓ Harnesses detectados: Claude Code, Cursor
✓ Skills: 5 em .agents/skills/ e .claude/skills/
! Arquivo do usuário mantido: .claude/skills/sintetica-start/SKILL.md (skill sintetica-start pulada)
✓ Runtime: .sintetica/bin/sintetica (wheel sintetica-0.1.0)
! uv não encontrado. Instale com: curl -LsSf https://astral.sh/uv/install.sh | sh
✓ Governança: .sintetica/policy.json, state.json, install-manifest.json

Instalado em /caminho/absoluto/do/projeto
  /caminho/absoluto/.agents/skills
  /caminho/absoluto/.claude/skills
  /caminho/absoluto/.sintetica
Próximo passo: no seu harness, rode /sintetica-start
```

Confirmação (terminal interativo):

```
? .claude/skills/sintetica-start/SKILL.md já existe e não foi criado pelo sintetica. Substituir? (sim/não)
```

- 🟡 `--yes`: responde sim a tudo, exceto à substituição de `policy.json`.
- 🟡 Sem terminal interativo e sem `--yes`: responde não, com aviso que sugere `--yes`.

## 2. Lançador `.sintetica/bin/sintetica`

```sh
.sintetica/bin/sintetica <comando> [argumentos]      # macOS e Linux
.sintetica\bin\sintetica.cmd <comando> [argumentos]  # Windows
```

- 🟡 Define `SINTETICA_CMD=.sintetica/bin/sintetica` e roda `uvx --from .sintetica/runtime/<wheel> sintetica <argumentos>`.
- 🟡 Sem o wheel: roda `uv run sintetica <argumentos>` (desenvolvimento).
- 🟡 O código de saída é o do runtime (tabela em `docs/*.md` das features 002 a 007).

## 3. `SINTETICA_CMD` no runtime Python

| Valor | Exemplo de mensagem |
|-------|---------------------|
| ausente | `Para retomar: uv run sintetica generate pedidos --resume` |
| `.sintetica/bin/sintetica` | `Para retomar: .sintetica/bin/sintetica generate pedidos --resume` |

## 4. Idempotência

- 🟡 2ª execução sem mudanças: nenhum arquivo é gravado (hashes e datas iguais).
- 🟡 Reinstalação com versão nova: só os arquivos do manifest sem edição são substituídos.
