# Regression Watch: cli-installer

> Identificador: `008-cli-installer`
> Data: `2026-10-12`
> Feature greenfield. Não há regras 🟢 para vigiar. O watch principal fica vazio. Os requisitos implementados ficam em "Observações", sem peso de regressão, até uma extração `/reversa` futura confirmá-los como 🟢.

## Watch principal

| ID | Origem (arquivo, seção) | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|-------------------------|-----------------------------|---------------------|-------------------|

## Observações

| ID | Origem (arquivo, seção) | Regra esperada | Tipo de verificação | Sinal de violação |
|----|-------------------------|----------------|---------------------|-------------------|
| W001 | `_reversa_forward/008-cli-installer/requirements.md#4` RN-01 | Node < 18 termina com código 1, com a versão encontrada e a mínima | presença | `installer/test/detect.test.js` falha |
| W002 | `requirements.md#4` RN-02 (Q51) | Skills sempre em `.agents/skills/` e `.claude/skills/`; detecção só informa | presença | Skill instalada em pasta específica de harness |
| W003 | `requirements.md#4` RN-03 | Nenhum arquivo do usuário substituído sem confirmação; `--yes` nunca substitui `policy.json` | ausência | Conteúdo do usuário perdido em `install.test.js` |
| W004 | `requirements.md#4` RN-04 | Política padrão lida pelo runtime sem erro | presença | `tests/test_skills_commands.py::test_default_policy_is_accepted_by_the_runtime` falha |
| W005 | `requirements.md#4` RN-05 | Manifest com cada arquivo e SHA-256; 2ª execução não grava nada | presença | Teste "segunda execução sem mudanças" falha |
| W006 | `requirements.md#4` RN-06 (Q50) | Wheel em `.sintetica/runtime/` e lançador com `uvx --from`; sem o wheel, `uv run sintetica` | presença | `tests/test_launcher.py` falha |
| W007 | `requirements.md#4` RN-07 | Falha no meio desfaz tudo desta execução | presença | Arquivo novo após "falha no meio da cópia" |
| W008 | `requirements.md#4` RN-09 | Instalador sem chamada de rede e sem chave de API | ausência | Uso de `http`, `https` ou `fetch` em `installer/src/` |
| W009 | `requirements.md#4` RN-10 | Toda skill cita só comandos que existem na CLI | presença | `test_every_cited_command_exists` falha |
| W010 | `requirements.md#5` RF-16 | Mensagens citam o comando de quem chamou (`SINTETICA_CMD`) | presença | `tests/test_command.py` falha |
| W011 | `requirements.md#4` RN-11 (Q52) | `tsc --checkJs --strict` sem erros e cobertura ≥ 80% pelo `c8` | presença | `npm run typecheck` ou `npm run coverage` falha |
| W012 | `actions.md#Notas de execução` (decisão da T018) | Harnesses do `state.json` anterior continuam detectados | presença | `state.json` muda numa 2ª execução sem mudanças |
| W013 | `tests/test_skills_commands.py` | Versão do `package.json` igual à do `pyproject.toml` | presença | `test_npm_and_python_versions_match` falha |

## Histórico de re-extrações

### Re-extração 2026-10-12 12:00

> Watch principal vazio (feature greenfield). Itens de "Observações" verificados de forma informativa, sem peso de regressão.

| ID | Veredito | Observação |
|----|----------|------------|
| W001 | 🟢 verde | regra presente em `_reversa_sdd/sdd/cli-installer.md` e `_reversa_sdd/domain.md` |
| W002 | 🟢 verde | regra presente em `_reversa_sdd/sdd/cli-installer.md` e `_reversa_sdd/domain.md` |
| W003 | 🟢 verde | regra presente em `_reversa_sdd/sdd/cli-installer.md` e `_reversa_sdd/domain.md` |
| W004 | 🟢 verde | regra presente em `_reversa_sdd/sdd/cli-installer.md` e `_reversa_sdd/domain.md` |
| W005 | 🟢 verde | regra presente em `_reversa_sdd/sdd/cli-installer.md` e `_reversa_sdd/domain.md` |
| W006 | 🟢 verde | regra presente em `_reversa_sdd/sdd/cli-installer.md` e `_reversa_sdd/domain.md` |
| W007 | 🟢 verde | regra presente em `_reversa_sdd/sdd/cli-installer.md` e `_reversa_sdd/domain.md` |
| W008 | 🟢 verde | regra presente em `_reversa_sdd/sdd/cli-installer.md` e `_reversa_sdd/domain.md` |
| W009 | 🟢 verde | regra presente em `_reversa_sdd/sdd/cli-installer.md` e `_reversa_sdd/domain.md` |
| W010 | 🟢 verde | regra presente em `_reversa_sdd/sdd/cli-installer.md` e `_reversa_sdd/domain.md` |
| W011 | 🟢 verde | regra presente em `_reversa_sdd/sdd/cli-installer.md` e `_reversa_sdd/domain.md` |
| W012 | 🟢 verde | regra presente em `_reversa_sdd/sdd/cli-installer.md` e `_reversa_sdd/domain.md` |
| W013 | 🟢 verde | regra presente em `_reversa_sdd/sdd/cli-installer.md` e `_reversa_sdd/domain.md` |

| Data | Resultado | Observação |
|------|-----------|------------|

## Arquivadas

| ID | Motivo | Data |
|----|--------|------|
