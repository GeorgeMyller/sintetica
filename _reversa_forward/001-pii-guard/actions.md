# Actions: pii-guard (detecção e mascaramento local de PII)

> Identificador: `001-pii-guard`
> Data: `2026-10-09`
> Roadmap: `_reversa_forward/001-pii-guard/roadmap.md`
> Fontes auxiliares: `data-delta.md`, `requirements.md` (13 cenários Gherkin). Sem `interfaces/`.

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 27 |
| Paralelizáveis (`[//]`) | 16 |
| Maior cadeia de dependência | 10 (T002 → T012 → T015 → T016 → T017 → T021 → T022 → T023 → T024 → T025) |

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Criar `pyproject.toml`: projeto `sintetica`, Python ≥ 3.10, backend `hatchling`, layout `src`, dependência `faker`; grupo dev com `pytest`, `pytest-cov`, `mypy`, `ruff`; `[tool.mypy] strict = true` com override `ignore_missing_imports` só para `faker`; `[tool.ruff]` com `target-version = "py310"`; `[tool.pytest.ini_options]` com marcador `perf` excluído por padrão (D-01, D-02, R-02, R-03) | - | `[//]` | `pyproject.toml` | 🟡 | `[X]` |
| T002 | Criar o pacote raiz: `src/sintetica/__init__.py` com `__version__ = "0.1.0"` e o marcador vazio `src/sintetica/py.typed` | - | `[//]` | `src/sintetica/__init__.py` | 🟡 | `[X]` |
| T003 | Criar ou completar `.gitignore` com `.venv/`, `__pycache__/`, `.coverage`, `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/` e `datasets/`, sem remover linhas existentes | - | `[//]` | `.gitignore` | 🟡 | `[X]` |
| T004 | Executar `uv sync` para criar o ambiente e o `uv.lock` | T001 | - | `uv.lock` | 🟡 | `[X]` |

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T005 | Gerar o conjunto de referência de CPF e CNPJ: 20 positivos (com e sem pontuação) e 20 negativos por tipo (DV errado, dígitos repetidos, 11 ou 14 dígitos em IDs), formato `{"positives": [...], "negatives": [...]}` (D-14, Q24) | - | `[//]` | `tests/fixtures/pii_reference/cpf.json`, `cnpj.json` | 🟢 | `[X]` |
| T006 | Gerar o conjunto de referência de e-mail e telefone: 20 + 20 por tipo; negativos de telefone incluem dígitos corridos de 10 e 11 dígitos (RN-06, Q25) | - | `[//]` | `tests/fixtures/pii_reference/email.json`, `phone.json` | 🟢 | `[X]` |
| T007 | Gerar o conjunto de referência de cartão, IPv4 e IPv6: 20 + 20 por tipo; negativos de cartão falham em Luhn; negativos de IP têm octeto > 255 ou forma IPv6 malformada; sem números de versão nos negativos (R-07) | - | `[//]` | `tests/fixtures/pii_reference/card.json`, `ipv4.json`, `ipv6.json` | 🟢 | `[X]` |
| T008 | Escrever testes de `cpf_is_valid`, `cnpj_is_valid` e `luhn_is_valid`, incluindo dígitos repetidos e entradas com pontuação | T002 | `[//]` | `tests/pii/test_checksums.py` | 🟡 | `[X]` |
| T009 | Escrever o teste parametrizado do conjunto de referência: 100% dos positivos detectados por tipo e ≤ 5% de falsos positivos nos negativos (RNF de precisão) | T005, T006, T007 | - | `tests/pii/test_reference_set.py` | 🟢 | `[X]` |
| T010 | Escrever os testes dos 13 cenários Gherkin do `requirements.md#7` sobre a fachada `PiiGuard`, com `tmp_path` como pasta do dataset | T002 | `[//]` | `tests/pii/test_guard.py` | 🟡 | `[X]` |
| T011 | Escrever testes de allowlist (acréscimo, duplicados, arquivo ausente, normalização antes do hash) e de política (arquivo ausente, chave ausente, JSON inválido, regex inválida, padrão > 200 caracteres) | T002 | `[//]` | `tests/pii/test_allowlist_policy.py` | 🟡 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T012 | Implementar o domínio: `PiiType` (`str, Enum`, 8 valores), `PiiFinding`, `MaskResult` (com `fallbacks`), `Coverage` como `@dataclass(frozen=True, slots=True)` e `PolicyError(index)`, conforme `data-delta.md#1` (D-03) | T002 | - | `src/sintetica/pii/domain.py` | 🟡 | `[X]` |
| T013 | Implementar `cpf_is_valid`, `cnpj_is_valid` e `luhn_is_valid` como funções puras, rejeitando dígitos repetidos | T002 | `[//]` | `src/sintetica/pii/checksums.py` | 🟡 | `[X]` |
| T014 | Implementar `normalize(type, value) -> str` pela tabela de `data-delta.md#2` (D-10) | T012 | `[//]` | `src/sintetica/pii/normalize.py` | 🟡 | `[X]` |
| T015 | Definir os protocolos `Detector` (`type`, `find`), `SubstituteGenerator` (`generate(type, original)`) e `AllowlistStore` (`add`, `contains`) com `typing.Protocol` | T012 | - | `src/sintetica/pii/ports.py` | 🟡 | `[X]` |
| T016 | Implementar `CpfDetector`, `CnpjDetector` e `CardDetector`: regex com fronteiras de palavra, validação por `checksums`, preview de 2 caracteres + `***` (D-04, D-13, RN-03) | T013, T015 | - | `src/sintetica/pii/detectors.py` | 🟡 | `[X]` |
| T017 | Implementar `EmailDetector`, `PhoneDetector` (só formatado ou com `+55`, D-06), `IpDetector` (confirmação por `ipaddress`) e `CustomDetector` (padrões compilados) no mesmo módulo | T016 | - | `src/sintetica/pii/detectors.py` | 🟡 | `[X]` |
| T018 | Implementar `FakerSubstituteGenerator` com locale `pt_BR`, semente opcional e formato espelhado do original (pontuado ou não, `+55` ou não) (D-07, R-02) | T015 | `[//]` | `src/sintetica/pii/substitutes.py` | 🟡 | `[X]` |
| T019 | Implementar `FileAllowlistStore`: hash SHA-256 do valor normalizado, acréscimo com `fsync`, carga em `set` com remoção de duplicados (D-09, D-10) | T014, T015 | `[//]` | `src/sintetica/pii/allowlist.py` | 🟡 | `[X]` |
| T020 | Implementar `load_custom_patterns(path)`: arquivo ou chave ausente retorna lista vazia; JSON inválido, padrão > 200 caracteres ou regex que não compila geram `PolicyError` com o índice (D-11) | T012 | `[//]` | `src/sintetica/pii/policy.py` | 🟡 | `[X]` |
| T021 | Implementar `PiiGuard.scan`: executar os detectores, resolver sobreposição (mais longo vence; empate pela ordem de D-05) e processar textos > 1 MB em blocos de 64 KB com sobreposição de 64 caracteres, sem duplicar achados (D-05, D-12) | T017 | - | `src/sintetica/pii/guard.py` | 🟡 | `[X]` |
| T022 | Implementar `PiiGuard.mask` e `PiiGuard.leaks`: trocar achados de trás para frente, verificar o substituto com o próprio detector (até 5 tentativas, depois `***` do mesmo tamanho e `fallbacks += 1`), gravar o hash de cada substituto e filtrar achados da allowlist em `leaks` (D-08, RN-05, RF-08) | T021, T018, T019 | - | `src/sintetica/pii/guard.py` | 🟡 | `[X]` |
| T023 | Implementar `PiiGuard.coverage()` com os 7 tipos, a contagem de padrões custom e os limites conhecidos (nomes, endereços livres, CNPJ alfanumérico, IPv4 x números de versão, coincidência de CPF falso) e a fábrica `PiiGuard.for_dataset(dataset_dir, policy_path, seed)` | T022, T020 | - | `src/sintetica/pii/guard.py` | 🟡 | `[X]` |

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T024 | Expor a API pública em `sintetica.pii`: `PiiGuard`, `PiiType`, `PiiFinding`, `MaskResult`, `Coverage`, `PolicyError`, com `__all__` | T023 | - | `src/sintetica/pii/__init__.py` | 🟡 | `[X]` |
| T025 | Completar os testes até cobertura ≥ 80% em `sintetica.pii` e 100% em `checksums.py` e `detectors.py`, com `mypy --strict` e `ruff` sem erros (critério de pronto) | T024, T008, T009, T010, T011 | - | `tests/pii/` | 🟡 | `[X]` |
| T026 | Escrever o teste de desempenho marcado `@pytest.mark.perf`: `scan` em 10.000 registros de 1 KB com PII misturada em ≤ 30 s (RNF de desempenho, R-03) | T024 | `[//]` | `tests/pii/test_perf.py` | 🟡 | `[X]` |

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T027 | Escrever a documentação curta do módulo: uso da fachada, formato de `pii_custom_patterns` (limite de 200 caracteres e aviso de retrocesso catastrófico), tipos cobertos e limites conhecidos (R-04, R-05, R-07) | T024 | `[//]` | `docs/pii-guard.md` | 🟡 | `[X]` |

## Notas de execução

<!--
Reservado para /reversa-coding registrar avisos ou observações que surgiram durante a execução.
Não use isso para corrigir ações, edits manuais ficam fora desse arquivo, vão direto no código.
-->

- A revisão do conjunto de referência pelo Antigravity (Q24) é item do critério de pronto do roadmap, não ação do agente. Ela ocorre depois de T005 a T007.
- 2026-10-09, T017: a regex de IPv6 aceitava `::1` dentro de `gggg::1` e `z::1` (2 falsos positivos no conjunto de referência). A fronteira passou a excluir qualquer caractere de palavra.
- 2026-10-09, T018: o substituto `custom` trocava letras e quebrava prefixos fixos como `MAT-`, caindo para `***`. Com dígitos no valor, só os dígitos são trocados.
- 2026-10-09, T001: removida a chave `readme` do `pyproject.toml`, porque `docs/pii-guard.md` ainda não existia no `uv sync`. `ruff` passou a excluir `.agents`, `.claude`, `.reversa`, `_reversa_*` e `docs`.
- 2026-10-09, T025: 92 testes passam; cobertura de `sintetica.pii` em 99% (100% em `checksums.py` e `detectors.py`); `mypy --strict` e `ruff` sem erros. T026: 10.000 registros de 1 KB em 1,06 s.
- Pendente fora do agente: revisão dos 280 casos de `tests/fixtures/pii_reference/` pelo Antigravity (Q24).

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-09 | Versão inicial gerada por `/reversa-to-do` | reversa |
