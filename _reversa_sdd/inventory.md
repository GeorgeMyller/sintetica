# Inventário: data_sintetic_generation (sintetica)

> Gerado pelo Scout do Reversa em 2026-10-12. Nível de documentação: completo.
> Confiança: 🟢 CONFIRMADO (lido do código), 🟡 INFERIDO, 🔴 LACUNA.

## 1. Visão geral

🟢 O projeto é o **sintetica**: geração de dados sintéticos orientada por intenção, distribuída como skills de harnesses de IA. Tem 2 partes:

| Parte | Linguagem | Pasta | Papel |
|-------|-----------|-------|-------|
| Runtime | Python ≥ 3.10 | `src/sintetica/` | CLI `sintetica` com entrevista, contrato, amostra, lote, avaliação, provedores de LLM e detecção de PII |
| Instalador | JavaScript ESM (Node ≥ 18) | `installer/` | Pacote npm `sintetica` (`npx sintetica install`), as 5 skills e o lançador do runtime |

🟢 O projeto não é um repositório git. Não há CI/CD, Docker nem banco de dados.

## 2. Estrutura de pastas

```
.
├── src/sintetica/            # runtime Python (81 arquivos .py, ~7.100 linhas)
│   ├── cli.py                # ponto de entrada da CLI
│   ├── command.py            # prefixo dos comandos citados nas mensagens
│   ├── fsutil.py             # write_atomic
│   ├── pii/                  # detecção e mascaramento de PII
│   ├── providers/            # porta LLMProvider, harness, APIs externas, decoradores
│   │   ├── data/defaults.json
│   │   ├── decorators/       # budget, concurrency, masking, retrying
│   │   ├── external/         # OpenAI, Anthropic, Gemini, Ollama
│   │   └── harness/          # protocolo request/submit
│   ├── schema/               # contrato de dados e geração de código Pydantic
│   ├── intent/               # entrevista de intenção
│   ├── sample/               # amostra para aprovação
│   ├── batch/                # geração em lote, background e retomada
│   └── quality/              # avaliação de qualidade
├── tests/                    # 63 arquivos .py, 51 de teste (pytest)
│   ├── fixtures/pii_reference/   # 7 conjuntos de referência de PII
│   └── fixtures/schema/          # 7 definições de contrato
├── installer/                # pacote npm
│   ├── bin/sintetica.js
│   ├── src/                  # args, detect, files, plan, prompt, runtime, install
│   ├── skills/sintetica-{start,schema,sample,generate,eval}/SKILL.md
│   ├── templates/policy.json
│   ├── runtime/              # wheel gerado por build:runtime (artefato)
│   ├── test/                 # 7 arquivos (node:test)
│   └── coverage/             # 🟡 artefato do c8, não versionado
├── docs/                     # 9 guias curtos, 1 por componente
├── pyproject.toml, uv.lock
├── AGENTS.md, CLAUDE.md      # instruções do framework Reversa
├── .agents/, .claude/        # skills do Reversa (fora do produto)
├── _reversa_sdd/, _reversa_forward/, .reversa/   # artefatos do Reversa
```

## 3. Linguagens

| Linguagem | Extensões | Arquivos | Observação |
|-----------|-----------|----------|------------|
| Python | `.py` | 144 | 81 no runtime, 63 nos testes |
| JavaScript | `.js` | 15 | 8 no instalador, 7 nos testes (tipados por JSDoc) |
| JSON | `.json` | 28 | fixtures, política, defaults, pacote npm |
| Markdown | `.md` | 15 | docs, skills, instruções |

🟢 Linguagem principal: Python.

## 4. Módulos do runtime

| Módulo | Arquivos | Linhas | Responsabilidade (pelo nome e docstrings) |
|--------|----------|--------|-------------------------------------------|
| `pii` | 10 | 690 | Detectores de CPF, CNPJ, e-mail, telefone, cartão, IPv4/IPv6; substitutos falsos; allowlist por hash |
| `providers` | 21 | 1.350 | Porta `LLMProvider`, seleção por política, custo, harness, APIs externas, decoradores |
| `schema` | 15 | 1.430 | Rascunho declarativo, validação, normalização de nomes, CSV plano, geração de `schema.py` |
| `intent` | 7 | 634 | Entrevista em 5 perguntas, modos Guiado e Expresso, `intent.json` |
| `sample` | 6 | 679 | Amostra de 3 a 5 registros, revisão, aprovação, sementes |
| `batch` | 11 | 1.502 | Lote em blocos, custo, retomada, trava, processo em background |
| `quality` | 7 | 837 | Conformidade, unicidades, PII, duração, veredito e relatório |
| raiz | 3 | ~400 | `cli.py`, `command.py`, `fsutil.py` |

## 5. Pontos de entrada

| Caminho | Tipo | Observação |
|---------|------|------------|
| `src/sintetica/cli.py` (`main`) | CLI | Script `sintetica` do `pyproject.toml`; 9 comandos: `request`, `submit`, `schema`, `start`, `intent`, `sample`, `generate`, `status`, `eval` |
| `src/sintetica/batch/worker.py` | Processo em background | `python -m sintetica.batch.worker <projeto> <slug> [--lock-fd N]` |
| `installer/bin/sintetica.js` | CLI Node | `npx sintetica install [--yes] [--dir]` |
| `.sintetica/bin/sintetica` (gerado) | Lançador sh/cmd | `uvx --from <wheel> sintetica`; sem wheel, `uv run sintetica` |

## 6. Configuração

| Arquivo | Conteúdo |
|---------|----------|
| `pyproject.toml` | Pacote `sintetica` 0.1.0, hatchling, mypy estrito com plugin Pydantic, ruff (linha 100), pytest com marcadores `perf`, `live`, `codegen` |
| `installer/package.json` | Pacote npm `sintetica` 0.1.0, `engines.node >= 18`, scripts `typecheck`, `test`, `coverage`, `build:runtime`, `prepack` |
| `installer/tsconfig.json` | `allowJs`, `checkJs`, `strict`, `noEmit` |
| `src/sintetica/providers/data/defaults.json` | Modelo padrão por backend e preços por token |
| `installer/templates/policy.json` | Política padrão instalada em `.sintetica/policy.json` |
| `.sintetica/policy.json` e `.sintetica/pricing.json` (no projeto do usuário) | Política e preços sobrescritos |

🟢 Variáveis de ambiente lidas: `OLLAMA_HOST`, `SINTETICA_EXTERNAL_BACKEND`, `SINTETICA_<BACKEND>_MODEL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `SINTETICA_CMD`.

## 7. Integrações externas

| Integração | Onde | Uso |
|------------|------|-----|
| OpenAI (`api.openai.com/v1/chat/completions`) | `providers/external/backends.py` | Geração de registros |
| Anthropic (`api.anthropic.com/v1/messages`) | idem | Geração de registros |
| Gemini (`generativelanguage.googleapis.com`) | idem | Geração de registros |
| Ollama (`$OLLAMA_HOST/api/chat`, `/api/tags`) | idem e `providers/selection.py` | Geração local e sondagem |
| Agente do harness | `providers/harness/` | Arquivos `requests/<id>.json` e `<id>.response.jsonl` |

## 8. Persistência

🟢 Sem banco de dados. Tudo é arquivo por dataset em `datasets/<slug>/`:
`intent.json`, `schema.draft.json`, `schema.json`, `schema.py`, `record.schema.json`, `schema.state.json`, `sample.state.json`, `seeds/sample.jsonl`, `seeds/sample.meta.json`, `requests/`, `output/` (`run.json`, `records.partial.jsonl`, `dataset.<ext>`, `run.lock`, `worker.log`), `report.json`, `report.md`, `.pii_allowlist`.

## 9. Testes

| Suíte | Framework | Arquivos | Testes | Observação |
|-------|-----------|----------|--------|------------|
| Runtime | pytest 9.1, pytest-cov | 51 de teste | 532 (+ 7 `perf`/`live` fora da suíte padrão) | `mypy --strict` e `ruff` cobrem `src` e `tests` |
| Instalador | `node:test`, `c8` | 7 | 37 | Cobertura de 99,6% de linhas |

🟡 Cobertura do runtime por pacote, nas últimas medições: 96% a 99%.

## 10. Organização sugerida das specs

🟢 `module`: o runtime está organizado em pastas de domínio (`pii`, `providers`, `schema`, `intent`, `sample`, `batch`, `quality`), e o instalador é um pacote à parte. A decisão já está gravada em `.reversa/config.toml` (`granularity = "module"`).
