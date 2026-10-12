# Onboarding: cli-installer

> Identificador: `008-cli-installer`
> Data: `2026-10-12`
> Para quem vai testar a feature pela primeira vez, depois do `/reversa-coding`.

## Pré-requisitos

1. Instale Node.js 18 ou superior, Python 3.10 ou superior e o `uv`.
2. Abra um terminal na raiz do repositório.
3. Instale as ferramentas de desenvolvimento do instalador (exige rede):
   ```bash
   cd installer && npm install && cd ..
   ```

## Passo a passo

1. Rode as verificações. O resultado esperado é 0 erros, todos os testes passando e cobertura ≥ 80%.
   ```bash
   (cd installer && npm run typecheck && npm run coverage)
   uv run mypy && uv run ruff check && uv run pytest
   ```
2. Gere o wheel do runtime. O resultado esperado é `installer/runtime/sintetica-0.1.0-py3-none-any.whl`.
   ```bash
   (cd installer && npm run build:runtime)
   ```
3. Instale num projeto vazio com Claude Code. O resultado esperado é o resumo com Claude Code, as 10 pastas de skills e `.sintetica/`.
   ```bash
   mkdir -p /tmp/proj/.claude && cd /tmp/proj
   node /caminho/do/repo/installer/bin/sintetica.js install
   ```
4. Rode o lançador. O resultado esperado é a ajuda do runtime.
   ```bash
   .sintetica/bin/sintetica --help
   ```
5. Rode o instalador de novo. O resultado esperado é nenhum arquivo alterado.
   ```bash
   shasum -a 256 .sintetica/install-manifest.json
   node /caminho/do/repo/installer/bin/sintetica.js install
   shasum -a 256 .sintetica/install-manifest.json
   ```
6. Edite `.claude/skills/sintetica-start/SKILL.md` e rode de novo sem terminal interativo. O resultado esperado é o arquivo mantido e o aviso com `--yes`.
   ```bash
   echo "minha versão" > .claude/skills/sintetica-start/SKILL.md
   node /caminho/do/repo/installer/bin/sintetica.js install < /dev/null
   ```
7. No Claude Code, rode `/sintetica-start`. O resultado esperado é a entrevista pela skill instalada.

## Limpeza

```bash
rm -rf /tmp/proj
```
