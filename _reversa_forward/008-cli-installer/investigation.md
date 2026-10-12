# Investigation: cli-installer

> Identificador: `008-cli-installer`
> Data: `2026-10-12`
> Fonte: `_reversa_forward/008-cli-installer/roadmap.md`

## 1. Pesquisa de fundo (código entregue)

### 1.1 Política lida pelo runtime (features 001 e 002)
- 🟢 `load_provider_policy` lê `pii_premask`, `cost_ceiling_usd` e `provider_priority`, e ignora chaves desconhecidas: `telemetry` não quebra a leitura.
- 🟢 `load_custom_patterns` lê `pii_custom_patterns` (lista de textos não vazios, até 200 caracteres).
- 🟢 Arquivo ausente vale como padrão nas 2 leituras.

### 1.2 Mensagens com comandos (features 002 a 007)
- 🟢 40 ocorrências de `uv run sintetica` em 9 arquivos de `src/sintetica/` (CLI, serviços e `HarnessAgentProvider.submit_command`).
- 🟢 Os testes das features anteriores conferem parte dessas mensagens; com o padrão `uv run sintetica`, continuam válidos (D-13).

### 1.3 Pacote Python
- 🟢 `pyproject.toml` com `hatchling`, versão `0.1.0` e o script `sintetica = "sintetica.cli:main"`; `uv build --wheel` gera `sintetica-0.1.0-py3-none-any.whl`.
- 🟢 O lote em background roda `sys.executable -m sintetica.batch.worker`, que funciona em qualquer ambiente onde o pacote está instalado, inclusive o do `uvx`.

### 1.4 Ambiente desta máquina
- 🟢 Node.js 22.16.0 (Volta). Os aliases `npm` e `uv` do shell apontam para um comando ausente (`safety`); a execução usa os binários diretos.

## 2. Alternativas avaliadas

### 2.1 Mensagens com o comando certo (RF-16)
| Alternativa | Prós | Contras | Decisão |
|-------------|------|---------|---------|
| Variável `SINTETICA_CMD` definida pelo lançador | 1 ponto de mudança; padrão inalterado | Toca 9 arquivos de features anteriores | Escolhida (D-13) |
| A skill manda o agente trocar `uv run sintetica` pelo lançador | Sem mudança no Python | Frágil; depende do agente | Descartada |
| Lançador chamado `uv` | — | Confunde o usuário | Descartada |

### 2.2 Verificação da versão do Node
| Alternativa | Prós | Contras | Decisão |
|-------------|------|---------|---------|
| `bin` com sintaxe antiga e `import()` dinâmico depois da checagem | Node 16 mostra a mensagem certa | 1 arquivo com estilo diferente | Escolhida (D-02) |
| `engines` no `package.json` | Sem código | O `npx` só avisa, não bloqueia | Complemento |

### 2.3 Confirmação sem terminal
| Alternativa | Prós | Contras | Decisão |
|-------------|------|---------|---------|
| Responder "não" e sugerir `--yes` | Nunca sobrescreve sem querer (G-04) | O agente precisa rodar de novo | Escolhida (D-06) |
| Esperar a entrada | — | Trava o agente do harness | Descartada |

## 3. Padrões aplicáveis

- 🟡 Escrita atômica: arquivo temporário no mesmo diretório e `fs.renameSync`.
- 🟡 SHA-256 com `node:crypto` (`createHash("sha256")`).
- 🟡 Processos externos com `child_process.spawnSync` sem shell, para evitar interpretação de argumentos.
- 🟡 Agent Skills: pasta por skill com `SKILL.md` e frontmatter `name` e `description`.

## 4. Fontes externas

- Node.js, `node:test`: https://nodejs.org/api/test.html
- `c8`: https://github.com/bcoe/c8
- TypeScript, JSDoc em JavaScript (`checkJs`): https://www.typescriptlang.org/docs/handbook/type-checking-javascript-files.html
- `uv`, `uvx --from` e instalação: https://docs.astral.sh/uv/
- Agent Skills (formato `SKILL.md`): https://docs.anthropic.com/en/docs/claude-code/skills
