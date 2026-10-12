# C4 Nível 1, Contexto: sintetica

> Gerado pelo Arquiteto do Reversa em 2026-10-12. 🟢 extraído do código e do PRD.

```mermaid
C4Context
    title Contexto do sintetica

    Person(dev, "dev-de-testes", "Quer dados de teste em JSON ou CSV")
    Person(ml, "engenheiro-de-ml", "Quer conversas rotuladas em JSONL para fine-tuning")
    Person(an, "analista-de-dados", "Quer CSV que respeite regras de negócio")

    System_Ext(harness, "Harness de IA", "Claude Code, Antigravity, Cursor, Gemini CLI, Codex; roda as skills e o agente")
    System(sintetica, "sintetica", "Skills + runtime Python + instalador; gera, valida, mascara e avalia datasets")

    System_Ext(openai, "OpenAI API", "chat/completions")
    System_Ext(anthropic, "Anthropic API", "messages")
    System_Ext(gemini, "Gemini API", "generateContent")
    System_Ext(ollama, "Ollama", "LLM local")
    System_Ext(pypi, "PyPI", "Dependências do runtime (uvx)")
    System_Ext(npm, "npm", "Distribuição do instalador (npx)")

    Rel(dev, harness, "Descreve o dataset", "chat")
    Rel(ml, harness, "Descreve o dataset", "chat")
    Rel(an, harness, "Descreve o dataset", "chat")
    Rel(harness, sintetica, "Chama comandos; responde pedidos", "CLI + arquivos")
    Rel(sintetica, openai, "Pedidos mascarados", "HTTPS")
    Rel(sintetica, anthropic, "Pedidos mascarados", "HTTPS")
    Rel(sintetica, gemini, "Pedidos mascarados", "HTTPS")
    Rel(sintetica, ollama, "Pedidos mascarados", "HTTP")
    Rel(sintetica, pypi, "Baixa dependências na 1ª execução", "HTTPS")
    Rel(npm, sintetica, "Entrega o instalador", "npx")
```

| Elemento | Relação com o sintetica | Confiança |
|----------|------------------------|-----------|
| Personas | Interagem só pelo harness; nunca chamam o runtime direto | 🟢 |
| Harness | Lê as skills, roda a CLI, gera registros no protocolo `request`/`submit` | 🟢 |
| APIs de LLM e Ollama | Recebem pedidos mascarados; opcionais | 🟢 |
| PyPI e npm | Só distribuição | 🟢 |
