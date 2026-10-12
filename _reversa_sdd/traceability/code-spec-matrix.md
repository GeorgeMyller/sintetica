# Matriz código/spec: sintetica

> Gerado pelo Redator do Reversa em 2026-10-12. Lista cada arquivo do código e a spec que o cobre.
> 🟢 coberto pela spec · 🟡 coberto só por documento transversal · n/a sem spec.

**Cobertura:** 98 de 100 arquivos mapeados (98%).

| Arquivo do código | Spec | Cobertura |
|-------------------|------|-----------|
| `src/sintetica/__init__.py` | n/a | n/a |
| `src/sintetica/batch/__init__.py` | sdd/batch-generator.md | 🟢 |
| `src/sintetica/batch/background.py` | sdd/batch-generator.md | 🟢 |
| `src/sintetica/batch/engine.py` | sdd/batch-generator.md | 🟢 |
| `src/sintetica/batch/lock.py` | sdd/batch-generator.md | 🟢 |
| `src/sintetica/batch/output.py` | sdd/batch-generator.md | 🟢 |
| `src/sintetica/batch/plan.py` | sdd/batch-generator.md | 🟢 |
| `src/sintetica/batch/request.py` | sdd/batch-generator.md | 🟢 |
| `src/sintetica/batch/review.py` | sdd/batch-generator.md | 🟢 |
| `src/sintetica/batch/service.py` | sdd/batch-generator.md | 🟢 |
| `src/sintetica/batch/state.py` | sdd/batch-generator.md | 🟢 |
| `src/sintetica/batch/worker.py` | sdd/batch-generator.md | 🟢 |
| `src/sintetica/cli.py` | sdd/llm-provider.md (request, submit); demais specs por comando | 🟢 |
| `src/sintetica/command.py` | sdd/cli-installer.md (RF-15) | 🟢 |
| `src/sintetica/fsutil.py` | transversal (`code-analysis.md#visão-transversal`) | 🟡 |
| `src/sintetica/intent/__init__.py` | sdd/intent-interview.md | 🟢 |
| `src/sintetica/intent/answers.py` | sdd/intent-interview.md | 🟢 |
| `src/sintetica/intent/model.py` | sdd/intent-interview.md | 🟢 |
| `src/sintetica/intent/questions.py` | sdd/intent-interview.md | 🟢 |
| `src/sintetica/intent/service.py` | sdd/intent-interview.md | 🟢 |
| `src/sintetica/intent/slug.py` | sdd/intent-interview.md | 🟢 |
| `src/sintetica/intent/summary.py` | sdd/intent-interview.md | 🟢 |
| `src/sintetica/pii/__init__.py` | sdd/pii-guard.md | 🟢 |
| `src/sintetica/pii/allowlist.py` | sdd/pii-guard.md | 🟢 |
| `src/sintetica/pii/checksums.py` | sdd/pii-guard.md | 🟢 |
| `src/sintetica/pii/detectors.py` | sdd/pii-guard.md | 🟢 |
| `src/sintetica/pii/domain.py` | sdd/pii-guard.md | 🟢 |
| `src/sintetica/pii/guard.py` | sdd/pii-guard.md | 🟢 |
| `src/sintetica/pii/normalize.py` | sdd/pii-guard.md | 🟢 |
| `src/sintetica/pii/policy.py` | sdd/pii-guard.md | 🟢 |
| `src/sintetica/pii/ports.py` | sdd/pii-guard.md | 🟢 |
| `src/sintetica/pii/substitutes.py` | sdd/pii-guard.md | 🟢 |
| `src/sintetica/providers/__init__.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/data/defaults.json` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/decorators/__init__.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/decorators/budget.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/decorators/concurrency.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/decorators/masking.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/decorators/retrying.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/domain.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/errors.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/external/__init__.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/external/backends.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/external/provider.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/factory.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/harness/__init__.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/harness/provider.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/harness/store.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/models.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/policy.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/ports.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/pricing.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/prompt.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/providers/selection.py` | sdd/llm-provider.md | 🟢 |
| `src/sintetica/py.typed` | n/a | n/a |
| `src/sintetica/quality/__init__.py` | sdd/quality-evaluator.md | 🟢 |
| `src/sintetica/quality/metrics.py` | sdd/quality-evaluator.md | 🟢 |
| `src/sintetica/quality/reader.py` | sdd/quality-evaluator.md | 🟢 |
| `src/sintetica/quality/report.py` | sdd/quality-evaluator.md | 🟢 |
| `src/sintetica/quality/semantic.py` | sdd/quality-evaluator.md | 🟢 |
| `src/sintetica/quality/service.py` | sdd/quality-evaluator.md | 🟢 |
| `src/sintetica/quality/text.py` | sdd/quality-evaluator.md | 🟢 |
| `src/sintetica/sample/__init__.py` | sdd/sample-preview.md | 🟢 |
| `src/sintetica/sample/render.py` | sdd/sample-preview.md | 🟢 |
| `src/sintetica/sample/request.py` | sdd/sample-preview.md | 🟢 |
| `src/sintetica/sample/review.py` | sdd/sample-preview.md | 🟢 |
| `src/sintetica/sample/service.py` | sdd/sample-preview.md | 🟢 |
| `src/sintetica/sample/state.py` | sdd/sample-preview.md | 🟢 |
| `src/sintetica/schema/__init__.py` | sdd/schema-builder.md | 🟢 |
| `src/sintetica/schema/checks.py` | sdd/schema-builder.md | 🟢 |
| `src/sintetica/schema/codegen.py` | sdd/schema-builder.md | 🟢 |
| `src/sintetica/schema/csvflat.py` | sdd/schema-builder.md | 🟢 |
| `src/sintetica/schema/formats.py` | sdd/schema-builder.md | 🟢 |
| `src/sintetica/schema/intent.py` | sdd/schema-builder.md | 🟢 |
| `src/sintetica/schema/loader.py` | sdd/schema-builder.md | 🟢 |
| `src/sintetica/schema/names.py` | sdd/schema-builder.md | 🟢 |
| `src/sintetica/schema/render.py` | sdd/schema-builder.md | 🟢 |
| `src/sintetica/schema/service.py` | sdd/schema-builder.md | 🟢 |
| `src/sintetica/schema/spec.py` | sdd/schema-builder.md | 🟢 |
| `src/sintetica/schema/state.py` | sdd/schema-builder.md | 🟢 |
| `src/sintetica/schema/validators.py` | sdd/schema-builder.md | 🟢 |
| `src/sintetica/schema/version.py` | sdd/schema-builder.md | 🟢 |
| `src/sintetica/schema/walk.py` | sdd/schema-builder.md | 🟢 |
| `installer/bin/sintetica.js` | sdd/cli-installer.md | 🟢 |
| `installer/src/args.js` | sdd/cli-installer.md | 🟢 |
| `installer/src/detect.js` | sdd/cli-installer.md | 🟢 |
| `installer/src/files.js` | sdd/cli-installer.md | 🟢 |
| `installer/src/install.js` | sdd/cli-installer.md | 🟢 |
| `installer/src/plan.js` | sdd/cli-installer.md | 🟢 |
| `installer/src/prompt.js` | sdd/cli-installer.md | 🟢 |
| `installer/src/runtime.js` | sdd/cli-installer.md | 🟢 |
| `installer/skills/sintetica-eval/SKILL.md` | sdd/cli-installer.md | 🟢 |
| `installer/skills/sintetica-generate/SKILL.md` | sdd/cli-installer.md | 🟢 |
| `installer/skills/sintetica-sample/SKILL.md` | sdd/cli-installer.md | 🟢 |
| `installer/skills/sintetica-schema/SKILL.md` | sdd/cli-installer.md | 🟢 |
| `installer/skills/sintetica-start/SKILL.md` | sdd/cli-installer.md | 🟢 |
| `installer/templates/policy.json` | sdd/cli-installer.md | 🟢 |
| `installer/package.json` | sdd/cli-installer.md (RF-16) / `dependencies.md` | 🟢 |
| `installer/tsconfig.json` | sdd/cli-installer.md (RF-16) / `dependencies.md` | 🟢 |
| `pyproject.toml` | sdd/cli-installer.md (RF-16) / `dependencies.md` | 🟢 |

## Testes por spec

| Spec | Testes |
|------|--------|
| `sdd/pii-guard.md` | `tests/pii/` (inclui 280 casos em `tests/fixtures/pii_reference/`) |
| `sdd/llm-provider.md` | `tests/providers/`, `tests/cli/test_request_submit.py` |
| `sdd/schema-builder.md` | `tests/schema/` (inclui `-m codegen`) |
| `sdd/intent-interview.md` | `tests/intent/` |
| `sdd/sample-preview.md` | `tests/sample/` |
| `sdd/batch-generator.md` | `tests/batch/` (processo real em background; `-m perf`) |
| `sdd/quality-evaluator.md` | `tests/quality/`, `tests/batch/test_quality_chain.py` |
| `sdd/cli-installer.md` | `installer/test/`, `tests/test_command.py`, `tests/test_skills_commands.py`, `tests/test_launcher.py` |
