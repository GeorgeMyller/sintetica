# Spec: sample-preview

> Selo 🟢 CONFORME CÓDIGO em todos os itens, salvo marcação. Fonte: `src/sintetica/sample/`, testes `tests/sample/`.
> Consolida os adendos `005-sample-preview.md`, `006-batch-generator.md` (funções públicas e próximo passo) e `008-cli-installer.md` (mensagens). Versão planejada em `sdd/_planejado/sample-preview.md`.

**Versão:** 2.0 (extraída do código)
**Status:** Implementado
**Autor:** reversa-writer
**Data:** 2026-10-12

---

## 1. Resumo

🟢 O `sample-preview` é o pacote `sintetica.sample` e a skill `sintetica-sample`. Com o contrato aprovado e atual, `sintetica sample run` pede de 3 a 5 registros ao provedor da política (o agente do harness, no padrão), valida, descarta inválidos e duplicados, troca dados pessoais por valores falsos, revalida e pede os faltantes, até 3 tentativas por rodada. O usuário aprova, ajusta ou volta ao contrato. A aprovação grava a semente que o lote usa.

## 2. Contexto

🟢 Gerar o lote sem validar o estilo antes é caro e arriscado (premissa 1 do PRD). A amostra é barata e roda sem chave (Q8).

## 3. Goals

- 🟢 G-01: Amostra validada e mascarada antes do lote.
- 🟢 G-02: Semente reutilizável pelo lote, amarrada à versão do contrato.

## 4. Non-Goals

- 🟢 NG-01: A amostra não mede diversidade; isso é da avaliação.

## 5. Usuários

🟢 Usuário (aprova), agente (gera no harness), `batch` (lê a semente).

## 6. Requisitos Funcionais

| ID | Requisito | Critério de aceite | Fonte |
|----|-----------|--------------------|-------|
| RF-01 | 🟢 Pré-condições: dataset e intenção (2); `schema.json` com `schema.state.json` `aprovado` e da mesma versão (11, cita `schema approve` ou `schema build`); `Record` e `record.schema.json` legíveis (11) | — | `service.py:85-116` |
| RF-02 | 🟢 N de 3 a 5, padrão 3; `--n` só vale ao iniciar uma rodada (senão aviso); fora do intervalo = 2 | Q41 | `state.py:19-21`, `service.py:305-329` |
| RF-03 | 🟢 Versão nova do contrato descarta a rodada anterior com aviso | — | `service.py:312-316` |
| RF-04 | 🟢 Provedor por `build_provider(k, …, harness_available=True)`; falha na escolha = 12 | — | `service.py:81-83`, `193-197` |
| RF-05 | 🟢 Pedido só com os faltantes: instruções com objetivo, estrutura e regras definidos, ajuste, "não repita os exemplos", "Responda com 1 objeto JSON por linha", "Tentativa k de 3"; aceitos como sementes | Tentativas têm ids diferentes | `request.py` |
| RF-06 | 🟢 Harness sem resposta: estado `aguardando_agente` com caminho do pedido e comando `submit` (código 0) | — | `service.py:202-209`, `266-283` |
| RF-07 | 🟢 Com a resposta, revisa e **apaga** `requests/<id>.response.jsonl` (pode ter PII) | Falha ao apagar = 10 | `service.py:171-185` |
| RF-08 | 🟢 Revisão: valida (motivo com caminho e 1º erro, sem o valor); duplicado pelo JSON canônico no mesmo lote e, após mascarar, contra os aceitos; mascara cada texto com o caminho do campo; revalida (valor falso que quebra a regra descarta); aceita até o limite | — | `review.py:48-90` |
| RF-09 | 🟢 Até 3 tentativas por rodada; `ProviderError` = 12 com a mensagem | — | `service.py:186-217` |
| RF-10 | 🟢 Fim da rodada: Expresso com N válidos aprova na mesma chamada; Expresso parcial = `interrompida` e pede decisão; Guiado parcial fica em revisão com alerta e sugestão de voltar ao contrato | Q43 | `service.py:220-237` |
| RF-11 | 🟢 Exibição: CSV em tabela Markdown (`|` escapado, casas fixas); JSON/JSONL em blocos ` ```json ` com decimal exato | — | `render.py` |
| RF-12 | 🟢 `sample approve`: estado `em_revisao` ou `interrompida`, contrato atual, ≥ 1 aceito; revalida cada aceito; grava `seeds/sample.jsonl` e `seeds/sample.meta.json`; parcial gera alerta e `partial: true`; indica `<comando> generate <slug>` | Fora disso = 13 (ou 11 com contrato mudado) | `service.py:240-263`, `364-388` |
| RF-13 | 🟢 `sample adjust <slug> '<texto>'`: mascara o texto, zera aceitos e tentativas, soma 1 rodada e roda `run`; a partir da 4ª rodada sugere voltar ao contrato; texto vazio = 2; amostra aprovada = 13 | — | `service.py:331-361` |
| RF-14 | 🟢 `sample show <slug>` mostra o estado e a amostra; sem rodada = 13 | — | `service.py:391-401` |
| RF-15 | 🟢 Funções públicas para o lote e a avaliação: `first_error`, `mask_value`, `parse_line`, `intent_lines`, `CommandResult` | — | `review.py`, `request.py`, `service.py:57` |

## 7. Requisitos Não-Funcionais

| ID | Requisito | Evidência |
|----|-----------|-----------|
| RNF-01 | 🟢 Nenhum valor de PII não mascarado na tela, no estado, na semente ou em `requests/` | `service.py:171-185`, testes com CPF |
| RNF-02 | 🟢 Escrita atômica do estado e da semente | `state.py:77-87` |

## 8. Interface

```
uv run sintetica sample run <slug> [--n 3..5]
uv run sintetica sample adjust <slug> '<pedido>'
uv run sintetica sample approve <slug>
uv run sintetica sample show <slug>
```

| Código | Significado |
|--------|-------------|
| 0 | Sucesso (inclui aguardando o agente) |
| 2 | Dataset, intenção ou argumento inválido |
| 9 | Mascaramento indisponível |
| 10 | Falha de escrita |
| 11 | Contrato não aprovado ou desatualizado |
| 12 | Falha do provedor |
| 13 | Amostra não aprovável no estado atual |

## 9. Modelo de Dados

🟢 `SampleState` (`sample.state.json`) e `SampleMeta` (`seeds/sample.meta.json`); `seeds/sample.jsonl`. Detalhe em `data-dictionary.md#módulo-sample`.

## 10. Integrações

🟢 `providers` (`build_provider`, `RequestStore`), `schema` (`Record`, `formats`), `intent`, `pii`.

## 11. Edge Cases

| Cenário | Comportamento |
|---------|---------------|
| 🟢 Resposta que não é JSON | Recusada pelo `submit` (código 5); não gasta tentativa |
| 🟢 Valor falso quebra o `pattern` | Registro descartado |
| 🟢 Registro com PII repetido entre tentativas | 🟡 Pode passar como novo (valores falsos diferem) |
| 🟢 Amostra vazia | Nunca aprovada |

## 12. Segurança e Privacidade

- 🟢 Motivos de descarte sem valores; resposta bruta apagada; ajuste mascarado.

## 13. Decisões (consolidadas)

| Decisão | Fonte |
|---------|-------|
| 🟢 Padrão 3 registros | Q41 |
| 🟢 Semente em JSONL + metadados | Q42, ADR 009 |
| 🟢 Parcial: Guiado aprova com alerta, Expresso para | Q43 |
| 🟢 Resposta bruta apagada | Decisão da execução (W006, feature 005) |

## 14. Lacunas

- 🟡 Duplicado com PII entre tentativas (RF-08).
- 🟡 Checagem do contrato duplicada com `batch/service.py`.
- 🟡 [Revisão] A instrução "Responda com 1 objeto JSON por linha" vai a todo provedor (`request.py:38`), mas o prompt de sistema dos provedores automáticos pede `{"records": [...]}` (`providers/prompt.py:10-14`). O lote já envia essa linha só ao harness (`batch/request.py:33-34`). Decisão (Q55): alinhar a amostra ao lote, com a instrução só ao harness. Correção pendente pelo `/reversa-add` na feature 005.

## Histórico

| Versão | Data | Mudança |
|--------|------|---------|
| 1.0 | 2026-10-09 | Spec planejada (`_planejado/`) |
| 2.0 | 2026-10-12 | Reescrita conforme o código; adendos 005, 006 e 008 consolidados |
