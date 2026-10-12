# Investigation: llm-provider

> Identificador: `002-llm-provider`
> Data: `2026-10-09`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Pergunta de fundo

🟡 Como oferecer 1 porta de geração para 4 APIs externas e para o agente do harness, com custo previsível, mascaramento obrigatório e testes sem rede?

## 2. Alternativas avaliadas

### 2.1 Cliente das APIs externas

| Opção | Prós | Contras | Veredito |
|-------|------|---------|----------|
| SDKs oficiais (`openai`, `anthropic`, `google-genai`, `ollama`) | Tipos prontos; acompanham mudanças da API | 4 dependências; cada SDK tem retry e timeout próprios, que competem com a RF-09; simulação por SDK é diferente | Descartada |
| `httpx.AsyncClient` + adaptador fino por backend | 1 dependência; retry, timeout e concorrência num só lugar; `MockTransport` simula os 4 backends igual | Formatos de API mantidos à mão | 🟡 **Adotada** (D-03) |
| Biblioteca de abstração multi-provedor (ex.: LiteLLM) | Muitos backends prontos | Dependência pesada; telemetria e chamadas próprias contrariam Q15; controle fraco do custo | Descartada |

### 2.2 Onde ficam as regras transversais

| Opção | Prós | Contras | Veredito |
|-------|------|---------|----------|
| Dentro de cada adaptador | Menos classes | Mascaramento e teto duplicados; fácil esquecer em 1 backend (G-02 pede 0 falhas) | Descartada |
| Decoradores sobre a porta `LLMProvider` | 1 implementação por regra; teste isolado; ordem explícita | Mais classes pequenas | 🟡 **Adotada** (D-04) |

🟡 Ordem escolhida, de fora para dentro: teto → concorrência → mascaramento → retry → adaptador.
- O teto decide antes de ocupar vaga de concorrência.
- O mascaramento roda 1 vez por pedido, não 1 vez por tentativa. Assim a allowlist não recebe substitutos duplicados.
- O retry fica colado ao adaptador e só repete a chamada HTTP.

### 2.3 Harness sem bloqueio

🟡 O agente do harness executa comandos em sequência. Se `sintetica request` esperasse a resposta, o agente nunca chegaria ao `submit`. Por isso `generate` tem 2 resultados possíveis: resultado pronto ou `HarnessResponsePending`. O chamador (`sample-preview`) trata a exceção mostrando o comando ao agente (D-13).

### 2.4 Estimativa de custo

🟡 As APIs cobram entrada e saída com preços diferentes. A RF-06 define 1 preço por token. A estimativa usa o preço de saída, que é o maior nos backends pagos. Ela tende a superestimar, o que é o lado seguro para o teto da Q17. O custo real usa os 2 preços e os tokens informados pela API (D-16).

### 2.5 Retry: 3 tentativas

🟡 A RF-09 cita esperas de 1 s, 2 s e 4 s e "no máximo 3 tentativas". Os cenários Gherkin fixam 3 chamadas no total. Com 3 chamadas, só existem 2 esperas (1 s e 2 s). O plano segue os cenários, que são testáveis (D-19).

## 3. Padrões aplicáveis

- 🟡 Ports and Adapters (Clean Architecture), já usado em `sintetica.pii`.
- 🟡 Decorator para regras transversais.
- 🟡 Factory para a seleção e a montagem da pilha.
- 🟡 Idempotência por hash de conteúdo, já usada na allowlist da feature 001 (SHA-256).
- 🟡 Reserva de orçamento sob `asyncio.Lock` (semelhante a um semáforo de custo).

## 4. Referências

- 🟡 Documentação do `httpx`: `AsyncClient`, `MockTransport`, `Timeout`.
- 🟡 Documentação vigente das APIs OpenAI Chat Completions, Anthropic Messages, Gemini `generateContent` e Ollama `/api/chat`. Os formatos em `interfaces/` devem ser conferidos contra elas no início do coding (premissa do roadmap).
- 🟢 `_reversa_sdd/addenda/001-pii-guard.md`: fachada `PiiGuard` e falha segura.
- 🟢 `_reversa_sdd/questions.md`: Q8, Q17, Q21, Q29, Q30, Q31.

## 5. Pontos em aberto

- 🟡 Q32: identificadores de modelo vigentes para `defaults.json` (não bloqueia o plano; bloqueia o fechamento da feature).
