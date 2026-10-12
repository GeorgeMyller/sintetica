# Data Delta: cli-installer

> Identificador: `008-cli-installer`
> Data: `2026-10-12`
> Base: `_reversa_sdd/sdd/cli-installer.md#9. Modelo de Dados`. Não há modelo extraído de legado (greenfield).

## 1. Arquivos criados no projeto do usuário

| Caminho | Conteúdo | Atualização |
|---------|----------|-------------|
| `.agents/skills/sintetica-<etapa>/SKILL.md` (5) | Skill no formato universal | Substituído numa reinstalação se não foi editado |
| `.claude/skills/sintetica-<etapa>/SKILL.md` (5) | Mesma skill | Idem |
| `.sintetica/runtime/sintetica-<versão>-py3-none-any.whl` | Runtime Python (Q50) | Substituído pela versão nova |
| `.sintetica/bin/sintetica` e `sintetica.cmd` | Lançador (`uvx --from <wheel>`; sem wheel, `uv run`) | Substituído se não foi editado |
| `.sintetica/policy.json` | Política padrão (RN-04) | Nunca substituído; inválido → `policy.json.bak` + padrão |
| `.sintetica/state.json` | Estado da instalação | Regravado só se mudar |
| `.sintetica/install-manifest.json` | Registro dos arquivos | Regravado só se mudar |

## 2. Modelos

```
InstallManifest {
  sintetica_version: string           // versão do pacote npm = versão do wheel
  installed_at: string                // ISO 8601 UTC; muda só quando algum arquivo muda
  files: list<{ path: string,         // relativo à raiz do projeto, com "/"
                sha256: string }>     // ordenados por path; sem o próprio manifest
}

State {
  version: string
  harnesses: list<"claude-code" | "antigravity" | "cursor" | "gemini-cli" | "codex">
  runtime_ready: boolean              // uv e Python ≥ 3.10 encontrados
}

Policy {
  telemetry: false
  pii_premask: true
  cost_ceiling_usd: 5.00
  provider_priority: ["harness", "ollama", "external"]
  pii_custom_patterns: []
}
```

🟡 Diferença em relação à spec: `.sintetica/runtime/` e `.sintetica/bin/` são novos (Q50).

## 3. Variável de ambiente nova

| Variável | Quem define | Quem lê | Efeito |
|----------|-------------|---------|--------|
| `SINTETICA_CMD` | Lançador (`.sintetica/bin/sintetica`) | `sintetica.command.cli_command()` | Prefixo dos comandos citados nas mensagens; padrão `uv run sintetica` |

## 4. Migrações necessárias

Nenhuma. Arquivos novos.
