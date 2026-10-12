# Roadmap: pii-guard (detecção e mascaramento local de PII)

> Identificador: `001-pii-guard`
> Data: `2026-10-09`
> Requirements: `_reversa_forward/001-pii-guard/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA
> Cenário: greenfield. Não há `architecture.md`, `c4-context.md`, `state-machines.md`, `dependencies.md`, `code-analysis.md` nem `addenda/`. O delta é sobre o desenho planejado em `_reversa_sdd/sdd/pii-guard.md` e `_reversa_sdd/prd.md`.

## 1. Resumo da abordagem

🟡 Esta é a primeira feature com código. Ela cria o esqueleto do projeto Python (`pyproject.toml` gerido por `uv`, com `mypy --strict`, `ruff` e `pytest-cov`) e o pacote `sintetica.pii`.
🟡 O pacote segue Clean Architecture em 3 camadas: domínio (tipos imutáveis e funções puras de dígito verificador), portas (protocolos `Detector`, `SubstituteGenerator` e `AllowlistStore`) e adaptadores (detectores por regex, gerador de substitutos sobre Faker `pt_BR` e allowlist em arquivo).
🟡 A fachada `PiiGuard` expõe 4 operações: `scan`, `mask`, `leaks` e `coverage`. Os 5 componentes consumidores (`intent-interview`, `sample-preview`, `llm-provider`, `batch-generator`, `quality-evaluator`) importam só a fachada.
🟡 A detecção é 100% determinística: regex compiladas uma vez, validação de dígito verificador (CPF, CNPJ) e Luhn (cartão), e `ipaddress` da biblioteca padrão para IPv4 e IPv6.
🟡 A allowlist guarda o SHA-256 do valor **normalizado** (só dígitos para CPF, CNPJ, cartão e telefone; minúsculas para e-mail; forma canônica para IP). Assim, o mesmo valor com outra formatação continua reconhecido.
🟡 O conjunto de referência de 280 casos (Q24) é parte da entrega e é a prova das metas de precisão.

## 2. Princípios aplicados

🟡 `.reversa/principles.md` não existe. O `setup.json` declara `principles.enabled: true`, porém sem arquivo não há princípio a verificar. Recomendação: rodar `/reversa-principles` antes da feature 002.

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| n/a | Arquivo de princípios ausente | n/a |

🟡 Restrições do PRD tratadas como princípios de fato nesta feature: operação local (Q15), sem telemetria (Q15), tipagem estrita (PRD, seção 6), cobertura ≥ 80% (Q19). Todas são respeitadas.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Esqueleto Python na raiz: `pyproject.toml`, `src/sintetica/`, `tests/`, layout `src` | Primeira feature com código; layout `src` evita import acidental do diretório de trabalho | Layout plano; pacote em subpasta `python/` | 🟡 |
| D-02 | Python ≥ 3.10, `uv` como gerenciador, `hatchling` como backend de build | Q18; `uv` exigido no PRD | `poetry`; `setuptools` | 🟡 |
| D-03 | Tipos de domínio como `@dataclass(frozen=True, slots=True)` e `PiiType` como `enum.StrEnum`-compatível (`str, Enum`, por causa do Python 3.10) | Sem dependência extra; imutável; `mypy --strict` nativo | Pydantic no domínio (custo de validação por achado em 10.000 registros) | 🟡 |
| D-04 | 1 detector por tipo, cada um implementando o protocolo `Detector.find(text) -> list<PiiFinding>` | Teste isolado por tipo; facilita os 280 casos de referência | Uma regex única combinada | 🟡 |
| D-05 | Resolução de sobreposição: vence o achado mais longo; em empate, a ordem `card > cnpj > cpf > phone > ipv6 > ipv4 > email > custom` | Um número de cartão contém trechos que parecem CPF; o mais longo e mais específico é o correto | Reportar todos os achados sobrepostos | 🟡 |
| D-06 | Telefone só com formatação ou `+55` (RN-06) | Q25 | Dígitos corridos com DDD válido | 🟡 |
| D-07 | Substitutos via Faker `pt_BR`, com formato espelhado do original (pontuado ou não) e semente opcional | Q9 cita Faker; RF-06 e RF-09 | Asteriscos (perde o formato); gerador próprio | 🟡 |
| D-08 | Substituto gerado é verificado pelo próprio detector; se não for detectável, gera de novo (até 5 vezes) e depois cai para `***` (EC-04) | Garante que o substituto seja do mesmo tipo e formato | Confiar no Faker sem verificação | 🟡 |
| D-09 | Allowlist: arquivo texto `datasets/<slug>/.pii_allowlist`, 1 hash SHA-256 hex por linha, escrita por acréscimo com `fsync`; carregada em `set` na memória | Simples, legível, sem valores em claro (RN-04) | SQLite; JSON (reescrita total a cada acréscimo) | 🟡 |
| D-10 | Hash sobre o valor normalizado por tipo | O mesmo CPF com e sem pontuação gera o mesmo hash | Hash do texto bruto | 🟡 |
| D-11 | Padrões custom limitados a 200 caracteres e compilados no carregamento; erro gera `PolicyError` com o índice | EC-03; reduz risco de regex com retrocesso catastrófico | Biblioteca `regex` com timeout (dependência extra) | 🟡 |
| D-12 | Textos > 1 MB processados em blocos de 64 KB com sobreposição de 64 caracteres, sem achados duplicados na fronteira | EC-05 | Processar inteiro | 🟡 |
| D-13 | Prévia de achado: 2 primeiros caracteres + `***` | RF-10 | Sem prévia | 🟡 |
| D-14 | Conjunto de referência em `tests/fixtures/pii_reference/<tipo>.json`, 20 positivos + 20 negativos por tipo | Q24 | 50 + 50 por tipo | 🟢 |

> D-14 recebe 🟢 porque a decisão foi confirmada pelo revisor na Q24, não inferida.

## 4. Premissas

🟡 Nenhuma premissa vinda de `[DÚVIDA]`: o `requirements.md` está com 0 marcadores após o clarify.

| Premissa | Origem (`requirements.md` seção) | Risco se errada |
|----------|----------------------------------|-----------------|
| A máquina de desenvolvimento de referência para o RNF de desempenho é um notebook atual (4 núcleos, SSD) | 6. Requisitos Não Funcionais | Meta de 30 s pode falhar em CI lento; mitigação no item R-03 |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| Esqueleto Python | `_reversa_sdd/prd.md#6. Restrições` | componente-novo | `pyproject.toml`, configuração de `mypy`, `ruff`, `pytest`, cobertura |
| `sintetica.pii` | `_reversa_sdd/sdd/pii-guard.md` | componente-novo | Domínio, portas, adaptadores e fachada `PiiGuard` |
| Contrato Python `PiiGuard` | `_reversa_sdd/sdd/pii-guard.md#6. Requisitos Funcionais` | contrato-novo | API interna consumida por 5 componentes; ver seção 7 |

Estrutura de arquivos prevista:

```
pyproject.toml
src/sintetica/__init__.py
src/sintetica/py.typed
src/sintetica/pii/__init__.py          # exporta PiiGuard, PiiType, PiiFinding, MaskResult, Coverage, PolicyError
src/sintetica/pii/domain.py            # PiiType, PiiFinding, MaskResult, Coverage, PolicyError
src/sintetica/pii/checksums.py         # cpf_is_valid, cnpj_is_valid, luhn_is_valid (funções puras)
src/sintetica/pii/normalize.py         # normalização por tipo antes do hash
src/sintetica/pii/ports.py             # Protocols: Detector, SubstituteGenerator, AllowlistStore
src/sintetica/pii/detectors.py         # CpfDetector, CnpjDetector, EmailDetector, PhoneDetector, CardDetector, IpDetector, CustomDetector
src/sintetica/pii/substitutes.py       # FakerSubstituteGenerator
src/sintetica/pii/allowlist.py         # FileAllowlistStore
src/sintetica/pii/policy.py            # load_custom_patterns(.sintetica/policy.json)
src/sintetica/pii/guard.py             # PiiGuard: scan, mask, leaks, coverage
tests/pii/test_*.py
tests/fixtures/pii_reference/{cpf,cnpj,email,phone,card,ipv4,ipv6}.json
```

## 6. Delta no modelo de dados

- Resumo das mudanças: 🟡 3 tipos de domínio novos em memória (`PiiFinding`, `MaskResult`, `Coverage`), 1 arquivo novo por dataset (`.pii_allowlist`) e leitura da chave `pii_custom_patterns` de `.sintetica/policy.json`. Nenhuma migração.
- Detalhe completo em: `_reversa_forward/001-pii-guard/data-delta.md`

## 7. Delta de contratos externos

🟡 Nenhum contrato externo (HTTP, fila, gRPC, GraphQL). O diretório `interfaces/` não foi criado.
🟡 O contrato interno da fachada fica registrado aqui, pois 5 componentes dependem dele:

```
class PiiGuard:
    def __init__(self, allowlist: AllowlistStore, custom_patterns: Sequence<str> = (), seed: int | None = None) -> None
    def scan(self, text: str, field: str | None = None) -> list<PiiFinding>
    def mask(self, text: str, field: str | None = None) -> MaskResult        # grava hashes dos substitutos na allowlist
    def leaks(self, text: str, field: str | None = None) -> list<PiiFinding> # scan menos achados da allowlist
    def coverage(self) -> Coverage

    @classmethod
    def for_dataset(cls, dataset_dir: Path, policy_path: Path, seed: int | None = None) -> "PiiGuard"
```

## 8. Plano de migração

n/a. Projeto novo, sem dados nem código anteriores.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| R-01: Escrita fora das pastas do Reversa bloqueada: `.reversa/reversa-config.json` está com `allowLegacyEdits: false` | alto | alto | O usuário libera os caminhos `pyproject.toml`, `uv.lock`, `src/**`, `tests/**` e `.gitignore` antes do `/reversa-coding`. O Reversa não edita esse arquivo. |
| R-02: Faker sem tipagem completa quebra `mypy --strict` | médio | médio | Isolar Faker em `substitutes.py`, com override `ignore_missing_imports` só para `faker` e retorno tipado por `str()` explícito |
| R-03: Meta de 30 s para 10.000 registros falha em CI lento | baixo | médio | Teste de desempenho marcado `@pytest.mark.perf`, fora da suíte padrão; meta aferida localmente |
| R-04: Regex custom com retrocesso catastrófico trava o processo | médio | baixo | Limite de 200 caracteres (D-11) e aviso na documentação da política |
| R-05: Substituto Faker coincide com um documento real de outra pessoa | baixo | baixo | Risco inerente a CPF falso válido; documentado nos limites do `coverage()` |
| R-06: Sobreposição entre tipos gera achado errado (ex.: trecho de cartão como CPF) | médio | médio | D-05 e casos negativos cruzados no conjunto de referência |
| R-07: Falsos positivos de IPv4 em números de versão | baixo | alto | Aceito e documentado (EC-02 da spec); não entra nos negativos do conjunto de referência |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `cross-check.md` (se executado) sem CRITICAL nem HIGH
- [ ] `regression-watch.md` gerado
- [ ] Re-extração reversa executada e sem regressão vermelha (recomendado, não obrigatório)
- [ ] `uv run mypy --strict src` e `uv run ruff check` sem erros
- [ ] `uv run pytest --cov=sintetica.pii` com cobertura ≥ 80% no módulo e 100% em `checksums.py` e `detectors.py`
- [ ] Conjunto de referência: 100% dos 140 positivos detectados e ≤ 5% de falsos positivos nos 140 negativos
- [ ] Os 13 cenários Gherkin do `requirements.md` cobertos por testes
- [ ] Conjunto de referência revisado pelo Antigravity (Q24)

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-09 | Versão inicial gerada por `/reversa-plan` | reversa |
