# Lacunas: sintetica

> Gerado pelo Revisor do Reversa em 2026-10-12. Nível: completo.
> Perguntas correspondentes em `questions.md` (Etapa 15, Q53 a Q56), respondidas e processadas em 2026-10-12. Nenhuma lacuna bloqueia a reimplementação a partir das specs.

| ID | Lacuna | Confiança | Specs afetadas | Pergunta |
|----|--------|-----------|----------------|----------|
| G-01 | Ramo Windows (trava, processo em background, lançador `.cmd`) sem teste real. Decisão: declarar experimental até haver runner Windows em CI | 🟡 (era 🔴) | `sdd/batch-generator.md`, `sdd/cli-installer.md` | Q53 |
| G-02 | Diversidade temática e distribuição de valores não medidas. Decisão: manter as métricas vigentes no MVP; dispersão temática no roadmap | 🟢 (era 🔴) | `sdd/quality-evaluator.md`, `domain.md` | Q54 |
| G-03 | Amostra manda "1 objeto JSON por linha" a provedores automáticos, em conflito com o prompt de sistema. Decisão: instrução só ao harness, como no lote; correção pendente | 🟡 | `sdd/sample-preview.md` | Q55 |
| G-04 | `schema build` não confere a confirmação da intenção. Decisão: validar `confirmed_at` no `build`; correção pendente | 🟡 | `sdd/schema-builder.md`, `sdd/intent-interview.md` | Q56 |
| G-05 | Registro com PII repetido entre tentativas ou depois de uma retomada pode passar como novo | 🟡 | `sdd/sample-preview.md`, `sdd/batch-generator.md` | — (limite aceito nas features 005 e 006) |
| G-06 | Duplicações: `write_atomic` (3 cópias), `CommandResult` (3), checagem de contrato (2), ciclo `batch`↔`quality` contornado | 🟡 | `architecture.md#7` | — (candidato a `/reversa-refactor`) |
| G-07 | Estimativa de custo ignora tokens de entrada | 🟡 | `sdd/llm-provider.md` | — (o teto contém; Q33) |
| G-08 | Modelos padrão podem expirar | 🟡 | `sdd/llm-provider.md` | — (override por variável) |

## Ações decorrentes das respostas

| Lacuna | Ação | Onde |
|--------|------|------|
| G-01 | Marcar o Windows como experimental nos guias de uso (`docs/batch-generator.md`, `docs/cli-installer.md`) | Fora das pastas do Reversa: pelo ciclo forward |
| G-02 | Registrar "dispersão temática" como evolução no roadmap do produto | `prd.md` ou próxima feature |
| G-03 | Enviar a instrução de linhas só ao harness em `sample/request.py` | `/reversa-add` na feature 005 |
| G-04 | Exigir `confirmed_at` no `schema build` (código 2 com o comando `intent confirm`) | `/reversa-add` na feature 003 |
