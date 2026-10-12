# PRD: sintetica

> Selo 🟡 PLANEJADO. Documento gerado a partir de ideation + personas.

**Versão:** 1.0
**Data:** 2026-10-09T16:19:00Z
**Autor:** reversa-drafter
**Status:** rascunho

---

## 1. Problema

🟡 Faltam dados sintéticos estruturados e rotulados em três frentes: fine-tuning de LLMs, testes funcionais de software e validação de sistemas com dados tabulares ou conversacionais.
🟡 Dados reais são escassos, caros ou contêm PII.
🟡 Hoje, gerar dados sintéticos exige scripts ad hoc (Faker, LLM manual) ou ferramentas com configuração técnica (SDV, distilabel, Gretel).
🟡 Nenhuma alternativa roda como skill conversacional nativa de harness de IA, com entrevista guiada, validação contínua por schema e tolerância a incertezas.
🟡 Scripts manuais com LLM não garantem schema, diversidade, ausência de PII nem reprodutibilidade.

### Quem sente
🟡 **dev-de-testes:** sente o problema ao escrever testes de integração sem massa de dados realista e sem PII.
🟡 **engenheiro-de-ml:** sente o problema no início de um fine-tuning, com poucos exemplos rotulados.
🟡 **analista-de-dados:** sente o problema ao validar um pipeline ou dashboard antes de ter acesso a dados reais.

---

## 2. Personas-alvo

🟡 Referência completa em [`personas.md`](./personas.md). Resumo:

- **dev-de-testes**: 🟡 Desenvolvedor avançado em programação e intermediário em modelagem de dados. Dor: gerar massa de teste exige scripts com Faker ou cópia de produção, com risco de expor PII.
- **engenheiro-de-ml**: 🟡 Engenheiro avançado em ML e Python. Dor: faltam exemplos rotulados diversos; scripts manuais com LLM não garantem schema, diversidade nem ausência de PII.
- **analista-de-dados**: 🟡 Analista intermediário em Python e avançado em SQL e planilhas. Dor: depende de acesso a dados sensíveis para validar o sistema; gerar tabelas coerentes à mão é lento.

---

## 3. Métricas de sucesso

🟡 Horizonte de avaliação: 3 meses após o lançamento do MVP.

| Métrica | Unidade | Alvo | Prazo |
|---|---|---|---|
| 🟡 Tempo da ideia ao dataset validado, lote de teste (até 100 registros) | 🟡 minutos (média) | 🟡 < 10 min | 🟡 3 meses |
| 🟡 Conformidade dos registros com o schema Pydantic | 🟡 % de registros válidos no lote final | 🟡 ≥ 95% | 🟡 3 meses |
| 🟡 Vazamento de PII detectado pelo `sintetica-eval` | 🟡 nº de ocorrências no dataset final | 🟡 0 | 🟡 3 meses |
| 🟡 Diversidade do lote | 🟡 [INDEFINIDO, validar com usuário] | 🟡 [INDEFINIDO, validar com usuário] | 🟡 3 meses |

🟡 **Critério de "vazamento de PII":** ocorrência detectada pelos detectores determinísticos do `sintetica-eval`. Os detectores cobrem regex de CPF, CNPJ, e-mail, telefone, cartão de crédito, IPv4/IPv6 e lista de substituição Faker. A métrica cobre apenas o que esses detectores cobrem. O relatório final documenta o escopo e os limites dessa cobertura (Q9).
🟡 **Lote de produção:** 1.000 a 10.000 registros, gerados em background pelo motor assíncrono. A métrica de tempo não se aplica a esse volume (Q10).

---

## 4. Escopo (in)

🟡 **Distribuição e instalação**
- 🟡 Pacote Node.js executável com `npx sintetica install`.
- 🟡 Detecção automática de harnesses: Claude Code, Antigravity, Cursor, Gemini CLI e Codex.
- 🟡 Injeção de skills e agentes em `.agents/skills/` e `.claude/skills/`, no formato universal de Agent Skills.
- 🟡 Diretório de governança `.sintetica/` com `state.json`, `install-manifest.json` e `policy.json`.

🟡 **Entrevista de intenção**
- 🟡 Criação imediata de `datasets/<slug>/seeds/` antes da primeira pergunta, com exibição do caminho absoluto.
- 🟡 Elicitação sem jargão: objetivo, formato e volume, sem parâmetros de baixo nível.
- 🟡 Modo **Guiado** (passo a passo com confirmações) e modo **Expresso** (entrevista única até a geração).
- 🟡 Resposta "não sei" vira selo `🟡 [INDEFINIDO]`, sem bloquear o fluxo.

🟡 **Pipeline de agentes**
1. 🟡 `sintetica-start`: orquestra a entrevista de intenção.
2. 🟡 `sintetica-schema`: traduz os requisitos em modelos Pydantic v2.
3. 🟡 `sintetica-sample`: gera amostra de 3 a 5 registros para aprovação visual.
4. 🟡 `sintetica-generate`: gera o lote completo de forma concorrente com `asyncio`.
5. 🟡 `sintetica-eval`: verifica qualidade, diversidade e ausência de PII, e emite relatório.

🟡 **Provedores de LLM (porta `LLMProvider`, Clean Architecture)**
- 🟡 `ExternalAPIProvider`: OpenAI, Anthropic, Gemini e Ollama local. Usado na geração em lote de alta vazão pelo runtime Python.
- 🟡 `HarnessAgentProvider`: o próprio assistente do harness gera amostras e protótipos, sem chave de API.

🟡 **Formatos de saída**
- 🟡 Tabular: CSV.
- 🟡 Textual e conversacional: JSON e JSONL (ex.: JSONL de mensagens para fine-tuning).

🟡 **Runtime Python**
- 🟡 `uv` com `pyproject.toml`.
- 🟡 Clean Architecture e OOP.
- 🟡 Tipagem estrita com `mypy`; formatação e lint com `ruff`.
- 🟡 Testes com `pytest`.

---

## 5. Não-objetivos (out)

🟡 Aprovados pelo revisor na Q14.

- 🟡 Interface gráfica web ou desktop. O sintetica roda apenas dentro de harnesses e da CLI.
- 🟡 Geração de imagem, áudio ou vídeo. O MVP cobre apenas dados tabulares (CSV) e textuais/conversacionais (JSON, JSONL).
- 🟡 Treinamento ou fine-tuning de modelos. O sintetica entrega o dataset e para aí.
- 🟡 Síntese a partir de dados reais do usuário (estilo SDV). O MVP gera a partir da intenção descrita.
- 🟡 Serviço hospedado ou SaaS. Tudo roda localmente.
- 🟡 Garantia de anonimização formal (ex.: privacidade diferencial).

---

## 6. Restrições

| Tipo | Descrição |
|---|---|
| 🟡 Técnica | 🟡 Instalador em Node.js (`npx`). Runtime de geração em Python com `uv`, Pydantic v2, `asyncio`, `mypy` estrito, `ruff` e `pytest`. Clean Architecture com porta `LLMProvider`. Skills no formato universal de Agent Skills, sem adaptação por engine. |
| 🟡 Técnica | 🟡 Versões mínimas de Node.js e Python: [INDEFINIDO, validar com usuário]. Meta de cobertura de testes ("alta cobertura") sem valor numérico: [INDEFINIDO, validar com usuário]. |
| 🟡 Prazo | 🟡 Sem prazo rígido para o MVP (Q15). |
| 🟡 Compliance | 🟡 Privacidade por design, alinhada à LGPD. Operação local. Sem telemetria não autorizada. Política de privacidade e governança em `.sintetica/policy.json`. Sem certificação formal no MVP (Q15). |
| 🟡 Orçamento | 🟡 [INDEFINIDO, validar com usuário]. O custo de tokens do `ExternalAPIProvider` recai sobre o usuário; não há teto definido. |

---

## 7. Dependências externas

- 🟡 **Registro npm:** distribuição do instalador via `npx sintetica install`.
- 🟡 **Harnesses de IA:** Claude Code, Antigravity, Cursor, Gemini CLI e Codex, para executar as skills.
- 🟡 **APIs de LLM (opcionais):** OpenAI, Anthropic e Gemini, com chave em variável de ambiente, via `ExternalAPIProvider`.
- 🟡 **Ollama (opcional):** LLM local via `ExternalAPIProvider`, sem envio de dados para fora da máquina.
- 🟡 **Bibliotecas Python:** Pydantic v2 (contratos) e Faker (mascaramento e substituição de PII).
- 🟡 **Ferramentas de runtime:** `uv` e Node.js instalados na máquina do usuário.

---

## 8. Riscos

| Risco | Impacto | Probabilidade | Mitigação proposta |
|---|---|---|---|
| 🟡 Diversidade e qualidade da geração via LLM insuficientes para uso real (premissa 1) | 🟡 alto | 🟡 média | 🟡 Amostra de 3 a 5 registros aprovada antes do lote (`sintetica-sample`) e verificação semântica no `sintetica-eval`. |
| 🟡 Detecção heurística local de PII deixa passar casos não cobertos pelos detectores (premissa 2) | 🟡 alto | 🟡 média | 🟡 Detectores determinísticos com lista configurável. Relatório documenta escopo e limites da cobertura. Métrica definida como "0 ocorrências detectadas". |
| 🟡 Harnesses alvo divergem no formato de skill e exigem adaptação por engine (premissa 3) | 🟡 médio | 🟡 média | 🟡 Distribuição pela especificação universal de Agent Skills em `.agents/skills/` e `.claude/skills/`. Detecção de harness no instalador. |
| 🟡 O usuário digita dados reais na entrevista e o `ExternalAPIProvider` os envia a uma API externa | 🟡 alto | 🟡 baixa | 🟡 Aviso na entrevista e regra em `.sintetica/policy.json`. Opção de Ollama local. [Mitigação a validar com usuário]. |
| 🟡 Lote de teste (100 registros) passa de 10 minutos por limite de taxa ou latência da API | 🟡 médio | 🟡 média | 🟡 Concorrência com `asyncio` e controle de taxa por provedor. |
| 🟡 Custo de tokens alto em lotes de produção (1.000 a 10.000 registros) | 🟡 médio | 🟡 média | 🟡 Estimativa de custo antes da geração. [INDEFINIDO: teto de orçamento]. |
| 🟡 Taxa de conformidade < 95% por saída malformada do LLM | 🟡 médio | 🟡 média | 🟡 Validação Pydantic por registro, com descarte ou nova tentativa dos inválidos. |
| 🟡 Respostas `[INDEFINIDO]` em excesso geram schema vago | 🟡 médio | 🟡 baixa | 🟡 Revisão do schema Pydantic e aprovação da amostra antes do lote. |

---

## 9. Critérios de aceite (alto nível)

- 🟡 **Dado** um projeto sem o sintetica, **Quando** o usuário executa `npx sintetica install`, **Então** o instalador detecta os harnesses presentes, injeta as skills em `.agents/skills/` e `.claude/skills/` e cria `.sintetica/` com `state.json`, `install-manifest.json` e `policy.json`.
- 🟡 **Dado** o sintetica instalado, **Quando** o usuário executa `/sintetica-start`, **Então** a pasta `datasets/<slug>/seeds/` existe e o caminho absoluto aparece antes da primeira pergunta.
- 🟡 **Dado** uma pergunta da entrevista, **Quando** o usuário responde "não sei", **Então** o item recebe o selo `🟡 [INDEFINIDO]` e a entrevista continua.
- 🟡 **dev-de-testes:** **Dado** a descrição das entidades do sistema, formato JSON ou CSV e até 100 registros, **Quando** o usuário aprova o schema e a amostra, **Então** recebe o lote em menos de 10 minutos, com ≥ 95% de conformidade e 0 ocorrências de PII no relatório.
- 🟡 **engenheiro-de-ml:** **Dado** a descrição da tarefa, dos rótulos e do formato JSONL de mensagens, **Quando** o usuário aprova a amostra de 3 a 5 conversas e pede 1.000 a 10.000 registros, **Então** o lote é gerado em background pelo `ExternalAPIProvider` e o relatório traz qualidade, diversidade e PII.
- 🟡 **analista-de-dados:** **Dado** a descrição das colunas e regras de negócio em linguagem natural, **Quando** o usuário aprova o schema com tipos e restrições por coluna, **Então** recebe um CSV que respeita essas regras e carrega no pipeline ou dashboard.
- 🟡 **Dado** o modo Expresso, **Quando** o usuário responde a entrevista única, **Então** o pipeline segue até o relatório do `sintetica-eval` sem novas confirmações.

---

## Pendências de cobertura

- 🟡 **Métrica de diversidade:** unidade e alvo não definidos. O `sintetica-eval` verifica diversidade, mas não há critério mensurável.
- 🟡 **Orçamento:** sem teto de custo de tokens para o `ExternalAPIProvider`.
- 🟡 **Versões mínimas:** Node.js e Python não definidos.
- 🟡 **Cobertura de testes:** "alta cobertura" sem valor percentual.
- 🟡 **Medição do tempo:** pontos de início e fim da métrica "ideia ao dataset" não definidos. Proposta a validar: início em `/sintetica-start`, fim na emissão do relatório do `sintetica-eval`.
- 🟡 **Dados reais na entrevista:** mitigação do risco de envio de dados reais à API externa precisa de validação.

---

Gerado por reversa-drafter em 2026-10-09T16:19:00Z
Fontes: ideation.md, personas.md, questions.md (Q8 a Q10, Q14, Q15)
