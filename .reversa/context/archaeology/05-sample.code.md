## Módulo `sample` (`src/sintetica/sample/`)

🟢 **Propósito:** amostra de 3 a 5 registros para aprovação antes do lote (skill `sintetica-sample`). Pede os registros ao provedor da política (o harness, no padrão), valida pelo contrato, descarta inválidos e duplicados, mascara PII, revalida e pede os faltantes, até 3 tentativas por rodada. A aprovação grava a semente usada pelo lote.

### Arquivos

| Arquivo | Papel |
|---------|-------|
| `state.py` | `SampleState`, `SampleMeta`, constantes, `load_sample_state`, `save_sample_state`, `write_seeds` |
| `request.py` | `intent_lines`, `build_instructions`, `build_request` |
| `review.py` | `review_records`, `first_error`, `mask_value`, `parse_line`, `ReviewResult` |
| `render.py` | `render_records`: tabela Markdown (CSV) ou blocos JSON |
| `service.py` | `run`, `adjust`, `approve`, `show`; laço de tentativas |

### Funções e métodos principais

| Função | Assinatura | Retorno | Local |
|--------|-----------|---------|-------|
| `run` | `(project, slug, n=None, provider_factory=None)` | `CommandResult` (0, 2, 9, 10, 11, 12) | `service.py:305` |
| `adjust` | `(project, slug, text, provider_factory=None)` | `CommandResult` (0, 2, 13…) | `service.py:331` |
| `approve` | `(project, slug)` | `CommandResult` (0, 11, 13) | `service.py:364` |
| `show` | `(project, slug)` | `CommandResult` | `service.py:391` |
| `review_records` | `(raw, model, existing, masker, limit)` | `ReviewResult(accepted, rejected)` | `review.py:48` |
| `build_request` | `(intent, schema_json, accepted, k, attempt, adjustment)` | `GenerationRequest` | `request.py:44` |
| `write_seeds` | `(dataset_dir, lines, meta)` | `(sample.jsonl, sample.meta.json)` | `state.py:83` |

### Algoritmos e regras

1. 🟢 **Pré-condições** (`service.py:85-116`): dataset e intenção (2); `schema.json` presente, `schema.state.json` com `status = aprovado` e a mesma versão do contrato (11, cita `schema approve` ou `schema build`); `Record` e `record.schema.json` legíveis (11).
2. 🟢 **N da amostra** (`state.py:19-21`, `service.py:305-329`): 3 a 5, padrão 3 (Q41); `--n` só vale ao iniciar uma rodada; versão nova do contrato descarta a rodada anterior com aviso.
3. 🟢 **Laço de tentativas** (`service.py:167-217`): se há pedido pendente, lê a resposta do harness; sem resposta, mantém `aguardando_agente`; com resposta, revisa e **apaga a resposta bruta** (`requests/<id>.response.jsonl`), que pode ter PII. Enquanto faltarem registros e houver tentativas (até 3), monta pedido só com os faltantes e chama o provedor; `HarnessResponsePending` grava o estado `aguardando_agente` com o comando `submit`; `ProviderError` vira código 12.
4. 🟢 **Pedido único por tentativa** (`request.py:29-56`): instruções com objetivo, estrutura e regras definidos, o ajuste, "tentativa k de 3" e os aceitos como sementes ("não repita"). O número da tentativa muda o id do pedido do harness, que de outro modo devolveria a resposta antiga.
5. 🟢 **Revisão** (`review.py:48-90`): valida com o `Record`; motivo do descarte traz só o 1º erro com o caminho, nunca o valor; duplicado pelo JSON canônico antes do mascaramento (no mesmo lote) e depois (contra os aceitos); mascara cada texto com o caminho do campo (`mask_value`); revalida; valor falso que quebra a regra descarta o registro; aceita até o limite pedido.
6. 🟢 **Fim da rodada** (`service.py:220-237`): Expresso com N válidos aprova na mesma chamada; Expresso parcial vai para `interrompida` e pede decisão; Guiado parcial fica em revisão com alerta e sugestão de voltar ao contrato (Q43).
7. 🟢 **Aprovação** (`service.py:240-263`, `364-388`): exige estado `em_revisao` ou `interrompida`, contrato atual e ≥ 1 registro; revalida cada aceito; grava `seeds/sample.jsonl` e `seeds/sample.meta.json`; parcial gera alerta e `partial: true`; indica `<comando> generate <slug>` como próximo passo.
8. 🟢 **Ajuste** (`service.py:331-361`): mascara o texto do ajuste, zera aceitos e tentativas, soma 1 rodada e executa `run`; a partir da 4ª rodada sugere voltar ao contrato.
9. 🟢 **Exibição** (`render.py`): CSV vira tabela Markdown com `|` escapado e casas fixas; JSON/JSONL viram blocos ` ```json ` com `to_json_text(indent=2)` e decimal exato.

### Tratamento de erros

🟢 Padrão `_Fail(code, message)` capturado em cada comando; mascaramento indisponível (9) antes de gravar; falha de escrita (10) com a causa; `provider_factory` que falha na escolha vira 12.

### Constantes

| Constante | Valor | Local |
|-----------|-------|-------|
| `MIN_N`, `MAX_N`, `DEFAULT_N` | 3, 5, 3 | `state.py:19-21` |
| `MAX_ATTEMPTS` | 3 por rodada | `state.py:22` |
| `ADJUST_SUGGEST_FROM` | 4 | `service.py:50` |
| Códigos próprios | 11, 12, 13 | `service.py:46-48` |

### Limite conhecido

🟡 Registro com PII repetido entre tentativas pode passar como novo, porque os valores falsos diferem (nota da feature 005).

### Dependências

🟢 `intent`, `schema`, `providers`, `pii`, `fsutil`, `command`.
