# ADR 015: Instalador npx com wheel embutido e lançador

> Status: aceito (retroativo). Data da decisão: 2026-10-09 a 2026-10-12. Gerado pelo Detetive do Reversa.
> Confiança: 🟢 a decisão está registrada nas fontes e o código a confirma.

## Contexto

As skills precisam do runtime Python no projeto do usuário, que pode nem ter `pyproject.toml` (Q50).

## Decisão

Pacote npm `sintetica` em JavaScript ESM tipado por JSDoc (Q52), sem dependências de produção; instala as skills nos 2 destinos universais (Q51), o wheel da mesma versão e o lançador `.sintetica/bin/sintetica` (`uvx --from <wheel>`; sem wheel, `uv run`). O lançador define `SINTETICA_CMD` para as mensagens citarem o comando certo.

## Consequências

Uma só versão para npm e Python. As dependências Python vêm do PyPI na 1ª execução.

## Fontes

Q18, Q50 a Q52; `_reversa_forward/008-cli-installer/`; `installer/`, `src/sintetica/command.py`
