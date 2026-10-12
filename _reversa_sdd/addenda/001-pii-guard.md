# Adendo: pii-guard (detecção e mascaramento local de PII)

> Identificador: `001-pii-guard`
> Data: `2026-10-09`
> Cenário: greenfield

## Vigência

Vigente desde 2026-10-09.
Superado pela re-extração de 2026-10-12.

## Resumo da entrega

O módulo `sintetica.pii` encontra dados pessoais identificáveis em texto e os troca por valores falsos do mesmo tipo e formato, 100% local. Ele cobre 7 tipos fixos (CPF, CNPJ, e-mail, telefone, cartão, IPv4, IPv6) e padrões extras da política do projeto. A fachada `PiiGuard` (`scan`, `mask`, `leaks`, `coverage`, `for_dataset`) é o contrato que os componentes `intent-interview`, `sample-preview`, `llm-provider`, `batch-generator` e `quality-evaluator` devem consumir.

A entrega também criou o esqueleto Python do projeto: `pyproject.toml` com `uv`, Python ≥ 3.10, `mypy --strict`, `ruff` e `pytest-cov`, em layout `src`.

Ações concluídas: 27 de 27 (`progress.jsonl` com 27 registros). Verificação: 92 testes, cobertura de 99%, 280 casos de referência aprovados pelo revisor.

## Impacto por artefato da extração

| Artefato | Seção | Tipo de impacto | Delta |
|----------|-------|-----------------|-------|
| `_reversa_sdd/prd.md` | 6. Restrições (Técnica) | componente-novo | A restrição técnica de runtime Python agora existe em código: `pyproject.toml` com `uv`, Python ≥ 3.10, `mypy --strict`, `ruff`, `pytest-cov` e layout `src/sintetica/`. |
| `_reversa_sdd/prd.md` | 3. Métricas de sucesso (vazamento de PII) | componente-novo | O critério "0 ocorrências detectadas" passa a ser medido por `PiiGuard.leaks`, que ignora valores falsos registrados por hash em `.pii_allowlist` (Q23). |
| `_reversa_sdd/sdd/pii-guard.md` | 6. Requisitos Funcionais (RF-01 a RF-03) | componente-novo | Implementados. Leia RF-03 com a regra nova: telefone só é detectado com formatação ou prefixo `+55`; dígitos corridos não contam (Q25, RN-06 da feature). |
| `_reversa_sdd/sdd/pii-guard.md` | 6. Requisitos Funcionais (RF-04) | componente-novo | Implementado. Padrões extras vêm de `pii_custom_patterns` em `.sintetica/policy.json`, com limite de 200 caracteres por padrão. |
| `_reversa_sdd/sdd/pii-guard.md` | 6. Requisitos Funcionais (RF-05, RF-06, RF-09) | componente-novo | Implementados como `scan`, `mask` e semente opcional. Leia `mask` como idempotente: valores já presentes na allowlist não são trocados de novo. |
| `_reversa_sdd/sdd/pii-guard.md` | 6. Requisitos Funcionais (RF-07, RF-08) | componente-novo | Implementados. O hash SHA-256 é calculado sobre o valor normalizado por tipo, e não sobre o texto bruto (ver `data-delta.md` da feature). |
| `_reversa_sdd/sdd/pii-guard.md` | 6. Requisitos Funcionais (RF-10, RF-11) | componente-novo | Implementados. A prévia mostra 2 caracteres + `***`; `coverage()` lista 7 tipos, padrões extras e 6 limites conhecidos. |
| `_reversa_sdd/sdd/pii-guard.md` | 9. Modelo de Dados | componente-novo | Leia `MaskResult` com o campo extra `fallbacks` e `PiiGuard` com a propriedade `allowlist_available` (EC-04 e EC-06). |
| `_reversa_sdd/sdd/pii-guard.md` | 14. Open Questions (OQ-01, OQ-02) | componente-novo | Resolvidas: OQ-01 pela Q23 (allowlist por hash) e OQ-02 pela Q24 (280 casos em `tests/fixtures/pii_reference/`). |
| `_reversa_sdd/sdd/intent-interview.md`, `sample-preview.md`, `llm-provider.md`, `batch-generator.md`, `quality-evaluator.md` | 10. Integrações e Dependências (`pii-guard`) | componente-novo | A dependência `pii-guard` citada nessas specs já existe; consuma a fachada `sintetica.pii.PiiGuard` e trate `PolicyError` e exceções de escrita como falha segura. |

## Regras sob vigilância

W001, W002, W003, W004, W005, W006, W007, W008, W009, W010. Todos em "Observações", sem peso de regressão (cenário greenfield). Detalhes em `_reversa_forward/001-pii-guard/regression-watch.md`.

## Fontes

- `_reversa_forward/001-pii-guard/legacy-impact.md`
- `_reversa_forward/001-pii-guard/regression-watch.md`
- `_reversa_forward/001-pii-guard/requirements.md`
- `_reversa_forward/001-pii-guard/data-delta.md`
- `_reversa_forward/001-pii-guard/progress.jsonl`
- `_reversa_forward/001-pii-guard/actions.md`
