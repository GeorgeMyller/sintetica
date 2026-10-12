## Módulo `intent` (`src/sintetica/intent/`)

🟢 **Propósito:** entrevista de intenção da skill `sintetica-start`. Cria a pasta do dataset e o `intent.json` com `started_at` antes da 1ª pergunta; valida, mascara e grava cada resposta; decide quando a intenção precisa de confirmação e indica o próximo passo.

### Arquivos

| Arquivo | Papel |
|---------|-------|
| `model.py` | `IntentModel`, `Item`, constantes (formatos, volume, padrões), `load_intent_model`, `save_intent` |
| `answers.py` | `Answers`, `apply_answers`, `parse_volume`, `PiiGuardMasker`, `InvalidAnswer`, `MaskingUnavailable` |
| `questions.py` | As 5 perguntas com exemplos por persona; `render_questions` |
| `slug.py` | `base_slug`, `create_dataset_dir` |
| `summary.py` | `missing_items`, `is_complete`, `is_critical`, `needs_confirmation`, `is_ready`, `render_summary` |
| `service.py` | `start`, `questions`, `set_answers`, `show`, `confirm` |

### Funções e métodos principais

| Função | Assinatura | Retorno | Local |
|--------|-----------|---------|-------|
| `start` | `(project_dir, name, mode="guiado", now=None)` | `CommandResult` (0, 10) | `service.py:52` |
| `set_answers` | `(project_dir, slug, answers, masker_factory=None)` | `CommandResult` (0, 2, 8, 9, 10) | `service.py:105` |
| `confirm` | `(project_dir, slug, now=None)` | `CommandResult` (0, 2, 8, 10) | `service.py:154` |
| `apply_answers` | `(intent, answers, masker_factory)` | `(IntentModel, avisos)` ou `InvalidAnswer`/`MaskingUnavailable` | `answers.py:100` |
| `parse_volume` | `(raw)` | `int \| None` | `answers.py:92` |
| `create_dataset_dir` | `(datasets_dir, name, now)` | `(slug, path)` | `slug.py:20` |
| `render_summary` | `(intent, dataset_dir)` | linhas | `summary.py:62` |
| `load_intent_model` | `(dataset_dir)` | `IntentModel` ou `IntentError` | `model.py:74` |

### Algoritmos e regras

1. 🟢 **Início antes da 1ª pergunta** (`service.py:52-75`): cria `datasets/`, a pasta do dataset, `seeds/` e o `intent.json` com `started_at` em UTC; mostra o caminho absoluto e o comando `intent questions`.
2. 🟢 **Slug sem corrida** (`slug.py`): NFKD → ASCII → kebab-case, até 60 caracteres; sem nome útil, `dataset-AAAAMMDD-HHMMSS`; pasta existente tenta `-2`, `-3`… com `mkdir(exist_ok=False)`.
3. 🟢 **Respostas tudo ou nada** (`answers.py:100-174`): textos vazios são erro (sugere `--unknown`); formato fora de CSV/JSON/JSONL é erro; volume aceito de 1 a 10.000 com `2000`, `2.000` ou `2 000`; qualquer erro levanta `InvalidAnswer` e nada é gravado, exceto o contador de recusas de volume.
4. 🟢 **Volume recusado 3 vezes** (`answers.py:119-135`): na 3ª recusa seguida, grava o padrão 10 com aviso.
5. 🟢 **"Não sei"** (`answers.py:137-146`): formato vira JSONL e volume vira 10, marcados como padrão (Q38); itens de texto viram `indefinido`.
6. 🟢 **Mascaramento antes de gravar** (`answers.py:152-170`): objetivo, estrutura e regras passam pelo `PiiGuard.mask` com o nome do item como campo; o aviso cita item e tipos com contagem (`e-mail (1)`), nunca o valor; política inválida ou falha de escrita da allowlist viram `MaskingUnavailable` (código 9).
7. 🟢 **Confirmação** (`summary.py:31-34`, `answers.py:172-173`): qualquer resposta nova zera `confirmed_at`; o Guiado sempre confirma a intenção completa; o Expresso só confirma quando objetivo **e** estrutura são indefinidos (Q39).
8. 🟢 **Próximo passo** (`summary.py:62-83`): `Faltam: …`, `Confirme …` ou `Próximo passo: <comando> schema build <slug>`; textos longos aparecem cortados em 80 caracteres no resumo.

### Tratamento de erros

🟢 `IntentError` (intenção ausente ou ilegível, código 2); `InvalidAnswer(messages, intent)` (código 8); `MaskingUnavailable` (código 9); `OSError` na gravação (código 10, com o caminho).

### Constantes

| Constante | Valor | Local |
|-----------|-------|-------|
| `FORMATS` | `csv`, `json`, `jsonl` | `model.py:24` |
| `DEFAULT_FORMAT`, `DEFAULT_VOLUME` | `jsonl`, 10 | `model.py:25-26` |
| `MIN_VOLUME`, `MAX_VOLUME` | 1, 10.000 | `model.py:27-28` |
| `MAX_VOLUME_REJECTIONS` | 3 | `answers.py:23` |
| `MAX_SLUG` | 60 | `slug.py:10` |
| `MAX_SHOWN` | 80 | `summary.py:10` |

### Dependências

🟢 Pydantic; módulo `pii`; `sintetica.command`, `sintetica.fsutil`.
