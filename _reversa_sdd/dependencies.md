# Dependências: data_sintetic_generation (sintetica)

> Gerado pelo Scout do Reversa em 2026-10-12. Versões travadas lidas de `uv.lock` e `installer/package-lock.json`.
> Confiança: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA.

## 1. Runtime Python (`pyproject.toml`)

🟢 Gerenciador: `uv` (`uv.lock` com 30 pacotes). Build: `hatchling`. Python ≥ 3.10 (mypy alvo 3.10; ruff alvo `py310`).

### Produção

| Pacote | Restrição | Travada | Uso |
|--------|-----------|---------|-----|
| `pydantic` | `>=2.7` | 2.14.1 (`pydantic-core` 2.50.1) | Modelos de estado, contrato `Record` gerado, relatório |
| `faker` | `>=30.0` | 40.42.0 | Valores falsos do mascaramento de PII |
| `httpx` | `>=0.27` | 0.28.1 (`httpcore` 1.0.9, `anyio` 4.15.1, `h11` 0.16.0) | Chamadas às APIs de LLM e sondagem do Ollama |

🟢 Transitivas relevantes: `annotated-types` 0.8.0, `typing-extensions` 4.16.0, `certifi` 2026.7.22, `idna` 3.20, `tzdata` 2026.5.

### Desenvolvimento (`[dependency-groups] dev`)

| Pacote | Restrição | Travada |
|--------|-----------|---------|
| `mypy` | `>=1.13` | 2.4.0 |
| `pytest` | `>=8.3` | 9.1.1 |
| `pytest-cov` | `>=6.0` | 7.1.0 (`coverage` 7.16.2) |
| `ruff` | `>=0.8` | 0.16.10 |

## 2. Instalador Node (`installer/package.json`)

🟢 Gerenciador: npm (`package-lock.json` com 88 pacotes, todos de desenvolvimento). Node ≥ 18.0.0 (`engines`).

### Produção

🟢 Nenhuma. O instalador usa só a biblioteca padrão do Node (`node:fs`, `node:path`, `node:crypto`, `node:child_process`, `node:readline`, `node:os`, `node:url`).

### Desenvolvimento

| Pacote | Restrição | Travada | Uso |
|--------|-----------|---------|-----|
| `typescript` | `^5.6.0` | 5.9.3 | `tsc --checkJs --strict` sobre o JavaScript |
| `c8` | `^10.1.2` | 10.1.3 | Cobertura do `node:test` (≥ 80% de linhas) |
| `@types/node` | `^20.11.0` | 20.19.43 | Tipos da biblioteca padrão |

## 3. Ferramentas externas exigidas

| Ferramenta | Quem usa | Obrigatória? |
|------------|----------|--------------|
| `uv` / `uvx` | Lançador `.sintetica/bin/sintetica`, `npm run build:runtime` | Para o runtime; o instalador só avisa a falta |
| Python ≥ 3.10 | Runtime | Idem |
| Node.js ≥ 18 | `npx sintetica install` | Sim |
| Ollama (opcional) | `ExternalAPIProvider` com backend `ollama` | Não |
| Chaves `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` (opcionais) | APIs externas | Não |

## 4. Observações

- 🟢 O wheel `installer/runtime/sintetica-0.1.0-py3-none-any.whl` empacota só `sintetica/` e o `defaults.json`; as dependências de produção vêm do PyPI na 1ª execução do `uvx`.
- 🟢 A versão do pacote npm e a do pacote Python são as mesmas (teste `tests/test_skills_commands.py`).
- 🟡 Não há auditoria de vulnerabilidades configurada; o `npm install` avisou um pacote transitivo depreciado (`glob@10.5.0`, via `c8`), só de desenvolvimento.
