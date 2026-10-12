# Dúvidas do pipeline /reversa-new, sintetica

> `answer_mode: file`. Responda abaixo de cada pergunta, na linha `**Resposta:**`.
> Revisor: Antigravity. Executor: Claude Code.
> A coluna "Sugestão" é uma inferência do Claude a partir do brief. Ela não é decisão.
> Para aceitar a sugestão, escreva `OK`. Para "não sei", escreva `NÃO SEI` (vira 🟡 [INDEFINIDO]).

---

## Etapa 1, reversa-ideator (status: CONSUMIDO em ideation.md)

### Q1. Problema raiz
Qual problema o sintetica resolve? Quem sente esse problema hoje, e em que momento?

**Sugestão:** Times que treinam ou avaliam modelos de IA precisam de datasets. Dados reais são escassos, caros ou têm PII. Gerar dados sintéticos hoje exige scripts ad hoc e parâmetros de baixo nível. O problema aparece no início de um projeto de fine-tuning, avaliação ou teste.

**Resposta:** OK. Foco principal em resolver a carência de dados sintéticos estruturados e rotulados para fine-tuning de LLMs, testes funcionais de software e geração de dados tabulares/conversacionais para validação de sistemas.

### Q2. Valor entregue
O que o usuário consegue fazer depois do sintetica que não conseguia antes? Em uma frase.

**Sugestão:** Descrever em linguagem natural o dataset desejado e receber, dentro do próprio harness de IA, um dataset validado por schema Pydantic, sem PII e com relatório de qualidade.

**Resposta:** OK. Descrever o dataset desejado em linguagem natural durante uma entrevista guiada e receber, dentro do próprio harness de IA, o lote sintético gerado e validado por schemas Pydantic, com conformidade de tipos e métricas de qualidade.

### Q3. Alternativas existentes
Quais soluções já existem? Por que elas não bastam?

**Sugestão:** Faker, SDV, Gretel, distilabel, scripts manuais com LLM. Elas exigem código ou parâmetros técnicos. Nenhuma roda como skill nativa de harness (Claude Code, Antigravity, Cursor, Gemini CLI, Codex) com entrevista guiada.

**Resposta:** OK. As ferramentas existentes exigem programação manual de scripts ou configuração complexa de hiperparâmetros. O `sintetica` atua como skill conversacional nativa de harnesses, traduzindo intenção humana em dados sintéticos com validação contínua e tolerância a incertezas.

### Q4. Público-alvo bruto
Quem é o usuário principal? Uma frase.

**Sugestão:** Desenvolvedor ou pesquisador que já usa um harness de IA e precisa de dados para treinar, testar ou avaliar modelos, sem querer escrever pipeline de geração.

**Resposta:** OK. Desenvolvedores de software, engenheiros de Machine Learning e analistas de dados que utilizam assistentes de IA (Claude Code, Antigravity, Cursor, Gemini CLI) e precisam produzir dados sintéticos sob demanda sem programar geradores manuais.

### Q5. Métrica de sucesso
Daqui a 3 meses, como saber se deu certo? Uma métrica concreta com unidade.

**Sugestão:** [sem inferência possível a partir do brief]. Exemplos: "N instalações via npx por mês", "% de datasets aprovados no sintetica-eval na primeira geração", "tempo da ideia ao dataset em minutos".

**Resposta:** Tempo médio da ideia inicial ao dataset validado em menos de 10 minutos para lotes de teste, com taxa mínima de 95% de conformidade com schemas Pydantic e zero vazamento de dados sensíveis (PII).

### Q6. Premissas perigosas
Qual suposição, se estiver errada, mata o projeto? Máximo 3.

**Sugestão:**
1. A geração via LLM do próprio harness tem diversidade e qualidade suficientes para uso real.
2. É viável detectar PII de forma confiável sem serviço externo.
3. Os harnesses alvo aceitam o mesmo formato de skill sem adaptação por engine.

**Resposta:** OK para as 3 premissas sugeridas. Mitigações adotadas:
1. Geração iterativa com amostragem inicial (3 a 5 registros) e verificação semântica no `sintetica-eval`.
2. Sanitização local com regras heurísticas leves e bibliotecas locais (ex.: Faker para mascaramento/substituição).
3. Distribuição padronizada via especificação universal de Agent Skills (`.agents/skills/` e `.claude/skills/`).

### Q7. Referências de padrão (técnica)
O `mira-animator` não foi encontrado localmente. Existe `/Volumes/SSD-EXTERNO/itsfine-lab`. Esse diretório é a referência do `@sandeco/itsfine`? Onde está o `mira-animator`?

**Sugestão:** Informar o caminho local ou o repositório. Sem acesso, o Claude segue apenas o padrão do `reversa` instalado em `.reversa/` e `.claude/skills/`, e marca o resto como 🟡.

**Resposta:** Sim, `/Volumes/SSD-EXTERNO/itsfine-lab` é a referência local do `@sandeco/itsfine`. O `mira-animator` é distribuído via pacote npm (`npm view mira-animator`), cuja principal referência adotada é o "Princípio da Criação Imediata de Diretório" (criar a pasta do dataset e exibir o caminho absoluto no início da entrevista). O `reversa` atual é a referência mestre de orquestração multiagente.

---

## Pendências abertas pelo ideation.md (status: RESPONDIDO, será consumido no prd.md)

### Q8. Fonte do LLM no motor de geração
O `sintetica-generate` roda em Python com `asyncio`. Quem gera os registros?

**Sugestão:** Arquitetura com porta `LLMProvider` (Clean Architecture). Adaptador padrão: API externa chamada pelo runtime Python (ex.: Anthropic, OpenAI, Gemini), com chave em variável de ambiente. Adaptador secundário: o próprio harness gera os lotes pequenos (amostra) sem chave de API.

**Resposta:** OK com a sugestão. Interface abstrata `LLMProvider` seguindo Clean Architecture. Dois adaptadores implementados:
1. `ExternalAPIProvider` (OpenAI, Anthropic, Gemini, Ollama local) para geração assíncrona em lote e alta vazão pelo runtime Python.
2. `HarnessAgentProvider` (o próprio assistente do harness atuando no chat) para amostras e prototipagem rápida sem chave de API.

### Q9. Critério de "zero vazamento de PII"
A detecção local é heurística. Qual é o critério mensurável da métrica?

**Sugestão:** "0 ocorrências detectadas pelo conjunto de detectores do `sintetica-eval` (regex de CPF, CNPJ, e-mail, telefone, cartão, IP, mais lista configurável) no dataset final". Documentar o limite: a métrica cobre o que os detectores cobrem.

**Resposta:** OK com a sugestão. Definido como zero ocorrências detectadas pelo conjunto de detectores determinísticos do `sintetica-eval` (regex para CPF, CNPJ, e-mail, telefone, cartão de crédito, IPv4/IPv6 e lista de substituição Faker). O relatório final documentará formalmente o escopo e os limites dessa cobertura.

### Q10. Volume de "lote de teste"
A métrica de < 10 minutos vale para quantos registros?

**Sugestão:** até 100 registros.

**Resposta:** OK. Lote de teste fixado em até 100 registros para a métrica de < 10 minutos. Lotes de produção (1.000 a 10.000 registros) serão gerados via motor assíncrono em background.

---

## Etapa 2, reversa-researcher (status: CONSUMIDO em personas.md)

### Q11. Número de personas
Público-alvo do `ideation.md`: desenvolvedores de software, engenheiros de ML e analistas de dados que usam assistentes de IA.
Quantas personas detalhar? (1 = foco de MVP, 2, ou 3 = cobertura ampla)

**Sugestão:** 3 personas, uma por perfil citado:
1. `dev-de-testes`: desenvolvedor que precisa de massa de dados para testes funcionais.
2. `engenheiro-de-ml`: engenheiro que precisa de dataset conversacional rotulado para fine-tuning de LLM.
3. `analista-de-dados`: analista que precisa de dados tabulares para validar sistemas e dashboards.

**Resposta:** OK. Adotar 3 personas: `dev-de-testes`, `engenheiro-de-ml` e `analista-de-dados`.

### Q12. Contexto, nível técnico e objetivo final de cada persona
Responda por persona confirmada na Q11.

**Sugestão:**
- **dev-de-testes:** Contexto: escreve testes de integração no IDE com um assistente de IA e não tem dados realistas sem PII. Nível: avançado em programação, intermediário em dados. Objetivo final: entregar software confiável sem expor dados de produção.
- **engenheiro-de-ml:** Contexto: prepara um fine-tuning e tem poucos exemplos rotulados. Nível: avançado em ML e Python. Objetivo final: melhorar o modelo com dados diversos e de qualidade comprovada.
- **analista-de-dados:** Contexto: valida um pipeline ou dashboard antes de receber dados reais. Nível: intermediário em Python, avançado em SQL e planilhas. Objetivo final: validar o sistema cedo, sem depender de acesso a dados sensíveis.

**Resposta:** OK. Aprovo integralmente o contexto, nível técnico e objetivo final propostos para as 3 personas.

### Q13. Jornada principal (base comum)
O Claude vai adaptar esta jornada para cada persona. Ela faz sentido? Falta ou sobra algum passo?

**Sugestão:**
1. Instalar o sintetica com `npx sintetica install`.
2. Iniciar a entrevista com `/sintetica-start` e ver o caminho absoluto da pasta do dataset.
3. Descrever objetivo, formato e volume em linguagem natural.
4. Revisar o schema Pydantic proposto.
5. Aprovar a amostra de 3 a 5 registros.
6. Gerar o lote completo.
7. Ler o relatório de qualidade e PII e usar o dataset.

**Resposta:** OK. Jornada de 7 passos aprovada sem alterações. O fluxo atende perfeitamente ao princípio da pasta imediata e da validação antes da geração em escala.

---

## Etapa 3, reversa-drafter (status: RESPONDIDO PELO REVISOR)

> O drafter faz no máximo 2 perguntas de cobertura. Stack e dependências externas já estão definidas no brief e na Q8.

### Q14. Não-objetivos (fora do escopo do MVP)
O que fica explicitamente FORA do MVP?

**Sugestão:**
1. Interface gráfica web ou desktop. O sintetica roda só dentro de harnesses e da CLI.
2. Geração de imagem, áudio ou vídeo. O MVP cobre só dados tabulares (CSV) e textuais/conversacionais (JSON, JSONL).
3. Treinamento ou fine-tuning de modelos. O sintetica entrega o dataset e para aí.
4. Síntese a partir de dados reais do usuário (ex.: estilo SDV). O MVP gera a partir da intenção descrita.
5. Serviço hospedado ou SaaS. Tudo roda localmente.
6. Garantia de anonimização formal (ex.: privacidade diferencial).

**Resposta:** OK. Aprovo integralmente todos os 6 não-objetivos propostos. O escopo do MVP permanece focado em dados tabulares e conversacionais gerados a partir de intenção e validados por Pydantic dentro dos harnesses de IA.

### Q15. Compliance e prazo
Existe exigência regulatória (ex.: LGPD) ou prazo que limite o escopo?

**Sugestão:**
- Compliance: alinhamento com LGPD por design. Nenhum dado real do usuário é enviado a serviço externo pelo sintetica. A política de privacidade fica em `.sintetica/`. Sem certificação formal no MVP.
- Prazo e orçamento: [INDEFINIDO]. Sem prazo informado.

**Resposta:** OK. Princípio de privacidade por design alinhado à LGPD: operação local, sem telemetria não autorizada, com política de privacidade e governança em `.sintetica/policy.json`. Sem restrição de prazo rígido para o MVP.

---

## Etapa 4, reversa-spec-sdd (status: RESPONDIDO PELO REVISOR)

### Q16. Métrica de diversidade
- **Definição:** Taxa de unicidade semântica e estrutural ≥ 90% avaliada pelo `sintetica-eval`.

### Q17. Teto de orçamento
- **Definição:** Estimativa prévia de custo em lote com pedido explícito de autorização se o custo ultrapassar $5.00 USD.

### Q18. Versões mínimas de runtime
- **Definição:** Node.js >= 18.0.0 (instalador CLI) e Python >= 3.10 (runtime `uv`).

### Q19. Cobertura de testes
- **Definição:** Mínimo de 80% de cobertura de código com `pytest` e `pytest-cov`.

### Q20. Janela de medição de tempo
- **Definição:** Medição iniciada no disparo de `/sintetica-start` até a emissão do relatório final em `sintetica-eval`.

### Q21. Mitigação para dados reais na entrevista
- **Definição:** Filtro de mascaramento preventivo de PII antes de qualquer trânsito para `ExternalAPIProvider`, priorizando `HarnessAgentProvider` ou Ollama local.

---

## Etapa 5, reversa-spec-sdd, Fase 0: decomposição (status: RESPONDIDO PELO REVISOR)

> Q16 a Q21 serão consumidas nas specs. Cada componente abaixo vira uma spec em `_reversa_sdd/sdd/<componente>.md`.

### Q22. Decomposição em componentes
O Claude propõe 8 componentes a partir do `prd.md`. Concorda? Quer adicionar, remover, renomear ou fundir algum?

**Sugestão:**
1. `cli-installer`: `npx sintetica install` (Node.js ≥ 18). Detecta harnesses, injeta skills em `.agents/skills/` e `.claude/skills/` e cria `.sintetica/` com `state.json`, `install-manifest.json` e `policy.json`.
2. `intent-interview`: skill `sintetica-start`. Cria `datasets/<slug>/seeds/` antes da 1ª pergunta, conduz os modos Guiado e Expresso, aplica `🟡 [INDEFINIDO]` e inicia a medição de tempo (Q20).
3. `schema-builder`: skill `sintetica-schema`. Traduz a intenção em modelos Pydantic v2 e pede revisão do schema.
4. `sample-preview`: skill `sintetica-sample`. Gera 3 a 5 registros para aprovação, por padrão via `HarnessAgentProvider`.
5. `llm-provider`: porta `LLMProvider` com `ExternalAPIProvider` (OpenAI, Anthropic, Gemini, Ollama) e `HarnessAgentProvider`. Inclui estimativa de custo e autorização acima de US$ 5,00 (Q17).
6. `pii-guard`: detectores determinísticos de PII (CPF, CNPJ, e-mail, telefone, cartão, IPv4/IPv6) e mascaramento com Faker. Usado antes de enviar dados ao `ExternalAPIProvider` (Q21) e no `sintetica-eval`.
7. `batch-generator`: skill `sintetica-generate`. Geração concorrente com `asyncio`, validação Pydantic por registro, nova tentativa, lotes de teste (≤ 100) e de produção (1.000 a 10.000) em background, saída CSV, JSON e JSONL.
8. `quality-evaluator`: skill `sintetica-eval`. Mede conformidade ≥ 95%, unicidade ≥ 90% (Q16) e 0 PII detectada, emite o relatório e fecha a medição de tempo.

Requisitos transversais (Python ≥ 3.10, `uv`, `mypy` estrito, `ruff`, cobertura ≥ 80% com `pytest-cov`, Q18 e Q19) entram como RNF em cada spec, sem spec própria.

**Resposta:** OK. Aprovo integralmente a decomposição nos 8 componentes propostos. A arquitetura está modular, adere à Clean Architecture e atende a todos os requisitos funcionais e não-funcionais. Prossiga com a geração das 8 specs SDD em `_reversa_sdd/sdd/` e a validação do `spec_scorer.py`.

---

## Etapa 6, Transição para /reversa-forward (status: RESPONDIDO PELO REVISOR)

### Q26. PII gerada deliberadamente (pii-guard OQ-01)
- **Decisão:** Aprovado. O hash dos valores gerados pelo Faker/gerador sintético entra em uma allowlist de dados gerados. Isso evita falsos positivos na verificação de vazamento do `sintetica-eval`.

### Q27. Métrica de unicidade semântica (quality-evaluator OQ-01)
- **Decisão:** Aprovado. O limiar de Jaccard de 0,8 sobre 3-gramas é o ponto de corte par a par para detectar quase-duplicados (pares com Jaccard ≥ 0,8 são considerados repetidos). A meta global do dataset permanece unicidade ≥ 90% (menos de 10% de registros quase-duplicados).

### Q28. Faixa intermediária de volume (101 a 999 registros)
- **Decisão:** Lotes acima de 100 registros seguem o pipeline assíncrono em background via `batch-generator`.

---

## Etapa 6, /reversa-clarify da feature 001-pii-guard (status: RESPONDIDO PELO REVISOR)

> Fonte: `_reversa_forward/001-pii-guard/requirements.md`. Responda com a letra da opção ou com texto livre na linha `**Resposta:**`.

### Q23. Critério de vazamento para PII pedida de propósito (RN-05, RF-08)
O usuário pode pedir um campo de CPF no dataset. O `pii-guard` troca o CPF gerado pelo LLM por um CPF falso. Como o avaliador evita contar esse CPF falso como vazamento?

a) Registro de impressões (hash) de cada valor falso inserido pelo mascaramento. Só conta como vazamento o achado fora do registro. **(Sugestão do Claude)**
b) Campos declarados como PII no schema ficam fora da verificação.
c) Todo achado conta como vazamento. O usuário não pode pedir campos de PII.
d) Resposta livre.

**Resposta:** a) Registro de impressões (hash) de cada valor falso inserido pelo mascaramento. Só conta como vazamento o achado fora do registro.

### Q24. Conjunto de referência para a precisão (RNF: 100% de detecção, ≤ 5% de falsos positivos)
Quem monta o conjunto de referência e com quantos casos por tipo?

a) O Claude gera durante o `/reversa-coding`, com 20 casos positivos e 20 negativos por tipo (7 tipos, 280 casos), versionados em `tests/fixtures/`. O Antigravity revisa. **(Sugestão do Claude)**
b) Mesmo formato da opção a, com 50 + 50 casos por tipo.
c) O usuário fornece o conjunto.
d) Resposta livre.

**Resposta:** a) O Claude gera durante o `/reversa-coding`, com 20 casos positivos e 20 negativos por tipo (7 tipos, 280 casos), versionados em `tests/fixtures/`. O Antigravity revisa.

### Q25. Rigor na detecção de telefone (RF-03)
Sequências de 10 ou 11 dígitos sem formatação aparecem em IDs e pedidos. Isso pode estourar o limite de 5% de falsos positivos.

a) Detectar telefone só com formatação (parênteses no DDD, hífen ou espaço) ou com prefixo `+55`. Dígitos corridos não contam. **(Sugestão do Claude)**
b) Detectar também dígitos corridos, desde que o DDD seja válido (11 a 99, lista da Anatel) e o 1º dígito do celular seja 9.
c) Detectar qualquer sequência de 10 ou 11 dígitos.
d) Resposta livre.

**Resposta:** a) Detectar telefone só com formatação (parênteses no DDD, hífen ou espaço) ou com prefixo `+55`. Dígitos corridos não contam para evitar falsos positivos com identificadores numéricos e chaves primárias.

---

## Etapa 7, /reversa-clarify da feature 002-llm-provider (status: CONSUMIDO em requirements.md e roadmap.md)

> Fonte: `_reversa_forward/002-llm-provider/requirements.md`. Responda com a letra da opção ou com texto livre na linha `**Resposta:**`.

### Q29. Contrato do provedor do harness (RN-02, RF-04)
O runtime Python não consegue chamar o agente do harness. O agente é quem orquestra a skill. Como os registros do harness chegam ao Python?

a) Protocolo em 2 passos por arquivo. `uv run sintetica request <slug>` grava `datasets/<slug>/requests/<id>.json` com instruções, schema e sementes, e mostra o pedido ao agente. O agente gera os registros e executa `uv run sintetica submit <slug> <id>`, enviando o JSONL pela entrada padrão. O `HarnessAgentProvider` lê a resposta, valida o formato e devolve o resultado comum da porta. Limite de 100 registros por pedido. **(Sugestão do Claude)**
b) Apenas entrada padrão. O agente gera os registros sem pedido gravado e envia direto para `uv run sintetica validate`. O provedor do harness só lê a entrada padrão.
c) Tirar o harness da porta Python. A geração pelo harness fica só na skill `sintetica-sample`, e a porta cobre só os provedores externos.
d) Resposta livre.

**Resposta:** a) Protocolo em 2 passos por arquivo (`request` e `submit` via CLI/stdin com limite de 100 registros). Essa abordagem cria uma fronteira desacoplada, rastreável e auditável entre o agente de chat e o runtime Python.

### Q30. Mascaramento no Ollama (RN-04)
O Ollama roda na máquina do usuário, mas `OLLAMA_HOST` pode apontar para outro servidor.

a) Mascarar sempre, como nos outros backends. A regra fica uniforme e falha para o lado seguro. **(Sugestão do Claude)**
b) Não mascarar no Ollama.
c) Mascarar só quando `OLLAMA_HOST` não for `localhost`, `127.0.0.1` ou `::1`.
d) Resposta livre.

**Resposta:** a) Mascarar sempre por padrão (falha segura). Garante conformidade uniforme e proteção de dados independentemente da topologia de rede do Ollama.

### Q31. Modelos padrão e manutenção de `pricing.json` (RF-02, RF-06)
Nomes e preços de modelos mudam com frequência. Um padrão embutido fica desatualizado.

a) Sem modelo padrão embutido. O usuário define `SINTETICA_OPENAI_MODEL`, `SINTETICA_ANTHROPIC_MODEL`, `SINTETICA_GEMINI_MODEL` ou `SINTETICA_OLLAMA_MODEL`. O usuário mantém `.sintetica/pricing.json`. Modelo sem preço segue a regra atual e exige autorização. **(Sugestão do Claude)**
b) Modelos padrão e preços embutidos no pacote, atualizados a cada versão do sintetica. O usuário pode sobrescrever por variável de ambiente.
c) Resposta livre, com os modelos padrão desejados.

**Resposta:** b) Fornecer modelos padrão econômicos e tabela de preços embutida no pacote como defaults (`gpt-4o-mini`, `claude-3-5-haiku-latest`, `gemini-1.5-flash`, `llama3.2`). Permitir override total pelo usuário via variáveis de ambiente (`SINTETICA_*_MODEL`) e arquivo `.sintetica/pricing.json`.

---

## Etapa 8, /reversa-plan da feature 002-llm-provider (status: CONSUMIDO em actions.md; Q32 parcial, ver Q34)

> Fonte: `_reversa_forward/002-llm-provider/roadmap.md`. Nenhuma das 2 perguntas bloqueia o `/reversa-to-do`. A Q32 bloqueia o fechamento da feature.

### Q32. Identificadores de modelo vigentes (RN-08, D-17)
A Q31 indicou `gpt-4o-mini`, `claude-3-5-haiku-latest`, `gemini-1.5-flash` e `llama3.2`. Em outubro de 2026, ao menos `claude-3-5-haiku-latest` está descontinuado. Modelo descontinuado gera erro 404 no primeiro uso real. Os valores ficam só em `src/sintetica/providers/data/defaults.json`.

a) Anthropic: `claude-haiku-5-5` (Haiku vigente). OpenAI, Gemini e Ollama: o revisor confirma os identificadores e os preços vigentes antes do coding. **(Sugestão do Claude)**
b) Manter os 4 valores da Q31 e corrigir depois.
c) Resposta livre, com os 4 identificadores e os preços de entrada e saída por token.

**Resposta:** a) Aprovado com identificadores canônicos e preços de referência em `defaults.json`:
- OpenAI: `gpt-4o-mini` ($0.15/1M input, $0.60/1M output)
- Anthropic: `claude-3-5-haiku-20241022` ou `claude-haiku-4-5` ($0.80/1M input, $4.00/1M output)
- Gemini: `gemini-1.5-flash` ($0.075/1M input, $0.30/1M output)
- Ollama: `llama3.2` (custo $0.00 local)

### Q33. Confirmação de 3 interpretações do plano
O plano interpretou 3 pontos do `requirements.md`. Confirme ou corrija cada um.

1. **D-13, harness sem bloqueio:** sem resposta enviada, `generate` grava o pedido e levanta `HarnessResponsePending` com o comando `submit`. O chamador mostra o comando ao agente.
2. **D-16, estimativa pelo preço de saída:** a estimativa usa `registros × tokens médios × preço de saída por token`. Ela tende a superestimar (lado seguro do teto). O custo real usa preço de entrada e de saída.
3. **D-19, retry com 3 chamadas:** 3 tentativas no total, com esperas de 1 s e 2 s. A espera de 4 s da RF-09 não ocorre, conforme os cenários Gherkin.

a) Confirmo os 3. **(Sugestão do Claude)**
b) Resposta livre, item por item.

**Resposta:** a) Confirmo integralmente as 3 interpretações. A abordagem do harness evita timeouts e bloqueios no runtime, a estimativa pelo lado superior garante segurança contra surpresas de faturamento, e a política de retry de 3 chamadas mantém a latência controlada.

---

## Etapa 9, /reversa-to-do da feature 002-llm-provider (status: CONSUMIDO em defaults.json)

> Fonte: `_reversa_forward/002-llm-provider/actions.md`. Bloqueia só a ação T002 (entrada `anthropic` de `defaults.json`).

### Q34. Modelo padrão da Anthropic (complemento da Q32)
A resposta da Q32 escolheu a opção a), que indicava `claude-haiku-5-5`. O texto da resposta, porém, cita `claude-3-5-haiku-20241022` **ou** `claude-haiku-4-5`, com preço de US$ 0,80 / US$ 4,00 por milhão. Um único valor é necessário. `claude-3-5-haiku-20241022` está descontinuado e geraria erro 404.

a) `claude-haiku-5-5`, conforme a opção a) da Q32. O revisor informa o preço de entrada e de saída por milhão de tokens. **(Sugestão do Claude)**
b) `claude-haiku-4-5`, com o preço de entrada e de saída por milhão de tokens.
c) Resposta livre.

> Observação: o Claude também não confirmou que `gemini-1.5-flash` e `gpt-4o-mini` continuam disponíveis em outubro de 2026. Se o revisor tiver dúvida, informe os identificadores vigentes na mesma resposta. Sem resposta, T002 usa os valores da Q32.

**Resposta:** a) Definir `claude-haiku-5-5` com preço de US$ 0,80 de entrada e US$ 4,00 de saída por 1M de tokens. Confirmados também os defaults de `gpt-4o-mini` ($0.15/$0.60) e `gemini-1.5-flash` ($0.075/$0.30) para o arquivo `defaults.json`.

---

## Etapa 9, /reversa-clarify da feature 003-schema-builder (status: RESPONDIDO PELO REVISOR)

> Fonte: `_reversa_forward/003-schema-builder/requirements.md`. Responda com a letra da opção ou com texto livre na linha `**Resposta:**`.

### Q35. Listas em formato CSV (RN-04, RF-07)
Objetos aninhados viram colunas com prefixo (`endereco_cidade`). Uma lista não tem achatamento por prefixo. O que fazer com um campo lista quando o formato é CSV?

a) Lista de valores simples (texto, número, data, enum) vira 1 coluna de texto com os itens separados por `|`, e o sistema avisa o usuário. Lista de objetos é recusada com erro, e o sistema sugere JSON ou JSONL. **(Sugestão do Claude)**
b) Recusar toda lista em CSV com erro, sugerindo JSON ou JSONL.
c) Expandir em colunas numeradas (`telefones_1`, `telefones_2`, ...) até um tamanho máximo fixo definido no schema.
d) Resposta livre.

**Resposta:** a) Lista de valores primitivos/simples vira coluna única serializada com delimitador `|`. Listas de objetos aninhados são recusadas com mensagem orientando uso de formato JSON ou JSONL.

### Q36. Verificação estrita de tipos do `schema.py` gerado (RN-08, RF-12)
A spec pede `mypy --strict` no `schema.py` antes de mostrar ao usuário. O `mypy` é dependência só de desenvolvimento e não existe no runtime do usuário.

a) A verificação estrita fica na suíte de testes do gerador: cada tipo, restrição e caso de borda gera um `schema.py` que passa em `mypy --strict` e `ruff` no CI. No runtime, o sistema valida importando o arquivo, conferindo a classe `Record` e exportando o JSON Schema. **(Sugestão do Claude)**
b) Tornar `mypy` dependência de runtime e rodar `mypy --strict` a cada geração (custo: dependência pesada e ~2 s a mais por geração).
c) Rodar `mypy` no runtime só se ele estiver instalado; sem ele, a validação é apenas por importação.
d) Resposta livre.

**Resposta:** a) A verificação com `mypy --strict` e `ruff` é garantida na suíte de testes do gerador. Em tempo de execução do usuário, o código gerado é validado por importação dinâmica e exportação do JSON Schema Pydantic.

### Q37. Representação de valores decimais (RF-03)
O tipo decimal exige escolher como o valor aparece no dataset final.

a) No contrato, decimal aceita número ou texto numérico na entrada e tem a restrição opcional `casas_decimais`. No JSON e no JSONL, o valor sai como número; no CSV, como texto com ponto decimal e as casas definidas. **(Sugestão do Claude)**
b) Sempre texto (`"19.90"`) em todos os formatos, para não perder precisão.
c) Sempre número de ponto flutuante, sem controle de casas.
d) Resposta livre.

**Resposta:** a) No contrato, decimal aceita número ou texto numérico e suporta a restrição opcional `casas_decimais`. Serialização numérica para JSON/JSONL e texto com casas fixadas para CSV.

---

## Etapa 10, /reversa-clarify da feature 004-intent-interview (status: RESPONDIDO PELO REVISOR)

> Fonte: `_reversa_forward/004-intent-interview/requirements.md`. Responda com a letra da opção ou com texto livre na linha `**Resposta:**`.

### Q38. Padrões para "não sei" em formato e volume (RN-06, RF-07)
Quando o usuário não sabe o formato ou o volume, a intenção precisa de um valor para seguir.

a) Formato JSONL e volume 10, marcados como padrão no resumo. O volume 10 cabe no limite do harness (100) e gera uma amostra barata. **(Sugestão do Claude)**
b) Formato JSON e volume 10.
c) Formato JSONL e volume 100 (o maior lote de teste do PRD).
d) Resposta livre.

**Resposta:** a) Formato JSONL e volume de 10 registros assumidos como padrão seguro, documentados no resumo de intenção.

### Q39. Modo Expresso com os 5 itens indefinidos (RN-08, RF-14)
O PRD diz que o Expresso segue sem novas confirmações. A spec (EC-03) pede confirmação quando tudo é "não sei", porque o contrato sai genérico.

a) Pedir 1 confirmação só quando objetivo **e** estrutura forem indefinidos (sem eles, o contrato é o padrão de 1 campo). Em qualquer outro caso, o Expresso segue direto. **(Sugestão do Claude)**
b) Pedir confirmação só quando os 5 itens forem indefinidos, como na spec.
c) Nunca pedir confirmação no Expresso; o resumo apenas avisa que o contrato será genérico.
d) Resposta livre.

**Resposta:** a) Pedir 1 confirmação apenas na condição crítica de ambiguidade (objetivo e estrutura simultaneamente indefinidos). Em qualquer outro cenário, prosseguir sem interrupções.

### Q40. Até onde o modo Expresso encadeia nesta feature
A spec manda encadear schema, amostra, geração e avaliação. Hoje só existe o `schema-builder` (feature 003).

a) Esta feature encadeia até `sintetica schema build`: o resumo do Expresso já indica esse comando. Cada feature seguinte (`sample-preview`, `batch-generator`, `quality-evaluator`) acrescenta o próximo elo. **(Sugestão do Claude)**
b) Esta feature implementa um orquestrador `sintetica run <slug>` que chama as etapas disponíveis e para com aviso nas que ainda não existem.
c) Resposta livre.

**Resposta:** a) Encadeamento progressivo até `sintetica schema build`. As features seguintes estendem os elos subsequentes da cadeia.

---

## Etapa 11, /reversa-clarify da feature 005-sample-preview (status: RESPONDIDO PELO REVISOR)

> Fonte: `_reversa_forward/005-sample-preview/requirements.md`. Responda com a letra da opção ou com texto livre na linha `**Resposta:**`.

### Q41. Tamanho padrão da amostra (RN-02, RF-02)
A amostra aceita de 3 a 5 registros. Qual é o padrão quando o agente não informa N?

a) 3 registros. A 1ª resposta chega mais rápido, e o usuário pode pedir 5 com `--n 5`. **(Sugestão do Claude)**
b) 5 registros, para mostrar mais variedade logo na 1ª amostra.
c) Depende do formato: 3 para CSV e JSON, 5 para conversas (JSONL com `kind: conversation`).
d) Resposta livre.

**Resposta:** a) 3 registros como padrão do sistema. O agente pode especificar `--n 5` se desejar maior volume.

### Q42. Formato do arquivo de semente (RN-07, RF-11)
A spec cita `seeds/sample.<ext>` com metadados (versão do contrato, data de aprovação, provedor). CSV não guarda metadados, e `sintetica request --seeds` (feature 002) aceita sementes só em JSONL.

a) `seeds/sample.jsonl` sempre (1 registro por linha, pronto para `--seeds`), mais `seeds/sample.meta.json` com versão do contrato, data de aprovação, provedor e número de registros. A exibição continua no formato do dataset (tabela para CSV). **(Sugestão do Claude)**
b) Arquivo no formato do dataset (`sample.csv`, `sample.json` ou `sample.jsonl`) mais `sample.meta.json`; a geração em lote converte para JSONL quando precisar.
c) Um único `seeds/sample.json` com o objeto `SampleFile` da spec (metadados e lista de registros).
d) Resposta livre.

**Resposta:** a) Salvar `seeds/sample.jsonl` sempre para interoperabilidade direta com `--seeds`, acompanhado de `seeds/sample.meta.json` para metadados estruturados.

### Q43. Aprovação de amostra parcial no modo Guiado (RN-08, RF-14)
Depois de 3 tentativas, a amostra pode ter menos de N registros válidos (por exemplo, 2 de 3).

a) Permitir aprovar com pelo menos 1 registro válido, com aviso de que a amostra ficou incompleta; a aprovação grava o número real de registros. No Expresso, amostra parcial nunca é aprovada sozinha: o fluxo para e pede decisão. **(Sugestão do Claude)**
b) Exigir N válidos sempre; com menos, o usuário só pode ajustar ou voltar ao contrato.
c) Permitir aprovar com pelo menos 2 registros válidos.
d) Resposta livre.

**Resposta:** a) Permitir aprovação no modo Guiado com no mínimo 1 registro válido e alerta explícito de amostra parcial. No modo Expresso, interromper a automação e exigir intervenção humana.

---

## Etapa 12, /reversa-clarify da feature 006-batch-generator (status: RESPONDIDO PELO REVISOR)

> Fonte: `_reversa_forward/006-batch-generator/requirements.md`. Responda com a letra da opção ou com texto livre na linha `**Resposta:**`.

### Q44. Lote de teste (até 100 registros) com o agente do harness (RN-03)
A política da feature 002 escolhe o harness quando o volume é ≤ 100 e o harness está disponível. Cada pedido ao harness exige 1 volta: `generate run`, resposta do agente por `submit`, `generate run` de novo.

a) Usar o harness num único pedido de até 100 registros, com as sementes da amostra. As rodadas extras pedem só os faltantes, cada uma com id próprio. Provedores automáticos (Ollama, API externa) usam blocos. **(Sugestão do Claude)**
b) Usar o harness em blocos, como os provedores automáticos (com blocos de 10, 100 registros exigem 10 voltas).
c) Não usar o harness no lote: o harness serve só para a amostra; o lote de teste usa Ollama ou API externa.
d) Resposta livre.

**Resposta:** a) Usar o harness em pedido consolidado de até 100 registros com sementes, solicitando faltantes em rodadas extras. Provedores automáticos utilizam blocos concorrentes.

### Q45. Mecanismo de execução em background para lotes acima de 100 (RN-05, RF-11)
O comando deve devolver o controle ao chat em até 5 s e o progresso deve ficar visível por um comando de status.

a) Processo separado, em sessão própria (desligado do terminal), com o PID e o progresso em `run.json`. O `generate status` mostra o andamento e detecta processo encerrado; o `generate resume` continua do último bloco gravado (RN-09). **(Sugestão do Claude)**
b) Fatias curtas: cada `generate run` processa no máximo cerca de 60 s e devolve `em_andamento`; o agente chama o comando de novo até o fim.
c) Os 2 modos: processo separado por padrão e fatias curtas com `--slice` para harnesses que encerram processos filhos.
d) Resposta livre.

**Resposta:** a) Processo separado em sessão própria desacoplada com PID em `run.json`, comando `status` para acompanhamento e suporte a `--resume` incremental.

### Q46. Tamanho do bloco por pedido aos provedores automáticos (RN-06, RF-06, OQ-02)
A spec fixa 10 registros por pedido. Registros longos, como conversas, podem passar do limite de tokens de saída do provedor.

a) Bloco adaptativo: até 10 registros, reduzido para que a saída estimada (tamanho médio da amostra × registros) fique em cerca de 4.000 tokens, com mínimo de 1. A opção `--block-size` permite ajuste manual. **(Sugestão do Claude)**
b) Bloco fixo de 10 registros para todos os formatos, como na spec.
c) Bloco fixo de 10 registros, e de 3 registros para conversas (JSONL com `kind: conversation`).
d) Resposta livre.

**Resposta:** a) Bloco adaptativo com teto de 10 registros e ajuste dinâmico para respeitar janela de tokens (alvo ~4.000 tokens), com flag `--block-size` para sobreposição manual.

---

## Etapa 13, /reversa-clarify da feature 007-quality-evaluator (status: RESPONDIDO PELO REVISOR)

> Fonte: `_reversa_forward/007-quality-evaluator/requirements.md`. Responda com a letra da opção ou com texto livre na linha `**Resposta:**`.

### Q47. Definição operacional da unicidade semântica (RN-03, RF-04)
A spec fala em "shingles de 3 palavras". A Q27 fala em "3-gramas". Falta definir a unidade, o texto comparado e os textos curtos.

a) 3-gramas de palavras sobre o texto livre do registro: todos os campos de tipo texto (inclusive os de listas e objetos aninhados), unidos na ordem do contrato e normalizados (minúsculas, sem pontuação, espaços únicos). Texto com menos de 3 palavras vira 1 único trecho com o texto inteiro. Campos de escolha fixa (enum), números e datas ficam fora. Registro sem texto livre fica fora da conta; contrato sem texto livre dá "não aplicável". **(Sugestão do Claude)**
b) Mesma regra, mas com 3-gramas de caracteres (mais sensível a textos curtos, como nomes).
c) 3-gramas de palavras calculados por campo de texto; a menor unicidade entre os campos entra no veredito.
d) Resposta livre.

**Resposta:** a) 3-gramas de palavras sobre texto livre agregado e normalizado, com token único para < 3 palavras e exclusão de tipos estruturados fixos (enums/números/datas).

### Q48. Código de saída de `REPROVADO` (RN-10, RF-11)
A spec define o código 2 para `REPROVADO`. O comando `sintetica` já usa o 2 para "dataset, intenção ou argumento inválido" (features 002 a 006).

a) 0 para `APROVADO` e 17 (novo, exclusivo) para `REPROVADO`. Erros de execução seguem os códigos existentes (2 argumento, 9 PII indisponível, 10 escrita, 11 contrato); dataset final ausente ganha o código 18. **(Sugestão do Claude)**
b) Manter o 2 para `REPROVADO`, como na spec; os erros de argumento do `eval` passam a usar o 1.
c) 1 para `REPROVADO` e os códigos existentes para os erros.
d) Resposta livre.

**Resposta:** a) Código 0 para `APROVADO`, código 17 para `REPROVADO` e código 18 para dataset final ausente, preservando a semântica dos erros de execução.

### Q49. Ligação entre o fim do lote e a avaliação (RN-11, RF-14, Q40)
Hoje o `sintetica generate` só indica a avaliação como próximo passo, sem comando.

a) O fim do lote roda a avaliação na mesma execução, em primeiro plano e no processo em background, em todo status final. O relatório fica pronto quando o lote termina. O comando `sintetica eval <slug>` também existe para avaliação avulsa. O código de saída do `generate` não muda com o veredito; o veredito aparece na saída e no `report.json`. **(Sugestão do Claude)**
b) O lote só indica `uv run sintetica eval <slug>`; o agente roda a avaliação como passo seguinte.
c) Avaliação automática só no background; em primeiro plano, o agente roda o comando.
d) Resposta livre.

**Resposta:** a) Disparo automático da avaliação ao concluir o lote em foreground e background, mantendo `sintetica eval <slug>` disponível para execuções avulsas e CI.

---

## Etapa 14, /reversa-clarify da feature 008-cli-installer (status: RESPONDIDO PELO REVISOR)

> Fonte: `_reversa_forward/008-cli-installer/requirements.md`. Responda com a letra da opção ou com texto livre na linha `**Resposta:**`.

### Q50. Como o runtime Python chega ao projeto do usuário (RN-06, RF-08)
As skills chamam o runtime (`sintetica start`, `schema`, `sample`, `generate`, `eval`). O projeto do usuário pode nem ter `pyproject.toml`, e a spec diz que o instalador não instala Python nem `uv` (NG-01).

a) O pacote npm leva o pacote Python pronto (arquivo wheel da mesma versão). O instalador copia o wheel para `.sintetica/runtime/` e cria um lançador `.sintetica/bin/sintetica` (mais `sintetica.cmd` no Windows) que roda `uvx --from <wheel> sintetica`. As skills chamam o lançador. Não altera o `pyproject.toml` do usuário, não depende de publicar no PyPI, e npm e Python ficam sempre na mesma versão. As dependências Python (Pydantic, Faker, httpx) vêm do PyPI na 1ª execução. **(Sugestão do Claude)**
b) Publicar o pacote Python no PyPI; as skills chamam `uvx --from sintetica==<versão> sintetica ...`.
c) O instalador roda `uv tool install sintetica==<versão>` (instalação global do comando).
d) O instalador acrescenta `sintetica` como dependência no `pyproject.toml` do usuário e as skills chamam `uv run sintetica`.
e) Resposta livre.

**Resposta:** a) Empacotar o wheel no pacote npm, copiá-lo para `.sintetica/runtime/` e gerar lançador `.sintetica/bin/sintetica` executando `uvx --from <wheel> sintetica`, com fallback transparente para `uv run sintetica` em ambiente de desenvolvimento.

### Q51. Marcadores e destinos dos harnesses (RN-02, RF-02, OQ-01)
O PRD manda instalar no formato universal, sem adaptação por engine. A spec lista os marcadores de cada harness.

a) Marcadores: Claude Code `.claude/`; Antigravity `.agents/` ou `.agent/`; Cursor `.cursor/`; Gemini CLI `.gemini/`; Codex `.codex/` ou `AGENTS.md`. Destinos: sempre `.agents/skills/` e `.claude/skills/`, para qualquer harness detectado ou nenhum. A detecção só informa o resumo e `state.json`. **(Sugestão do Claude)**
b) Mesmos marcadores, e também uma cópia no destino próprio de cada harness detectado (`.cursor/skills/`, `.gemini/skills/`, `.codex/skills/`).
c) Instalar só nos destinos dos harnesses detectados; sem harness detectado, perguntar o destino.
d) Resposta livre.

**Resposta:** a) Marcadores especificados para detecção contextual e gravação em `state.json`. Destinos padronizados universais em `.agents/skills/` e `.claude/skills/`.

### Q52. Linguagem, verificação estática e cobertura do instalador (RN-11, OQ-02)
O runtime Python usa `mypy --strict`, `ruff` e `pytest-cov` ≥ 80% (Q19). O instalador roda em Node.js ≥ 18 e não deve ter dependências de produção.

a) JavaScript em módulos ES, com tipos em comentários JSDoc verificados por `tsc --checkJs --strict` (sem etapa de build: o pacote publicado é o próprio código). Testes com o `node:test` embutido e cobertura ≥ 80% de linhas medida pelo `c8`. Dependências só de desenvolvimento: `typescript`, `c8` e `@types/node`. **(Sugestão do Claude)**
b) TypeScript com `tsc --strict` e build para `dist/`, testes com `node:test` e cobertura pelo `c8`.
c) TypeScript com `vitest` e cobertura pelo provedor `v8` do `vitest`.
d) Resposta livre.

**Resposta:** a) JavaScript ESM nativo com anotações JSDoc validadas via `tsc --checkJs --strict`, runner nativo `node:test`, cobertura via `c8` e zero dependências de produção.

---

## Etapa 15, reversa-reviewer da re-extração completa (status: RESPONDIDA, processada em 2026-10-12)

> Fonte: `_reversa_sdd/gaps.md`. Lacunas 🔴 e 🟡 que dependem de decisão humana. Nenhuma bloqueia a reimplementação a partir das specs.

### Q53. Suporte a Windows (gaps G-01)
O ramo Windows (trava `msvcrt`, processo `DETACHED_PROCESS`, lançador `.cmd`) existe, mas não tem teste real.

a) Manter o suporte declarado e criar uma feature para rodar a suíte num ambiente Windows (CI ou máquina). **(Sugestão do Claude)**
b) Declarar o Windows como "experimental" na documentação até haver teste real.
c) Declarar só macOS e Linux como suportados.
d) Resposta livre.

✅ Respondida

**Resposta:** b) Declarar Windows como experimental na documentação até haver runner de teste específico em CI.

### Q54. Diversidade além dos quase-duplicados (gaps G-02)
A métrica de diversidade do PRD virou só unicidade estrutural e semântica (Q16). Cobertura de temas e distribuição de valores não são medidas.

a) Manter como está no MVP e registrar a métrica de cobertura como evolução futura. **(Sugestão do Claude)**
b) Criar uma feature com métricas de distribuição por campo (`enum` e numéricos) no relatório, sem entrar no veredito.
c) Resposta livre.

✅ Respondida

**Resposta:** a) Manter as métricas vigentes no MVP e catalogar dispersão temática como evolução de roadmap.

### Q55. Instrução "1 objeto JSON por linha" na amostra (gaps G-03)
A amostra manda essa instrução também a provedores automáticos, cujo prompt de sistema pede `{"records": [...]}`. O lote já manda a instrução só ao harness.

a) Corrigir a amostra como no lote: a instrução só vai ao harness (ajuste curto pelo `/reversa-add` na feature 005). **(Sugestão do Claude)**
b) Manter: os modelos seguem o prompt de sistema e o parser aceita só `{"records": [...]}`.
c) Resposta livre.

✅ Respondida

**Resposta:** a) Alinhar a amostra ao padrão do lote, enviando a diretiva de linhas individuais exclusivamente ao harness.

### Q56. `schema build` sem intenção confirmada (gaps G-04)
O `build` lê a intenção pelo `schema/intent.py` e não confere `confirmed_at`. No Guiado, o contrato pode ser gerado antes da confirmação.

a) Exigir `confirmed_at` no `build` (código 2 com o comando `intent confirm`), salvo no Expresso não crítico. **(Sugestão do Claude)**
b) Manter: a skill orienta o agente a confirmar antes.
c) Resposta livre.

✅ Respondida

**Resposta:** a) Validar `confirmed_at` no `schema build`, orientando a confirmação prévia no modo Guiado.
