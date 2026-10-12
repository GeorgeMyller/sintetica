## Módulo `installer`

### `.sintetica/install-manifest.json`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `sintetica_version` | `string` | Versão do pacote npm (= versão do wheel) |
| `installed_at` | `string` | ISO 8601 UTC sem milissegundos; muda só quando a lista muda |
| `files` | `list<{path, sha256}>` | Caminhos relativos com `/`, ordenados; sem o próprio manifest |

### `.sintetica/state.json`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `version` | `string` | Versão instalada |
| `harnesses` | `list<string>` | `claude-code`, `antigravity`, `cursor`, `gemini-cli`, `codex` |
| `runtime_ready` | `boolean` | `uv` e Python ≥ 3.10 encontrados |

### `.sintetica/policy.json` (padrão em `installer/templates/policy.json`)

| Chave | Valor padrão | Lida por |
|-------|--------------|----------|
| `telemetry` | `false` | Nenhum código (declaração de política) |
| `pii_premask` | `true` | `providers.policy` |
| `cost_ceiling_usd` | `5.00` | `providers.policy` |
| `provider_priority` | `["harness", "ollama", "external"]` | `providers.policy` |
| `pii_custom_patterns` | `[]` | `pii.policy` |

### Arquivos instalados no projeto do usuário

| Caminho | Modo |
|---------|------|
| `.agents/skills/sintetica-<etapa>/SKILL.md`, `.claude/skills/sintetica-<etapa>/SKILL.md` | 644 |
| `.sintetica/bin/sintetica` | 755 |
| `.sintetica/bin/sintetica.cmd` | 644 |
| `.sintetica/runtime/sintetica-<versão>-py3-none-any.whl` | 644 |

### Opções do instalador (`InstallOptions`)

| Campo | Tipo | Uso |
|-------|------|-----|
| `dir` | `string` | Pasta do projeto |
| `yes` | `boolean` | Responde sim (exceto política) |
| `out` | `(line) => void` | Saída |
| `ask`, `interactive`, `fs`, `spawn`, `env`, `nodeVersion`, `home`, `platform`, `packageDir`, `now` | — | Injeção para testes |

### Variável de ambiente

| Variável | Definida por | Lida por |
|----------|--------------|----------|
| `SINTETICA_CMD` | Lançador | `sintetica.command.cli_command()` (padrão `uv run sintetica`) |
