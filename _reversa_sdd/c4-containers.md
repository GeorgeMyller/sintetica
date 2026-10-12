# C4 Nível 2, Containers: sintetica

> Gerado pelo Arquiteto do Reversa em 2026-10-12. 🟢 extraído do código.

```mermaid
C4Container
    title Containers do sintetica (no projeto do usuário)

    Person(user, "Usuário")
    System_Ext(agent, "Agente do harness")

    Container_Boundary(proj, "Projeto do usuário") {
        Container(skills, "Skills", "Markdown (Agent Skills)", "5 SKILL.md em .agents/skills e .claude/skills")
        Container(launcher, "Lançador", "sh / cmd", ".sintetica/bin/sintetica; define SINTETICA_CMD")
        Container(cli, "Runtime sintetica", "Python 3.10+, Pydantic v2, httpx, Faker", "CLI com 9 comandos")
        Container(worker, "Processo do lote", "Python", "python -m sintetica.batch.worker; lote > 100")
        ContainerDb(datasets, "datasets/<slug>/", "Arquivos JSON/JSONL/CSV", "Intenção, contrato, amostra, lote, relatório, allowlist")
        ContainerDb(gov, ".sintetica/", "JSON + wheel", "policy, pricing, state, manifest, runtime, bin")
    }

    Container(installer, "Instalador", "Node 18+, JavaScript ESM", "npx sintetica install")
    System_Ext(llm, "APIs de LLM / Ollama")

    Rel(user, agent, "conversa")
    Rel(agent, skills, "lê")
    Rel(agent, launcher, "executa comandos")
    Rel(agent, datasets, "escreve schema.draft.json; lê requests/")
    Rel(launcher, cli, "uvx --from wheel / uv run")
    Rel(cli, datasets, "lê e grava (write_atomic, fsync)")
    Rel(cli, gov, "lê política e preços")
    Rel(cli, worker, "inicia em sessão própria; passa a trava")
    Rel(worker, datasets, "grava output/ e report")
    Rel(cli, llm, "HTTPS/HTTP, pedidos mascarados")
    Rel(worker, llm, "HTTPS/HTTP, pedidos mascarados")
    Rel(installer, skills, "instala")
    Rel(installer, gov, "cria política, estado, manifest, wheel, lançador")
```

| Container | Tecnologia | Responsabilidade | Confiança |
|-----------|-----------|------------------|-----------|
| Skills | Markdown com frontmatter | Instruções ao agente, por etapa | 🟢 |
| Lançador | `sh` (755) e `.cmd` (ASCII, CRLF) | Roda o runtime do wheel; sem wheel, `uv run` | 🟢 |
| Runtime | Python, `argparse`, Pydantic, httpx, Faker | Todos os comandos do pipeline | 🟢 |
| Processo do lote | Python, `asyncio` | Lote acima de 100 registros, com trava | 🟢 |
| `datasets/<slug>/` | Arquivos | Estado de cada dataset | 🟢 |
| `.sintetica/` | Arquivos | Governança e runtime instalado | 🟢 |
| Instalador | Node, só biblioteca padrão | Instalação idempotente com desfazer | 🟢 |
