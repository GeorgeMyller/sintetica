# Adendo: cli-installer (instalador `npx sintetica install`)

> Identificador: `008-cli-installer`
> Data: `2026-10-12`
> Cenário: greenfield

## Vigência

Vigente desde 2026-10-12.
Superado pela re-extração de 2026-10-12.

## Resumo da entrega

O pacote npm `sintetica` (pasta `installer/`) implementa `npx sintetica install`. O instalador confere o Node.js ≥ 18 e detecta os harnesses pelos marcadores, só para informar. Depois, ele instala:
- as 5 skills em `.agents/skills/` e `.claude/skills/` (Q51);
- o wheel do runtime Python em `.sintetica/runtime/`;
- o lançador `.sintetica/bin/sintetica` (e `.cmd`), que roda `uvx --from <wheel> sintetica` e, sem o wheel, `uv run sintetica` (Q50);
- `.sintetica/policy.json`, `state.json` e `install-manifest.json` com SHA-256.

Regras de escrita do instalador:
- Ele nunca substitui um arquivo do usuário sem confirmação, e `--yes` nunca substitui `policy.json`.
- Uma 2ª execução sem mudanças não grava nada.
- Uma falha no meio desfaz tudo desta execução.
- A falta de `uv` ou de Python ≥ 3.10 vira aviso com o comando de instalação, sem bloquear.

O código é JavaScript ESM com JSDoc, verificado por `tsc --checkJs --strict` e testado com `node:test` e `c8` (Q52), sem dependências de produção.

A entrega também escreveu as 5 skills (`SKILL.md`) que as features 003 a 007 deixaram de fora. Ela também criou `sintetica.command.cli_command()`: as 40 mensagens do runtime que citam um comando passam a usar o prefixo definido pelo lançador (`SINTETICA_CMD`), com `uv run sintetica` como padrão.

Ações concluídas: 28 de 28 (`progress.jsonl` com 28 registros).

Verificação:
- 532 testes Python (516 das features 001 a 007 + 16 novos);
- 37 testes Node, com cobertura do instalador em 99,6% de linhas;
- `tsc --checkJs --strict`, `mypy --strict` e `ruff` sem erros;
- 17 cenários Gherkin cobertos;
- instalação real com o wheel gerado por `uv build` e o runtime rodando pelo lançador.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/prd.md` | 4. Escopo (in), "Distribuição e instalação" | componente-novo | `npx sintetica install` implementado: detecção dos 5 harnesses, skills no formato universal e `.sintetica/` com os 3 arquivos. |
| `_reversa_sdd/prd.md` | 4. Escopo (in), "Pipeline de agentes" | componente-novo | As 5 skills existem em `installer/skills/` e chamam o lançador `.sintetica/bin/sintetica`; um teste confere cada comando citado contra a CLI. |
| `_reversa_sdd/prd.md` | 4. Escopo (in), "Runtime Python" e 7. Dependências externas | componente-novo | Leia a distribuição do runtime como wheel dentro do pacote npm, rodado por `uvx` (Q50); o `pyproject.toml` do usuário não muda. As dependências Python vêm do PyPI na 1ª execução. |
| `_reversa_sdd/prd.md` | 6. Restrições (versões mínimas) | componente-novo | Node.js ≥ 18 e Python ≥ 3.10 agora são verificados pelo instalador (Q18). |
| `_reversa_sdd/prd.md` | 9. Critérios de aceite (instalação) | componente-novo | O critério "detecta, injeta e cria `.sintetica/`" tem teste de ponta a ponta. |
| `_reversa_sdd/sdd/cli-installer.md` | 6. Requisitos Funcionais (RF-01, RF-02) | componente-novo | Implementados. Leia RF-02 com a Q51: a detecção só informa o resumo e `state.json`; os destinos são sempre os 2 universais. |
| `_reversa_sdd/sdd/cli-installer.md` | 6. Requisitos Funcionais (RF-03 a RF-06) | componente-novo | Implementados. O manifest não lista a si mesmo e inclui `state.json`, o wheel e os lançadores. |
| `_reversa_sdd/sdd/cli-installer.md` | 6. Requisitos Funcionais (RF-07, RF-11) | componente-novo | Implementados. Arquivo do manifest editado pelo usuário também exige confirmação; sem terminal interativo e sem `--yes`, a resposta é não. |
| `_reversa_sdd/sdd/cli-installer.md` | 6. Requisitos Funcionais (RF-08) | componente-novo | Implementado, com wheel e lançador (Q50). `state.json` grava `runtime_ready`; o comando de instalação do `uv` só é exibido. |
| `_reversa_sdd/sdd/cli-installer.md` | 6. Requisitos Funcionais (RF-09, RF-10) e 6.3 Fluxos Alternativos | componente-novo | Implementados. Na reinstalação, os harnesses do `state.json` anterior continuam detectados. |
| `_reversa_sdd/sdd/cli-installer.md` | 9. Modelo de Dados | delta-de-dados | `.sintetica/runtime/` e `.sintetica/bin/` são novos; `State` segue a spec; harnesses com ids `claude-code`, `antigravity`, `cursor`, `gemini-cli`, `codex`. |
| `_reversa_sdd/sdd/cli-installer.md` | 11. Edge Cases (EC-01 a EC-05) | componente-novo | Implementados com escrita atômica e diário de desfazer. Fora de projeto: confirmação, ou `--yes`. |
| `_reversa_sdd/sdd/cli-installer.md` | 14. Open Questions (OQ-01, OQ-02) | componente-novo | Resolvidas: OQ-01 pela Q51; OQ-02 pela Q52 (`c8`). |
| `_reversa_sdd/addenda/002-llm-provider.md` a `007-quality-evaluator.md` | Mensagens dos comandos | delta-de-contrato-externo | As mensagens citam `cli_command()`: `.sintetica/bin/sintetica` pelo lançador, `uv run sintetica` sem ele. Os `docs/*.md` das features 004 a 007 ganharam a nota do lançador. |
| `_reversa_sdd/addenda/004-intent-interview.md` | Comando `sintetica` | delta-de-contrato-externo | Novo comando de instalação no Node (`npx sintetica install`, códigos 0 e 1); a CLI Python não muda. |

## Regras sob vigilância

W001, W002, W003, W004, W005, W006, W007, W008, W009, W010, W011, W012, W013. Todos estão em "Observações", sem peso de regressão (cenário greenfield). Detalhes em `_reversa_forward/008-cli-installer/regression-watch.md`.

## Fontes

- `_reversa_forward/008-cli-installer/legacy-impact.md`
- `_reversa_forward/008-cli-installer/regression-watch.md`
- `_reversa_forward/008-cli-installer/requirements.md`
- `_reversa_forward/008-cli-installer/roadmap.md`
- `_reversa_forward/008-cli-installer/data-delta.md`
- `_reversa_forward/008-cli-installer/interfaces/installer-cli.md`
- `_reversa_forward/008-cli-installer/progress.jsonl`
- `_reversa_forward/008-cli-installer/actions.md`
