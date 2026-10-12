# Spec: intent-interview

> Selo 🟢 CONFORME CÓDIGO em todos os itens, salvo marcação. Fonte: `src/sintetica/intent/`, testes `tests/intent/`.
> Consolida o adendo `004-intent-interview.md`. Versão planejada em `sdd/_planejado/intent-interview.md`.

**Versão:** 2.0 (extraída do código)
**Status:** Implementado
**Autor:** reversa-writer
**Data:** 2026-10-12

---

## 1. Resumo

🟢 O `intent-interview` é o pacote `sintetica.intent` e a skill `sintetica-start`. `sintetica start` cria a pasta do dataset e o `intent.json` com `started_at` antes de qualquer pergunta. O agente conduz a conversa e registra cada resposta com `sintetica intent set`; o runtime valida, mascara PII, aplica os padrões de "não sei", decide quando confirmar e indica o próximo passo.

## 2. Contexto

🟢 O usuário descreve o dataset sem jargão (Q2, Q13). Pode responder "não sei" sem travar (PRD). A medição de tempo começa no início da entrevista (Q20). Respostas podem ter dados pessoais (Q21).

## 3. Goals

- 🟢 G-01: Pasta e `started_at` antes da 1ª pergunta.
- 🟢 G-02: Nenhum dado pessoal detectável gravado na intenção.
- 🟢 G-03: Modos Guiado e Expresso com as regras de confirmação da Q39.

## 4. Non-Goals

- 🟢 NG-01: O runtime não faz perguntas; só valida e grava. A conversa é do agente.

## 5. Usuários

🟢 As 3 personas, pelo agente; consumidores: `schema`, `sample`, `batch`, `quality`.

## 6. Requisitos Funcionais

| ID | Requisito | Critério de aceite | Fonte |
|----|-----------|--------------------|-------|
| RF-01 | 🟢 `start [nome] [--mode guiado\|expresso]` cria `datasets/<slug>/`, `seeds/` e `intent.json` com `started_at` (UTC); mostra slug, caminho absoluto, início da medição e o próximo comando | Falha de escrita = código 10 com o caminho | `service.py:52-75` |
| RF-02 | 🟢 Slug kebab-case ASCII de até 60 caracteres; sem nome útil, `dataset-AAAAMMDD-HHMMSS`; pasta existente tenta `-2`, `-3`… sem corrida | `Pedidos de Café` → `pedidos-de-cafe` | `slug.py` |
| RF-03 | 🟢 `intent questions --mode` mostra as 5 perguntas sem jargão (objetivo, estrutura, regras, formato, volume), com 1 exemplo por persona; Guiado 1 por vez, Expresso num bloco | — | `questions.py` |
| RF-04 | 🟢 `intent set <slug>` com `--objective`, `--structure`, `--rules`, `--format`, `--volume` e `--unknown <item>` (repetível); nenhum item ou item com `--unknown` junto = código 2 | — | `service.py:105-117`, `cli.py` |
| RF-05 | 🟢 Validação tudo ou nada: texto vazio é erro (sugere `--unknown`); formato fora de CSV/JSON/JSONL é erro; volume de 1 a 10.000, aceita `2000`, `2.000`, `2 000` | Código 8; nada gravado, salvo o contador de recusas | `answers.py:100-150` |
| RF-06 | 🟢 Na 3ª recusa seguida de volume, grava o padrão 10 com aviso | — | `answers.py:119-135` |
| RF-07 | 🟢 "Não sei": formato → JSONL e volume → 10, marcados `(padrão)`; texto → `indefinido` | Q38 | `answers.py:137-146` |
| RF-08 | 🟢 Objetivo, estrutura e regras passam por `PiiGuard.mask` com o nome do item como campo; o aviso cita item e tipos com contagem, nunca o valor; `pii_masked = true` | Política inválida ou falha da allowlist = código 9, nada gravado | `answers.py:152-170` |
| RF-09 | 🟢 Qualquer resposta nova zera `confirmed_at` | — | `answers.py:172-173` |
| RF-10 | 🟢 Resumo: itens com status e texto (até 80 caracteres), formato e volume com origem, e a última linha: `Faltam: …`, `Confirme …` ou `Próximo passo: <comando> schema build <slug>` | — | `summary.py:62-83` |
| RF-11 | 🟢 Confirmação: Guiado sempre que completa; Expresso só com objetivo **e** estrutura indefinidos (aviso de contrato genérico) | Q39 | `summary.py:26-38` |
| RF-12 | 🟢 `intent confirm <slug>` exige intenção completa (senão código 8 com os itens que faltam) e grava `confirmed_at` | — | `service.py:154-168` |
| RF-13 | 🟢 `intent show <slug>` mostra o resumo | — | `service.py:146-151` |
| RF-14 | 🟢 `intent.json` preserva chaves desconhecidas (`extra="allow"`) | Chaves de outras features sobrevivem a novas respostas | `model.py:46-48` |
| RF-15 | 🟢 Mensagens citam o comando de quem chamou (`cli_command()`) | — | `service.py`, `summary.py`, `model.py` |

## 7. Requisitos Não-Funcionais

| ID | Requisito | Evidência |
|----|-----------|-----------|
| RNF-01 | 🟢 Escrita atômica do `intent.json` | `model.py:84-86` (`fsutil.write_atomic`) |
| RNF-02 | 🟢 Privacidade: nenhuma resposta gravada sem mascaramento | `answers.py:152-170` |

## 8. Interface

```
uv run sintetica start '<nome>' [--mode expresso]
uv run sintetica intent questions [--mode expresso]
uv run sintetica intent set <slug> --objective '...' --structure '...' --rules '...' --format json --volume 50 [--unknown rules]
uv run sintetica intent show <slug>
uv run sintetica intent confirm <slug>
```

| Código | Significado |
|--------|-------------|
| 0 | Sucesso |
| 2 | Dataset ou intenção ausente; uso inválido |
| 8 | Resposta inválida; confirmação com intenção incompleta |
| 9 | Mascaramento de PII indisponível |
| 10 | Falha de escrita |

## 9. Modelo de Dados

🟢 `IntentModel` (`slug`, `mode`, `started_at`, `objective`/`structure`/`rules` como `Item(status, text)`, `format`, `format_source`, `volume`, `volume_source`, `volume_rejections`, `pii_masked`, `confirmed_at`). Detalhe em `data-dictionary.md#módulo-intent`.

## 10. Integrações

🟢 `pii` (mascaramento). Consumidores: `schema` (lê formato, modo e estrutura), `sample` e `batch` (modo, textos, volume), `quality` (`started_at`, volume).

## 11. Edge Cases

| Cenário | Comportamento |
|---------|---------------|
| 🟢 2 datasets com o mesmo nome | `-2`, `-3`… |
| 🟢 Volume `abc` 3 vezes | Padrão 10 com aviso |
| 🟢 Texto com e-mail | Trocado por e-mail falso; aviso `e-mail (1)` |
| 🟢 Resposta depois da confirmação | Exige nova confirmação |

## 12. Segurança e Privacidade

- 🟢 Os textos gravados já estão mascarados; os valores falsos entram na allowlist do dataset.

## 13. Decisões (consolidadas)

| Decisão | Fonte |
|---------|-------|
| 🟢 Padrões JSONL e 10 para "não sei" | Q38 |
| 🟢 Confirmação do Expresso só no caso crítico | Q39 |
| 🟢 Encadeamento progressivo do Expresso | Q40, ADR 008 |
| 🟢 Medição de tempo a partir do `start` | Q20 |

## 14. Lacunas

- 🟡 A confirmação não é exigida pelo `schema build` (ver `schema-builder.md#14`). Decisão (Q56): o `build` vai exigir `confirmed_at`. Correção pendente.

## Histórico

| Versão | Data | Mudança |
|--------|------|---------|
| 1.0 | 2026-10-09 | Spec planejada (`_planejado/`) |
| 2.0 | 2026-10-12 | Reescrita conforme o código; adendo 004 consolidado |
