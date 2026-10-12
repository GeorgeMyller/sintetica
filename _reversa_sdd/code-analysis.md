# Análise de código: sintetica

> Gerado pelo Arqueólogo do Reversa em 2026-10-12. Nível: completo.
> Confiança: 🟢 CONFIRMADO (lido do código), 🟡 INFERIDO, 🔴 LACUNA.
> Fluxogramas em `_reversa_sdd/flowcharts/<módulo>.md`; dicionário em `_reversa_sdd/data-dictionary.md`.

## Visão transversal

### Linha de comando (`src/sintetica/cli.py`)

🟢 `main(argv)` monta um `argparse` com 9 comandos e importa cada serviço de forma tardia (só o comando chamado carrega o seu pacote). Cada serviço devolve `CommandResult(code, out, err)`; `_print_result` imprime `out` na saída padrão e `err` na saída de erro, com `erro:` na 1ª linha.

| Comando | Serviço | Módulo |
|---------|---------|--------|
| `request <slug> --n-records --instructions --schema [--seeds]` | `_request` (grava pedido do harness) | `providers.harness` |
| `submit <slug> <id>` (JSONL na entrada padrão) | `_submit` | `providers.harness` |
| `schema build \| show \| approve <slug>` | `schema.service` | `schema` |
| `start [nome] [--mode]` | `intent.service.start` | `intent` |
| `intent questions \| set \| show \| confirm` | `intent.service` | `intent` |
| `sample run [--n] \| adjust \| approve \| show` | `sample.service` | `sample` |
| `generate <slug> [--resume] [--new] [--authorize-usd] [--block-size]` | `batch.service.generate` | `batch` |
| `status <slug>` | `batch.service.status` | `batch` |
| `eval <slug>` | `quality.service.evaluate` | `quality` |

🟢 Todos aceitam `--project-dir` (padrão: pasta atual).

### Códigos de saída do runtime

| Código | Significado | Origem |
|--------|-------------|--------|
| 0 | Sucesso (no `eval`: `APROVADO`) | todos |
| 2 | Dataset, intenção ou argumento inválido | todos |
| 3 | Limite do harness (> 100 registros no `request`) | `cli.py` |
| 4, 5 | Pedido inexistente; resposta inválida no `submit` | `providers.harness.store` |
| 6, 7 | Definição de contrato inválida; código gerado inválido ou desatualizado | `schema` |
| 8 | Resposta inválida na entrevista | `intent` |
| 9 | Mascaramento ou detecção de PII indisponível | `intent`, `sample`, `batch`, `quality` |
| 10 | Falha de escrita | `intent`, `sample`, `batch`, `quality` |
| 11 | Contrato não aprovado, desatualizado ou ilegível | `sample`, `batch`, `quality` |
| 12 | Falha do provedor | `sample`, `batch` |
| 13 | Amostra não aprovável | `sample` |
| 14 | Amostra ausente ou de outra versão do contrato | `batch` |
| 15 | Custo exige autorização | `batch` |
| 16 | Lote em andamento, interrompido ou existente | `batch`, `quality` |
| 17 | Dataset `REPROVADO` | `quality` |
| 18 | Dataset final ausente ou ilegível | `quality` |

🟢 O instalador Node tem só 0 e 1.

### Padrões repetidos

- 🟢 **Pasta por dataset:** todo estado vive em `datasets/<slug>/`, gravado por `write_atomic` (temporário + `os.replace`).
- 🟢 **Prefixo de comando:** `sintetica.command.cli_command()` lê `SINTETICA_CMD` (lançador) e devolve `uv run sintetica` sem ela; 40 mensagens usam a função.
- 🟢 **Privacidade:** motivos de descarte e achados de PII nunca carregam o valor; respostas brutas do harness são apagadas depois de lidas; logs do background só têm contagens.
- 🟡 **Duplicações:** `write_atomic` em 3 cópias (`fsutil.py`, `schema/state.py`, `providers/harness/store.py`); `CommandResult` definido em `schema/service.py`, `intent/service.py` e `sample/service.py` (este reusado por `batch` e `quality`); o padrão `_Fail(code, message)` repetido em `sample`, `batch` e `quality`; a checagem de contrato (`_context`) repetida em `sample` e `batch`.
- 🟡 **Lacuna conhecida:** `schema build` não confere `confirmed_at` da intenção (`schema/intent.py` lê a intenção sem o `IntentModel`).

### Dependências entre módulos

```
pii ◄── providers ◄── sample ◄── batch ──► quality
 ▲          ▲           ▲  ▲        │          │
 │          │           │  └── intent ◄────────┤
 └──────────┴── schema ◄┴──────────────────────┘
installer (Node) ──► gera o lançador que chama o runtime (SINTETICA_CMD)
```

🟢 `batch` importa `quality` de forma tardia (dentro de `_execute`) para evitar ciclo, porque `quality` usa `batch.state` e `batch.lock`.

## Módulo `pii` (`src/sintetica/pii/`)

🟢 **Propósito:** detectar dados pessoais (PII) em texto e trocá-los por valores falsos do mesmo tipo e formato, 100% local. A fachada `PiiGuard` é consumida por `intent`, `sample`, `providers` (decorador de mascaramento), `batch` e `quality`.

### Arquivos

| Arquivo | Papel |
|---------|-------|
| `domain.py` | `PiiType`, `FIXED_TYPES`, `PiiFinding`, `MaskResult`, `Coverage`, `PolicyError`, `make_preview` |
| `ports.py` | Protocolos `Detector`, `SubstituteGenerator`, `AllowlistStore` |
| `detectors.py` | 7 detectores por regex com validação, mais `CustomDetector` |
| `checksums.py` | Dígitos verificadores de CPF e CNPJ (módulo 11) e Luhn |
| `normalize.py` | Normalização por tipo antes do hash da allowlist |
| `substitutes.py` | `FakerSubstituteGenerator` (Faker `pt_BR`), formato espelhado |
| `allowlist.py` | `FileAllowlistStore`: arquivo `.pii_allowlist`, 1 SHA-256 por linha |
| `policy.py` | `load_custom_patterns` de `.sintetica/policy.json` |
| `guard.py` | `PiiGuard`: `scan`, `mask`, `leaks`, `coverage`, `for_dataset` |

### Funções e métodos principais

| Função | Assinatura | Retorno | Local |
|--------|-----------|---------|-------|
| `PiiGuard.for_dataset` | `(dataset_dir, policy_path, seed=None)` | `PiiGuard` | `guard.py:74` |
| `PiiGuard.scan` | `(text, field=None)` | `list[PiiFinding]` | `guard.py:89` |
| `PiiGuard.mask` | `(text, field=None)` | `MaskResult` | `guard.py:127` |
| `PiiGuard.leaks` | `(text, field=None)` | `list[PiiFinding]` fora da allowlist | `guard.py:146` |
| `PiiGuard.coverage` | `()` | `Coverage` | `guard.py:153` |
| `load_custom_patterns` | `(path)` | `tuple[str, ...]` | `policy.py:14` |
| `cpf_is_valid`, `cnpj_is_valid`, `luhn_is_valid` | `(value)` | `bool` | `checksums.py:36,44,65` |
| `fingerprint` | `(pii_type, value)` | SHA-256 hex do valor normalizado | `allowlist.py:15` |

### Algoritmos

1. 🟢 **Detecção por regex com fronteiras** (`detectors.py:42-64`): cada regex usa lookbehind/lookahead para não casar dentro de sequências maiores de dígitos (`(?<!\d)(?<!\d[./-])…(?!\d)(?![./-]\d)`).
2. 🟢 **Validação pós-regex:** CPF e CNPJ por módulo 11 com pesos fixos (`checksums.py:10-49`), rejeitando dígitos todos iguais; cartão por Luhn com 13 a 19 dígitos (`detectors.py:67`); telefone com 10 ou 11 dígitos e DDD ≥ 11, descontando o `55` do prefixo `+55` (`detectors.py:72`); IPv4 e IPv6 pelo `ipaddress` (`detectors.py:79-94`).
3. 🟢 **Telefone só formatado** (`detectors.py:52-61`): exige DDD entre parênteses, DDD seguido de espaço ou hífen, ou prefixo `+55`. Dígitos corridos não contam (Q25).
4. 🟢 **Resolução de sobreposição** (`guard.py:47-53`): ordena os achados por tamanho decrescente, depois pela prioridade `CARD < CNPJ < CPF < PHONE < IPV6 < IPV4 < EMAIL < CUSTOM`, depois pelo início; aceita cada achado que não cruza um já aceito.
5. 🟢 **Varredura em blocos** (`guard.py:98-110`): textos acima de 1 MiB são lidos em janelas de 64 KiB com 64 caracteres de sobreposição; um achado só conta na janela onde começa.
6. 🟢 **Mascaramento** (`guard.py:127-144`): percorre os achados do fim para o começo (os índices continuam válidos); pula valores já na allowlist (idempotência); gera substituto até 5 vezes, exigindo que seja diferente do original e detectável pelo mesmo detector de ponta a ponta; registra o hash do substituto na allowlist; se as 5 tentativas falharem, troca por `*` do mesmo tamanho e conta 1 `fallback`.
7. 🟢 **Substitutos com formato espelhado** (`substitutes.py:13-81`): `_lay_digits` troca só os dígitos do original e mantém a pontuação; telefone mantém `+55` e gera celular (9 + 8 dígitos) ou fixo (2 a 5 + dígitos); cartão começa com 4 e fecha com o dígito de Luhn; padrão extra com dígitos troca só os dígitos (mantém prefixos como `MAT-`), sem dígitos troca letras mantendo a caixa.
8. 🟢 **Normalização para o hash** (`normalize.py:11-23`): CPF, CNPJ e cartão só dígitos; telefone só dígitos sem `55` inicial (12 ou 13 dígitos); e-mail em minúsculas sem espaços; IP na forma canônica do `ipaddress`.

### Tratamento de erros

- 🟢 `PolicyError(index, msg)`: política ausente vale como sem padrões; JSON inválido, não objeto, lista inválida, padrão vazio, acima de 200 caracteres ou regex inválida geram erro (`policy.py:14-36`).
- 🟢 Falha do Faker ao gerar substituto é registrada em log e conta como tentativa (`guard.py:120-122`).
- 🟢 A gravação da allowlist faz `flush` e `fsync` a cada hash novo (`allowlist.py:37-46`).

### Constantes de domínio

| Constante | Valor | Local |
|-----------|-------|-------|
| `CHUNK_THRESHOLD` | 1 MiB | `guard.py:32` |
| `CHUNK_SIZE`, `CHUNK_OVERLAP` | 64 KiB, 64 | `guard.py:33-34` |
| `MAX_SUBSTITUTE_ATTEMPTS` | 5 | `guard.py:35` |
| `KNOWN_LIMITS` | 6 limites textuais | `guard.py:37-44` |
| `MAX_PATTERN_LENGTH` | 200 | `policy.py:11` |
| `ALLOWLIST_FILENAME` | `.pii_allowlist` | `allowlist.py:12` |
| Prévia | 2 primeiros caracteres + `***` | `domain.py:71-73` |

### Dependências

🟢 Faker (`pt_BR`). Nenhum outro módulo do `sintetica`.


## Módulo `providers` (`src/sintetica/providers/`)

🟢 **Propósito:** porta única de geração por LLM (`LLMProvider`), com 2 famílias de adaptadores: o agente do harness (protocolo de arquivos `request`/`submit`) e as APIs externas (OpenAI, Anthropic, Gemini e Ollama local). A escolha segue a política do projeto; uma pilha de decoradores aplica teto de custo, concorrência, mascaramento de PII e novas tentativas.

### Arquivos

| Arquivo | Papel |
|---------|-------|
| `ports.py` | Protocolo `LLMProvider` (`name`, `is_local`, `generate`, `estimate_cost`) |
| `domain.py` | `GenerationRequest`, `GenerationResult`, `CostEstimate`, `ProviderChoice`, `ModelPrice`; constantes `HARNESS`, `OLLAMA`, `EXTERNAL`, `STOP_BUDGET` |
| `errors.py` | Hierarquia de erros (`ProviderError` e filhas) |
| `policy.py` | `load_provider_policy` de `.sintetica/policy.json` |
| `selection.py` | `select_provider`, `probe_availability`, `probe_ollama`, `external_backend_from_env` |
| `factory.py` | `build_provider`: política → seleção → pilha de decoradores |
| `pricing.py` | `PriceTable` (`defaults.json` + `.sintetica/pricing.json`) |
| `models.py` | `resolve_model` por backend (`SINTETICA_<BACKEND>_MODEL` ou padrão) |
| `prompt.py` | `SYSTEM_PROMPT`, `build_user_prompt`, `parse_records` |
| `external/backends.py` | 4 backends (`build`, `parse`), `check_status`, `ollama_host` |
| `external/provider.py` | `ExternalAPIProvider` sobre `httpx.AsyncClient` |
| `harness/store.py` | `RequestStore`: pedido, `submit` validado, leitura da resposta |
| `harness/provider.py` | `HarnessAgentProvider`, `estimate_tokens` |
| `decorators/budget.py` | `BudgetedProvider`: teto de custo com reserva |
| `decorators/concurrency.py` | `ConcurrencyLimitedProvider`: semáforo, 8 por padrão |
| `decorators/masking.py` | `MaskingProvider`: mascara instruções, sementes e textos do JSON Schema |
| `decorators/retrying.py` | `RetryingProvider`: 3 chamadas, esperas de 1 s e 2 s |
| `data/defaults.json` | Modelo padrão por backend e preços por token |

### Funções e métodos principais

| Função | Assinatura | Retorno | Local |
|--------|-----------|---------|-------|
| `build_provider` | `(n_records, *, dataset_dir, project_dir, harness_available=False, authorized_usd=None, per_request_estimate=None, concurrency=8, transport=None, probe_transport=None, sleep=asyncio.sleep)` | `(LLMProvider, ProviderChoice)` | `factory.py:29` |
| `select_provider` | `(priority, n_records, availability)` | `ProviderChoice` ou `ProviderUnavailable` | `selection.py:39` |
| `load_provider_policy` | `(path)` | `ProviderPolicy` | `policy.py:30` |
| `PriceTable.estimate` | `(model, n_records, avg_tokens)` | `Decimal \| None` | `pricing.py:69` |
| `PriceTable.real_cost` | `(model, input_tokens, output_tokens)` | `Decimal \| None` | `pricing.py:76` |
| `ExternalAPIProvider.generate` | `(request)` | `GenerationResult` | `external/provider.py:66` |
| `HarnessAgentProvider.generate` | `(request)` | `GenerationResult` ou `HarnessResponsePending` | `harness/provider.py:36` |
| `RequestStore.save_request` | `(request)` | id de 12 hex | `harness/store.py:64` |
| `RequestStore.submit` | `(rid, raw: bytes)` | número de registros | `harness/store.py:86` |
| `request_id` | `(request)` | 12 primeiros hex do SHA-256 do pedido canônico | `harness/store.py:36` |
| `parse_records` | `(text)` | `tuple[dict, ...]` ou `MalformedResponse` | `prompt.py:33` |

### Algoritmos e regras

1. 🟢 **Seleção por prioridade** (`selection.py:39-63`): percorre `provider_priority` (padrão `harness → ollama → external`). Harness: exige `harness_available` e `n_records ≤ 100`. Ollama: sonda `GET {OLLAMA_HOST}/api/tags` (timeout 2 s), só quando a prioridade chega a ele. External: usa `SINTETICA_EXTERNAL_BACKEND` se tiver chave, senão o 1º backend com chave na ordem fixa `openai → anthropic → gemini`. O motivo da escolha junta os pulados e o escolhido. Nenhum disponível: `ProviderUnavailable` listando as variáveis verificadas.
2. 🟢 **Pilha de decoradores** (`factory.py:52-73`): harness = `Budgeted(Concurrency(Harness))`; externo = `Budgeted(Concurrency(Masking(Retrying(External))))`, com `Masking` só se `pii_premask` (inclusive Ollama, Q30). O teto padrão é `cost_ceiling_usd` da política; `authorized_usd` o substitui.
3. 🟢 **Teto de custo com reserva** (`decorators/budget.py`): antes de cada pedido, reserva a previsão (média do custo real observado, ou `per_request_estimate`, ou 0) sob `asyncio.Lock`; se `gasto + reservado + previsão > autorizado`, devolve resultado vazio com `stop_reason = "teto de custo"` e marca `stopped`. Sem estimativa, o 1º pedido sai sozinho para medir o custo real.
4. 🟢 **Estimativa e custo real** (`pricing.py:69-80`): estimativa = `n × tokens médios × preço de saída` (superestima, lado seguro); custo real = `entrada × preço de entrada + saída × preço de saída`. Preço desconhecido: estimativa exige autorização (`requires_authorization = True`, `price_known = False`) e custo real registrado como 0 com aviso (`external/provider.py:96-114`). Provedor local custa 0.
5. 🟢 **Retry** (`decorators/retrying.py`): só `TransientProviderError` (429, 5xx, timeout, conexão, resposta malformada); 3 chamadas; esperas de 1 s e 2 s; depois `ProviderExhausted`.
6. 🟢 **Classificação HTTP** (`external/backends.py:191-212`): 429 e ≥ 500 temporários; 401/403 (ou 400 com "api key") viram `CredentialError` com o nome da variável, nunca o valor; 404 cita o modelo e a variável `SINTETICA_<BACKEND>_MODEL` (no Ollama, `ollama pull`).
7. 🟢 **Mascaramento do pedido** (`decorators/masking.py`): mascara instruções, cada semente e, no JSON Schema, só as chaves de texto livre (`description`, `examples`, `default`, `enum`). O `PiiGuard` é criado no 1º pedido: política inválida ou falha da allowlist viram `MaskingUnavailable` e nada é enviado.
8. 🟢 **Protocolo do harness** (`harness/store.py`): o id é o hash do pedido canônico (`n_records`, `instructions`, `schema_json`, `seeds`), então pedido igual tem o mesmo id e reaproveita a resposta. O pedido nunca é reescrito. `submit` aceita até 10 MiB em UTF-8, 1 objeto JSON por linha, de 1 a `n_records` linhas; qualquer erro não grava nada (códigos 4 e 5).
9. 🟢 **Prompt comum** (`prompt.py`): sistema pede só `{"records": [...]}`; usuário leva quantidade, instruções, JSON Schema e exemplos (com `sort_keys`). A resposta precisa ser objeto com lista `records` de objetos.
10. 🟢 **Chaves de API** (`external/provider.py:57-64`, `backends.py`): lidas do ambiente a cada chamada; Gemini recebe a chave no cabeçalho `x-goog-api-key`, nunca na URL; exceções do `httpx` são relançadas `from None` para não carregar os cabeçalhos.
11. 🟢 **Anthropic** (`backends.py:95-125`): `max_tokens = 8192`; resposta com `stop_reason = "max_tokens"` conta como malformada (retry).

### Constantes e configuração

| Constante | Valor | Local |
|-----------|-------|-------|
| `MAX_HARNESS_RECORDS` | 100 | `harness/store.py:19` |
| `MAX_SUBMIT_BYTES` | 10 MiB | `harness/store.py:20` |
| `DEFAULT_CONCURRENCY` | 8 | `decorators/concurrency.py:10` |
| `MAX_ATTEMPTS`, `DELAYS_S` | 3, (1 s, 2 s) | `decorators/retrying.py:12-13` |
| `DEFAULT_CEILING` | US$ 5.00 | `policy.py:18` |
| `DEFAULT_PRIORITY` | `harness, ollama, external` | `policy.py:19` |
| `REQUEST_TIMEOUT_S` | 60 s | `external/provider.py:24` |
| `OLLAMA_PROBE_TIMEOUT_S` | 2 s | `selection.py:22` |
| `DEFAULT_OLLAMA_HOST` | `http://localhost:11434` | `external/backends.py:22` |
| `ANTHROPIC_VERSION`, `ANTHROPIC_MAX_TOKENS` | `2023-06-01`, 8192 | `external/backends.py:23-24` |
| `STOP_BUDGET` | `"teto de custo"` | `domain.py:9` |
| Modelos padrão | `gpt-4o-mini`, `claude-haiku-5-5`, `gemini-1.5-flash`, `llama3.2` | `data/defaults.json` |
| Heurística de tokens | 4 caracteres por token | `harness/provider.py:15-17` |

### Tratamento de erros

🟢 Hierarquia: `ProviderError` → `TransientProviderError` → `MalformedResponse`; `ProviderExhausted`, `CredentialError`, `ProviderUnavailable`, `HarnessLimitExceeded`, `HarnessResponsePending`, `MaskingUnavailable`, `ProviderPolicyError`, `RequestStoreError(exit_code)`. Nenhum erro guarda o valor de uma chave.

### Dependências

🟢 `httpx`; módulo `pii` (só no `MaskingProvider` e no `factory`).


## Módulo `schema` (`src/sintetica/schema/`)

🟢 **Propósito:** contrato de dados de cada dataset. O agente grava um rascunho declarativo (`schema.draft.json`); o `build` valida, normaliza nomes, achata para CSV, gera o código Pydantic v2 (`schema.py`) de forma determinística, exporta o JSON Schema e controla a revisão (rodadas e aprovação). Também serializa registros válidos para JSON, JSONL e CSV.

### Arquivos

| Arquivo | Papel |
|---------|-------|
| `spec.py` | Meta-modelo: `SchemaSpecModel`, `FieldSpecModel`, `Constraints`, `SchemaIssue`; `parse_spec`, `dump_spec` |
| `checks.py` | Validação semântica (`check_spec`), `parse_bound`, `pattern_error` |
| `names.py` | `normalize_name`, `normalize_names` (snake_case ASCII, reservados, repetidos) |
| `csvflat.py` | `flatten_for_csv`, `LIST_SEPARATOR = "|"` |
| `codegen.py` | `generate_code`, `py_str` (literal seguro) |
| `version.py` | `schema_version` (SHA-256 do JSON canônico), `canonical_json`, `pretty_json` |
| `loader.py` | `read_spec`, `load_record_model`, `import_record`, `export_json_schema`, `header_version` |
| `state.py` | `SchemaState`, `next_state`, `approved`, `load_state`, `save_state`, `write_atomic` |
| `intent.py` | Leitura tolerante de `intent.json` (`Intent`) e `default_spec` |
| `render.py` | Tabela Markdown do contrato e `diff_specs` |
| `formats.py` | `to_json_obj`, `to_json_text`, `to_jsonl_line`, `to_csv_row`, `csv_columns` |
| `walk.py` | `walk`, `count_fields` |
| `validators.py` | `no_pipe` (usado pelo código gerado) |
| `service.py` | `build`, `show`, `approve` |

### Funções e métodos principais

| Função | Assinatura | Retorno | Local |
|--------|-----------|---------|-------|
| `build` | `(project_dir, slug)` | `CommandResult` (0, 2, 6, 7) | `service.py:133` |
| `approve` | `(project_dir, slug)` | `CommandResult` (0, 2, 7) | `service.py:207` |
| `show` | `(project_dir, slug)` | `CommandResult` | `service.py:193` |
| `check_spec` | `(spec)` | `list[SchemaIssue]` | `checks.py:138` |
| `normalize_names` | `(spec)` | `(spec, avisos)` | `names.py:72` |
| `flatten_for_csv` | `(spec)` | `(spec plano, avisos)` ou `list[SchemaIssue]` | `csvflat.py:52` |
| `generate_code` | `(spec, version)` | código-fonte | `codegen.py:262` |
| `schema_version` | `(spec)` | SHA-256 hex (64) | `version.py:20` |
| `load_record_model` | `(dataset_dir)` | `type[BaseModel]` | `loader.py:83` |
| `to_jsonl_line` | `(record)` | JSON compacto com decimal exato | `formats.py` |
| `to_csv_row` | `(record)` | `dict[str, str]` | `formats.py:120` |

### Algoritmos e regras

1. 🟢 **Pipeline do `build`** (`service.py:90-190`): lê a intenção (`intent.py`); sem rascunho e com estrutura indefinida, usa o contrato padrão de 1 campo `descricao` (`intent.py:51`); valida o meta-modelo; recusa formato diferente do da intenção; aplica `check_spec`; normaliza nomes; em CSV, achata e normaliza de novo; calcula a versão; gera o código num arquivo de preparo `.schema.staged.py`, importa e exporta o JSON Schema; só então grava `schema.json`, `schema.py`, `record.schema.json` e `schema.state.json`. Falha do código gerado grava o traceback em `errors.log` (código 7).
2. 🟢 **Validação semântica** (`checks.py`): limite de 100 campos (sem contar itens de lista); conversa só em JSON ou JSONL; restrições permitidas por tipo (`ALLOWED`); `list` exige `items`, `object` exige `fields`; `enum` exige `choices` não vazias e sem repetidos; `ge`/`le` convertidos ao tipo e sem contradição; `min_length ≤ max_length`; `pattern` precisa compilar no `re` e no validador do Pydantic; `casas_decimais` de 0 a 10.
3. 🟢 **Normalização de nomes** (`names.py`): NFKD → ASCII → minúsculas → `[^a-z0-9]+` vira `_`; vazio vira `campo`; começa com dígito vira `campo_…`; palavras-chave, nomes do `BaseModel`, nomes usados no código gerado e prefixo `model_` ganham `_`; repetidos no mesmo nível ganham `_2`, `_3`. Cada renomeação gera um aviso.
4. 🟢 **CSV plano** (`csvflat.py`): objeto vira colunas com prefixo (`endereco_cidade`); campo de objeto opcional fica opcional; lista de valores simples vira 1 coluna com `|`; lista de objetos ou de listas é recusada; `enum` de lista com `|` é recusado; itens de texto ganham o validador `no_pipe`.
5. 🟢 **Versão** (`version.py`): SHA-256 do JSON canônico (`sort_keys`, separadores compactos, sem valores ausentes). Mesma definição, mesma versão.
6. 🟢 **Geração de código segura** (`codegen.py`): nenhum texto da definição vira código; textos entram por `py_str` (escapa barra, aspas, controle e não imprimíveis); nomes já normalizados; tipos auxiliares (`…Choices`, `…Type`) com nomes únicos; tudo expandido com vírgula final (estável sob `ruff format`); linhas acima de 100 caracteres ganham `# noqa: E501`; cabeçalho com `# schema_version: <sha>`.
7. 🟢 **Carga com regeneração** (`loader.py:83-90`): se a versão do cabeçalho do `schema.py` não bate com a do `schema.json`, regera o arquivo antes de importar; importa com nome de módulo único e sem gerar `__pycache__`.
8. 🟢 **Rodadas de revisão** (`state.py:67-82`): versão nova sobre contrato existente soma 1 rodada; no Expresso, o `build` já aprova; a partir de 5 rodadas sem aprovação, a saída sugere reiniciar a entrevista.
9. 🟢 **Serialização** (`formats.py`): `to_json_text` troca cada `Decimal` por um marcador com nonce aleatório e devolve o número exato (`19.90`), nunca texto; casas decimais vêm das anotações (inclusive de itens de lista); CSV com decimais em casas fixas, listas unidas por `|`, booleanos `true`/`false`, datas ISO.
10. 🟢 **Conversa** (`codegen.py:200-234`): `Record(messages: list[Message] ≥ 1, labels: Labels)`, `Message.role ∈ {system, user, assistant}`, `content` com ao menos 1 caractere.

### Tratamento de erros

🟢 `SchemaIssue(path, message)` por problema (código 6); `GeneratedCodeError` (código 7, com `errors.log`); `SchemaNotFoundError`; `IntentError` local (código 2).

### Observações para as próximas fases

- 🟡 `schema/intent.py` lê a intenção por conta própria, sem usar `sintetica.intent`: não confere `confirmed_at` (lacuna conhecida desde a feature 003).
- 🟡 `write_atomic` existe em 3 cópias: `fsutil.py`, `schema/state.py` e `providers/harness/store.py` (`_write_atomic`).

### Constantes

| Constante | Valor | Local |
|-----------|-------|-------|
| `MAX_FIELDS` | 100 | `checks.py:15` |
| `MAX_DECIMAL_PLACES` | 10 | `checks.py:16` |
| `MAX_ROUNDS` | 5 | `state.py:14` |
| `LIST_SEPARATOR` | `|` | `csvflat.py:8` |
| `MAX_LINE` | 100 | `codegen.py:20` |
| Arquivos | `schema.draft.json`, `schema.json`, `schema.py`, `record.schema.json`, `schema.state.json`, `errors.log` | `service.py`, `loader.py`, `state.py` |

### Dependências

🟢 Pydantic. Usado por `sample`, `batch` e `quality`.


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


## Módulo `batch` (`src/sintetica/batch/`)

🟢 **Propósito:** geração do lote completo (1 a 10.000 registros), skill `sintetica-generate`. Escolhe o provedor pelo volume total, estima e autoriza o custo, pede os registros em blocos, revisa cada bloco, grava por bloco com durabilidade, retoma sem perda, roda em background acima de 100 registros, gera o arquivo final e chama a avaliação de qualidade.

### Arquivos

| Arquivo | Papel |
|---------|-------|
| `state.py` | `RunState` (7 status), caminhos de `output/`, `load_run_state`, `save_run_state`, constantes |
| `plan.py` | `avg_tokens`, `block_size` (adaptativo), `split` |
| `request.py` | `build_instructions`, `build_batch_request` (bloco b de B, rodada r de 4) |
| `review.py` | `DedupIndex` (SHA-256 em memória), `review_block`, `BlockReview` |
| `output.py` | `append_block` (fsync, truncamento), `load_partial` (linha incompleta), `convert_final` |
| `engine.py` | `BatchEngine`: rodadas, fila com N trabalhadores, caminho do harness, `finish`, `usd` |
| `lock.py` | `DatasetLock` (`fcntl.flock`/`msvcrt.locking`), `is_locked` |
| `background.py` | `start_background`, `worker_command`, `popen_options` |
| `worker.py` | Ponto de entrada `python -m sintetica.batch.worker` |
| `service.py` | `generate`, `status`, `run_worker`; pré-condições, custo, lote existente |

### Funções e métodos principais

| Função | Assinatura | Retorno | Local |
|--------|-----------|---------|-------|
| `generate` | `(project, slug, *, resume=False, new=False, authorize_usd=None, block_size_override=None, provider_factory=None, spawner=None, progress=None)` | `CommandResult` (0, 2, 9, 10, 11, 12, 14, 15, 16) | `service.py:509` |
| `status` | `(project, slug)` | `CommandResult` (0, 2, 16) | `service.py:609` |
| `run_worker` | `(project, slug, *, provider_factory=None, progress=None)` | `CommandResult` | `service.py:582` |
| `BatchEngine.run_automatic` | `(state, provider)` | `RunState` final | `engine.py:121` |
| `BatchEngine.run_harness` | `(state, provider, store)` | `RunState` (final ou `aguardando_agente`) | `engine.py:185` |
| `review_block` | `(raw, model, index, masker, limit)` | `BlockReview` | `review.py:56` |
| `block_size` | `(avg, override=None)` | `int` | `plan.py:23` |
| `append_block` | `(path, lines)` | — | `output.py:22` |
| `load_partial` | `(path, index)` | registros gravados | `output.py:44` |
| `convert_final` | `(src, dest, fmt, model)` | caminho do dataset | `output.py:82` |
| `start_background` | `(project, dataset_dir, slug, lock)` | PID | `background.py:36` |

### Algoritmos e regras

1. 🟢 **Pré-condições** (`service.py:112-176`): dataset e intenção (2); contrato aprovado e atual (11); `seeds/sample.meta.json` com a versão do contrato e `sample.jsonl` não vazio (14, cita `sample run`); volume definido na intenção (2).
2. 🟢 **Provedor pelo volume total** (`service.py:210-217`): a fábrica recebe o volume do lote, nunca o tamanho do bloco; acima de 100, o harness nunca é escolhido.
3. 🟢 **Custo e autorização** (`service.py:381-436`): tokens médios da amostra (4 caracteres por token); `estimate_cost(volume, média)`; com `requires_authorization` e sem `--authorize-usd`, termina com 15 sem nenhum pedido, citando o valor arredondado para cima em centavos (ou "preço desconhecido"); autorização abaixo da estimativa gera aviso; o valor autorizado (ou o teto da política) fica em `run.json`.
4. 🟢 **Teto na retomada** (`service.py:439-470`): o provedor recebe `autorizado − custo já gasto`; com saldo 0 e custo > 0, o lote termina como `interrompido_custo` sem chamar o provedor; a estimativa por pedido é `estimativa ÷ número de blocos`.
5. 🟢 **Bloco adaptativo** (`plan.py:23-29`): `min(10, max(1, 4000 // tokens médios))`; `--block-size` de 1 a 100 substitui (Q46).
6. 🟢 **Rodadas** (`engine.py:124-183`): 1ª rodada + até 3 extras, cada uma pedindo só os faltantes; fila de blocos atendida por até 8 trabalhadores; falha do provedor, teto atingido, falha de mascaramento ou de escrita param a fila (`asyncio.Event`); blocos em voo terminam; falha de mascaramento ou escrita é relançada depois do `gather`.
7. 🟢 **Status final** (`engine.py:58-75`): `concluido` com aceitos ≥ ⌈0,95 × volume⌉; `incompleto` abaixo disso; `interrompido_custo` com `stop_reason = "teto de custo"`; `falha_provedor` com `ProviderError`. Em todos, o arquivo final é gerado.
8. 🟢 **Revisão por bloco** (`review.py:56-90`): valida; duplicado pelo SHA-256 da linha bruta (só em memória) e da linha mascarada; mascara e revalida; aceita até o tamanho do bloco; registros além do pedido são ignorados.
9. 🟢 **Gravação durável** (`output.py:22-41`): anexa o bloco, `flush` e `fsync`; erro trunca o arquivo ao tamanho anterior. `run.json` é gravado depois, por `write_atomic`.
10. 🟢 **Retomada** (`output.py:44-69`): o arquivo parcial é a fonte da verdade; uma última linha sem quebra é cortada do arquivo; os aceitos são recontados e o índice de duplicados mascarados é reconstruído. A retomada zera o contador de rodadas.
11. 🟢 **Caminho do harness** (`engine.py:185-238`): 1 pedido com todos os faltantes por rodada, "bloco 1 de 1, rodada r de 4"; `HarnessResponsePending` grava `aguardando_agente`; a resposta lida é revisada e apagada.
12. 🟢 **Background** (`service.py:564-579`, `background.py`): volume > 100 grava `iniciando` e inicia `python -m sintetica.batch.worker` em sessão própria (POSIX `start_new_session`; Windows `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP`), entrada nula, saída em `worker.log`; o comando volta com o PID. O processo grava o próprio PID e muda para `em_andamento`.
13. 🟢 **Trava por dataset** (`lock.py`): `output/run.lock`; em POSIX, o pai abre a trava e o filho herda o descritor (`pass_fds`), e o pai fecha a sua cópia sem destravar; no Windows, o filho tenta pegar a trava por até 10 s. A trava some com o processo, então `status` detecta processo encerrado sem depender do PID.
14. 🟢 **Lote existente** (`service.py:329-378`): trava ocupada ou `iniciando` recente → 16 com o status; `aguardando_agente` → continua; contrato mudado → 16 sugerindo `--new`; `concluido` → 16 sugerindo `--new`; outros status sem `--resume` → 16 sugerindo `--resume` ou `--new`; `--resume` com `--authorize-usd` troca o teto total.
15. 🟢 **Conversão final** (`output.py:82-110`): em fluxo; JSONL copiado; JSON vira lista com 1 registro por linha; CSV com cabeçalho na ordem do contrato, `\r\n` e aspas pela RFC 4180; gravação por arquivo temporário e `os.replace`.
16. 🟢 **Avaliação no fim** (`service.py:505-509`): depois do arquivo final, `evaluate_after_lot` roda dentro da trava; o bloco da avaliação entra na saída; o código do `generate` não muda.
17. 🟢 **Privacidade do log** (`worker.py:46-50`): erro inesperado no background registra só o nome da exceção.

### Tratamento de erros

🟢 `_Fail(code, message)`; `MaskingFailed` (9, cita `--resume`); `BatchWriteError` (10); `RunStateError` (2, sugere `--new`); erro ao iniciar o processo (10).

### Constantes

| Constante | Valor | Local |
|-----------|-------|-------|
| `MAX_ROUNDS` | 4 | `state.py:22` |
| `MAX_BLOCK_OVERRIDE` | 100 | `state.py:23` |
| `CONFORMITY` | 0,95 | `state.py:24` |
| `TOKEN_TARGET`, `MAX_BLOCK` | 4000, 10 | `plan.py:11-12` |
| `BACKGROUND_ABOVE` | 100 | `service.py:70` |
| `STARTING_GRACE_S` | 10 s | `service.py:71` |
| Códigos próprios | 14, 15, 16 | `service.py:66-68` |

### Dependências

🟢 `providers`, `schema`, `intent`, `sample` (sementes, `review` e `CommandResult`), `pii`, `quality` (importação tardia), `fsutil`, `command`.


## Módulo `quality` (`src/sintetica/quality/`)

🟢 **Propósito:** avaliação de qualidade do dataset final (skill `sintetica-eval`). Mede conformidade, unicidade estrutural, unicidade semântica e vazamentos de PII; calcula a duração desde `started_at`; dá o veredito e grava `report.json` e `report.md`. Roda sozinha no fim do lote ou pelo comando `sintetica eval`. 100% local; não altera o dataset.

### Arquivos

| Arquivo | Papel |
|---------|-------|
| `reader.py` | `read_items`: leitura em fluxo de JSONL, lista JSON e CSV; `csv_record`; `Item`; `DatasetReadError` |
| `text.py` | `has_free_text`, `free_text`, `normalize`, `shingles` (3-gramas de palavras) |
| `semantic.py` | `similar` (Jaccard ≥ 0,8 em inteiros), `near_duplicates` (par a par ou filtro de prefixo) |
| `metrics.py` | `collect`, `pct`, `string_leaves`, `duration_min`, `time_target_met`, `verdict` |
| `report.py` | `Report` e submodelos, `write_report`, `render_markdown`, `metric_lines`, `headline`, `load_report` |
| `service.py` | `evaluate`, `evaluate_after_lot`; pré-condições e montagem do relatório |

### Funções e métodos principais

| Função | Assinatura | Retorno | Local |
|--------|-----------|---------|-------|
| `evaluate` | `(project, slug, *, clock=None)` | `CommandResult` (0, 2, 9, 10, 11, 16, 17, 18) | `service.py:244` |
| `evaluate_after_lot` | `(project, slug, *, clock=None)` | linhas da saída ou aviso | `service.py:253` |
| `read_items` | `(path, fmt, model, spec)` | `Iterator[Item]` | `reader.py:106` |
| `collect` | `(items, spec, leaks)` | `Stats` | `metrics.py:66` |
| `near_duplicates` | `(sets, *, force_prefix=False)` | posições quase-duplicadas | `semantic.py:65` |
| `verdict` | `(conformity, structural, semantic, leaks)` | `(veredito, métricas que falharam)` | `metrics.py:117` |
| `write_report` | `(dataset_dir, report)` | `(report.json, report.md)` | `report.py:180` |

### Algoritmos e regras

1. 🟢 **Pré-condições** (`service.py:83-112`, `147-160`): dataset e intenção (2); `schema.json` e `Record` legíveis (11); com a verificação de trava (só no comando avulso), lote em andamento dá 16; `output/dataset.<ext>` ausente dá 18; `PiiGuard` indisponível dá 9; `run.json` ilegível vira aviso.
2. 🟢 **Leitura** (`reader.py`): JSONL por linha, linhas vazias ignoradas, linha que não é JSON fica inválida; lista JSON lida inteira com decimal exato (arquivo que não é lista dá 18); CSV pelo `csv.reader`, com número de células comparado ao cabeçalho (colunas a mais ou a menos ficam inválidas) e conversão pelo contrato plano (vazio → `None`, ou `[]` em lista; lista dividida por `|`). Cada item tem o índice (a partir de 0), o registro válido ou o motivo, e a linha canônica (válido) ou bruta (inválido).
3. 🟢 **Conformidade** (`service.py:197`): `min(válidos, volume) ÷ volume`, com 1 casa (`ROUND_HALF_UP`). O volume vem de `run.json`; sem ele, da intenção; volumes diferentes geram aviso.
4. 🟢 **Unicidade estrutural** (`metrics.py:73-80`): SHA-256 da linha canônica; cópias exatas entram em `problem_indices.duplicates`; `(lidos − duplicados) ÷ lidos`.
5. 🟢 **Texto livre** (`text.py`): campos `text` do contrato, inclusive em listas e objetos, na ordem do contrato; numa conversa, o conteúdo das mensagens mais os campos `text` dos rótulos; `enum`, números e datas ficam fora. Normalização: minúsculas, pontuação Unicode (categoria P) vira espaço, espaços únicos. 3-gramas de palavras; menos de 3 palavras vira 1 trecho (Q47).
6. 🟢 **Quase-duplicados** (`semantic.py`): Jaccard ≥ 0,8 calculado em inteiros (`inter × 5 ≥ união × 4`), com filtro de tamanho. Até 1.000 registros com texto, par a par; acima disso, filtro de prefixo (AllPairs): trechos ordenados pela raridade global, com desempate pelo texto, e prefixo de `n − ⌈0,8·n⌉ + 1` trechos indexado; candidatos verificados pelo Jaccard exato. O resultado é igual ao par a par. Só o registro posterior de cada par conta.
7. 🟢 **Unicidade semântica** (`service.py:199-203`): `(com texto − quase-duplicados) ÷ com texto`; contrato sem texto livre: "não aplicável" (`None`), fora do veredito.
8. 🟢 **PII** (`metrics.py:84-96`): cada texto do registro válido (texto livre e `enum`), com o caminho do campo, passa por `PiiGuard.leaks`; linha inválida passa inteira, no campo `registro`. Cada vazamento guarda índice, campo, tipo e prévia; nunca o valor.
9. 🟢 **Duração** (`metrics.py:99-114`): minutos com 1 casa entre `started_at` e a emissão; sem `started_at` ou com formato inválido, "não medida"; meta de tempo (< 10 min) só para volume ≤ 100, fora do veredito.
10. 🟢 **Veredito** (`metrics.py:117-129`): `APROVADO` só com conformidade ≥ 95%, unicidades ≥ 90% e 0 vazamentos; métricas que falharam em ordem fixa (`conformidade`, `unicidade_estrutural`, `unicidade_semantica`, `pii`).
11. 🟢 **Relatório** (`report.py`): `report.json` com decimais como número exato (`to_json_text`), e `report.md` gerado do mesmo objeto, com métricas, avisos, até 20 índices por tipo e a seção "Escopo e limites da detecção de PII" (`coverage()`). Ambos por `write_atomic`.
12. 🟢 **Avisos** (`service.py:161-176`): status do lote diferente de `concluido`, contrato mudado depois do lote, volume divergente, `run.json` ausente ou ilegível, allowlist ausente.
13. 🟢 **Avaliação no fim do lote** (`service.py:253-259`): mesma avaliação, sem checar a trava (o lote a segura); erro vira 1 linha de aviso com o comando `eval`.

### Constantes

| Constante | Valor | Local |
|-----------|-------|-------|
| `CONFORMITY_TARGET`, `UNIQUENESS_TARGET` | 95, 90 | `metrics.py:19-20` |
| `TIME_TARGET_MIN`, `TIME_TARGET_MAX_VOLUME` | 10 min, 100 | `metrics.py:21-22` |
| `PAIRWISE_LIMIT` | 1.000 | `semantic.py:14` |
| `SHINGLE_WORDS` | 3 | `text.py:15` |
| `MD_INDEX_LIMIT` | 20 | `report.py:17` |
| Códigos próprios | 17 (`REPROVADO`), 18 (dataset ausente ou ilegível) | `service.py:55-56` |

### Dependências

🟢 `schema`, `intent`, `pii`, `batch` (só `state` e `lock`), `sample` (`first_error`, `CommandResult`), `fsutil`.


## Módulo `installer` (`installer/`, pacote npm `sintetica`)

🟢 **Propósito:** `npx sintetica install`. Confere o Node.js, detecta os harnesses, instala as 5 skills nos 2 destinos universais, o wheel do runtime Python e o lançador, e cria `.sintetica/` (política, estado e manifest). Nunca substitui arquivo do usuário sem confirmação; desfaz tudo se falhar; não usa a rede.

### Arquivos

| Arquivo | Papel |
|---------|-------|
| `bin/sintetica.js` | Ponto de entrada: confere a versão do Node antes de importar o resto |
| `src/args.js` | `checkNode`, `parseArgs`, `HELP`, `MIN_NODE` (sintaxe aceita pelo Node 16) |
| `src/detect.js` | `HARNESSES` (marcadores), `detectHarnesses` |
| `src/files.js` | `sha256`, `Journal` (escrita atômica e desfazer), `realFs` injetável |
| `src/runtime.js` | `checkRuntime`, `pythonOk`, `uvInstallHint`, `launcherSh`, `launcherCmd`, `findWheel`, `wheelName` |
| `src/plan.js` | `SKILLS`, `SKILL_ROOTS`, `desiredFiles`, `decide` (6 ações) |
| `src/prompt.js` | `makeAsker` (`readline`, `--yes`, sem terminal), `outOfProject` |
| `src/install.js` | `install`: orquestração, `state.json`, manifest, resumo |
| `skills/sintetica-*/SKILL.md` | As 5 skills, chamando `.sintetica/bin/sintetica` |
| `templates/policy.json` | Política padrão |
| `runtime/` | Wheel gerado por `npm run build:runtime` (`prepack`) |

### Funções principais

| Função | Assinatura | Retorno | Local |
|--------|-----------|---------|-------|
| `install` | `(opts: {dir, yes?, out, ask?, interactive?, fs?, spawn?, env?, nodeVersion?, home?, platform?, packageDir?, now?})` | código 0 ou 1 | `src/install.js:104` |
| `checkNode` | `(version)` | mensagem ou `null` | `src/args.js:18` |
| `parseArgs` | `(argv, cwd)` | `{command, yes, dir}` ou `{error}` | `src/args.js:43` |
| `detectHarnesses` | `(root, previous=[])` | harnesses na ordem fixa | `src/detect.js:38` |
| `desiredFiles` | `(packageDir, version)` | `{files, wheel}` | `src/plan.js:31` |
| `decide` | `(file, root, manifest)` | ação | `src/plan.js:80` |
| `checkRuntime` | `({spawn?, env?})` | `{uv, python, ready}` | `src/runtime.js:52` |
| `Journal.write` / `rename` / `rollback` | — | — | `src/files.js:73-110` |

### Algoritmos e regras

1. 🟢 **Versão do Node** (`bin/sintetica.js`, `args.js:18-34`): compara major.minor.patch com 18.0.0 antes de importar módulos modernos; abaixo, `✗` com a versão encontrada e a mínima, código 1.
2. 🟢 **Fora de projeto** (`prompt.js:39-43`, `install.js:123-128`): pasta pessoal ou raiz do sistema exigem confirmação (`--yes` confirma); recusa termina com 1 sem criar nada.
3. 🟢 **Detecção** (`detect.js`): Claude Code `.claude`; Antigravity `.agents` ou `.agent`; Cursor `.cursor`; Gemini CLI `.gemini`; Codex `.codex` ou `AGENTS.md`. `.claude` e `.agents` com só as skills do sintetica não contam, salvo se o `state.json` anterior já listava o harness. A detecção só informa o resumo e o `state.json` (Q51).
4. 🟢 **Plano de arquivos** (`plan.js`): 10 skills (5 × 2 destinos), lançador `sh` (modo 755) e `.cmd`, wheel (se empacotado) e política. Ação por arquivo: `criar` (ausente), `igual` (mesmo SHA-256), `substituir` (no manifest com o mesmo hash), `perguntar` (fora do manifest ou editado), `preservar` (`policy.json` válido), `recuperar` (`policy.json` inválido).
5. 🟢 **Confirmações** (`prompt.js:13-31`, `install.js:180-212`): 1 pergunta por skill (as 2 cópias juntas) e 1 por arquivo fora das skills; `--yes` responde sim; sem terminal interativo, não, com aviso sugerindo `--yes`; resposta não pula as 2 cópias.
6. 🟢 **Escrita com desfazer** (`files.js`): pastas criadas registradas; arquivo temporário no mesmo diretório, `chmod` e `rename`; o diário guarda criado, substituído (conteúdo anterior), renomeado (`.bak`) e pasta; `rollback` desfaz em ordem inversa e ignora erros pontuais. Qualquer erro na aplicação: desfaz e termina com 1, citando caminho e código (`ENOSPC`, `EACCES`).
7. 🟢 **Política** (`install.js:150-155`): `recuperar` renomeia para `policy.json.bak` e grava a padrão, com aviso; `--yes` nunca substitui a política existente.
8. 🟢 **Runtime** (`runtime.js:52-73`): `uv --version` por `spawnSync` sem shell; Python ≥ 3.10 por `uv python find ">=3.10"` (com `uv`) ou `python3`/`python --version`; sem eles, aviso com o comando de instalação do `uv` (só exibido) e `runtime_ready: false`.
9. 🟢 **Lançador** (`runtime.js:107-145`): define `SINTETICA_CMD` com o próprio caminho e roda `uvx --from <wheel> sintetica`; sem o wheel, `uv run sintetica`. O `.cmd` é ASCII com `\r\n`.
10. 🟢 **Idempotência** (`install.js:230-266`): `state.json` e manifest só são gravados se o conteúdo mudar; manifest ordenado, sem a si mesmo, com `installed_at` sem milissegundos.

### Tratamento de erros

🟢 Código 1 para Node antigo, comando inválido, pasta inexistente, cancelamento e falha de escrita; `install-manifest.json` ilegível vira aviso (arquivos existentes tratados como do usuário).

### Constantes

| Constante | Valor | Local |
|-----------|-------|-------|
| `MIN_NODE` | 18.0.0 | `args.js:4` |
| `MIN_PYTHON` | 3.10 | `runtime.js:5` |
| `LAUNCHER`, `LAUNCHER_CMD`, `RUNTIME_DIR` | `.sintetica/bin/sintetica`, `.cmd`, `.sintetica/runtime` | `runtime.js:6-8` |
| `SKILLS` | `sintetica-start`, `-schema`, `-sample`, `-generate`, `-eval` | `plan.js:7` |
| `SKILL_ROOTS` | `.agents/skills`, `.claude/skills` | `plan.js:14` |

### Integração com o runtime Python

🟢 `sintetica.command.cli_command()` (`src/sintetica/command.py`) lê `SINTETICA_CMD`; as mensagens do runtime citam o lançador quando ele é usado, e `uv run sintetica` sem ele.
