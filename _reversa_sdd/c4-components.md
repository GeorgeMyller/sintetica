# C4 Nível 3, Componentes: runtime `sintetica` e instalador

> Gerado pelo Arquiteto do Reversa em 2026-10-12. 🟢 extraído do código.

## Runtime Python

```mermaid
C4Component
    title Componentes do runtime sintetica

    Container_Boundary(rt, "Runtime sintetica") {
        Component(cli, "cli", "argparse", "9 comandos; importação tardia; códigos de saída")
        Component(cmd, "command", "Python", "cli_command(): SINTETICA_CMD ou uv run sintetica")
        Component(intent, "intent", "Pydantic", "Entrevista, confirmação, intent.json")
        Component(schema, "schema", "Pydantic + gerador", "Contrato, código Record, serialização")
        Component(sample, "sample", "Python", "Amostra, revisão, semente")
        Component(batch, "batch", "asyncio", "Lote, blocos, retomada, trava, background")
        Component(quality, "quality", "Python", "Métricas, veredito, relatório")
        Component(providers, "providers", "httpx", "LLMProvider, seleção, custo, decoradores, harness")
        Component(pii, "pii", "regex + Faker", "Detecção, mascaramento, allowlist")
        Component(fsutil, "fsutil", "Python", "write_atomic")
    }

    Rel(cli, intent, "start, intent")
    Rel(cli, schema, "schema")
    Rel(cli, sample, "sample")
    Rel(cli, batch, "generate, status")
    Rel(cli, quality, "eval")
    Rel(cli, providers, "request, submit")
    Rel(intent, pii, "mask")
    Rel(sample, providers, "build_provider")
    Rel(sample, schema, "Record, formats")
    Rel(sample, pii, "mask")
    Rel(batch, providers, "build_provider (volume total)")
    Rel(batch, sample, "sementes, review, CommandResult")
    Rel(batch, quality, "evaluate_after_lot (tardio)")
    Rel(quality, batch, "state, lock")
    Rel(quality, pii, "leaks, coverage")
    Rel(providers, pii, "MaskingProvider")
```

| Componente | Entradas | Saídas | Confiança |
|------------|----------|--------|-----------|
| `intent` | Respostas do usuário | `intent.json` | 🟢 |
| `schema` | `intent.json`, `schema.draft.json` | `schema.json`, `schema.py`, `record.schema.json`, `schema.state.json` | 🟢 |
| `sample` | Contrato aprovado, provedor | `sample.state.json`, `seeds/` | 🟢 |
| `batch` | Sementes, contrato, provedor | `output/`, chama `quality` | 🟢 |
| `quality` | `output/dataset.<ext>`, `run.json`, contrato, allowlist | `report.json`, `report.md` | 🟢 |
| `providers` | `GenerationRequest`, política, preços | `GenerationResult`, `requests/` | 🟢 |
| `pii` | Texto, política | Texto mascarado, achados, `.pii_allowlist` | 🟢 |

## Pilha de decoradores do provedor

```mermaid
flowchart LR
    B[BudgetedProvider<br/>teto com reserva] --> C[ConcurrencyLimitedProvider<br/>semáforo 8]
    C --> M[MaskingProvider<br/>se pii_premask]
    M --> R[RetryingProvider<br/>3 chamadas]
    R --> E[ExternalAPIProvider<br/>openai, anthropic, gemini, ollama]
    C -.harness.-> H[HarnessAgentProvider<br/>request/submit]
```

## Instalador

```mermaid
C4Component
    title Componentes do instalador
    Container_Boundary(inst, "installer") {
        Component(bin, "bin/sintetica.js", "Node", "Checa o Node antes de importar")
        Component(args, "args", "JS", "checkNode, parseArgs")
        Component(install, "install", "JS", "Orquestra; state e manifest")
        Component(detect, "detect", "JS", "Marcadores de harness")
        Component(plan, "plan", "JS", "Arquivos desejados e ações")
        Component(prompt, "prompt", "JS", "Confirmações")
        Component(files, "files", "JS", "Escrita atômica e desfazer")
        Component(runtime, "runtime", "JS", "uv/Python, lançador, wheel")
    }
    Rel(bin, args, "checkNode, parseArgs")
    Rel(bin, install, "import() tardio")
    Rel(install, detect, "")
    Rel(install, plan, "")
    Rel(install, prompt, "")
    Rel(install, files, "Journal")
    Rel(install, runtime, "checkRuntime")
    Rel(plan, runtime, "lançadores, wheel")
```
