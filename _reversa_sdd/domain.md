# Domínio: sintetica

> Gerado pelo Detetive do Reversa em 2026-10-12. Nível: completo.
> Fontes: código em `src/sintetica/` e `installer/` (🟢), decisões em `_reversa_sdd/questions.md` (Q1 a Q52) e `_reversa_forward/001` a `008` (🟢 quando o código confirma; 🟡 quando só a decisão registra).
> O projeto não tem histórico git; a arqueologia de decisões usa os artefatos do ciclo forward.

## 1. Propósito

🟢 O sintetica gera datasets sintéticos a partir de uma intenção descrita em linguagem natural, dentro do harness de IA do usuário (Claude Code, Antigravity, Cursor, Gemini CLI, Codex). O pipeline tem 5 etapas, cada uma uma skill: entrevista → contrato → amostra → lote → avaliação. A privacidade é por design: dados pessoais nunca vão ao disco nem a APIs externas sem mascaramento (Q1, Q2, Q15, Q21).

## 2. Glossário

| Termo | Definição | Onde |
|-------|-----------|------|
| **Dataset** | Conjunto de registros sintéticos com pasta própria `datasets/<slug>/` | 🟢 `intent/slug.py` |
| **Slug** | Nome kebab-case ASCII do dataset, até 60 caracteres; repetido ganha `-2`, `-3` | 🟢 `intent/slug.py` |
| **Intenção** | Objetivo, estrutura, regras, formato e volume pedidos pelo usuário (`intent.json`) | 🟢 `intent/model.py` |
| **Modo Guiado / Expresso** | Guiado: 1 pergunta por vez e confirmações; Expresso: entrevista única e encadeamento sem paradas, salvo custo e casos críticos | 🟢 `intent/summary.py`, Q39 |
| **"Não sei" / indefinido** | Resposta que não bloqueia: texto vira `indefinido`; formato vira JSONL; volume vira 10 | 🟢 `intent/answers.py`, Q38 |
| **Contrato** | Definição declarativa dos campos (`schema.json`) e o `Record` Pydantic gerado (`schema.py`) | 🟢 `schema/` |
| **Rascunho** | `schema.draft.json` escrito pelo agente; só dados, nunca código | 🟢 `schema/service.py` |
| **Versão do contrato** | SHA-256 do JSON canônico da definição | 🟢 `schema/version.py` |
| **Rodada de ajuste** | Cada versão nova do contrato sobre um existente | 🟢 `schema/state.py` |
| **Registro de conversa** | `Record(messages, labels)` para fine-tuning | 🟢 `schema/codegen.py` |
| **Amostra** | 3 a 5 registros aprovados antes do lote | 🟢 `sample/` |
| **Semente** | Amostra aprovada (`seeds/sample.jsonl` + `sample.meta.json`), usada como exemplos no lote | 🟢 `sample/state.py`, Q42 |
| **Lote** | Geração do volume completo (1 a 10.000) | 🟢 `batch/` |
| **Bloco** | Pedido de até 10 registros (adaptativo) a um provedor automático | 🟢 `batch/plan.py`, Q46 |
| **Rodada (lote)** | 1ª passada + até 3 rodadas extras para repor descartados | 🟢 `batch/state.py` |
| **Lote de teste / produção** | ≤ 100 registros (primeiro plano, meta < 10 min) / > 100 (background) | 🟢 `batch/service.py`, Q10, Q28 |
| **Provedor** | Quem gera os registros: agente do harness, Ollama ou API externa | 🟢 `providers/` |
| **Protocolo request/submit** | Pedido em arquivo para o agente do harness e resposta enviada por `sintetica submit` | 🟢 `providers/harness/`, Q29 |
| **Teto de custo** | Valor máximo de gasto (padrão US$ 5,00) sem autorização explícita | 🟢 `providers/policy.py`, Q17 |
| **PII** | Dado pessoal detectável: CPF, CNPJ, e-mail, telefone, cartão, IPv4, IPv6 e padrões extras | 🟢 `pii/domain.py`, Q9 |
| **Mascaramento** | Troca de PII por valor falso do mesmo tipo e formato | 🟢 `pii/guard.py` |
| **Allowlist** | Hashes dos valores falsos inseridos; o que está nela não é vazamento | 🟢 `pii/allowlist.py`, Q23/Q26 |
| **Vazamento** | Achado de PII fora da allowlist | 🟢 `pii/guard.py:146` |
| **Conformidade** | Válidos ÷ volume pedido | 🟢 `quality/service.py` |
| **Unicidade estrutural / semântica** | Distintos pelo JSON canônico / sem quase-duplicados (Jaccard ≥ 0,8 em 3-gramas) | 🟢 `quality/`, Q16, Q27, Q47 |
| **Veredito** | `APROVADO` ou `REPROVADO` pelas metas do PRD | 🟢 `quality/metrics.py` |
| **Lançador** | `.sintetica/bin/sintetica`, que roda o runtime do wheel instalado | 🟢 `installer/src/runtime.js`, Q50 |
| **Harness** | Ambiente de agente de IA onde as skills rodam | 🟢 `installer/src/detect.js` |

## 3. Regras de negócio

### 3.1 Entrevista (`intent`)

1. 🟢 A pasta do dataset e `started_at` existem antes da 1ª pergunta; a medição de tempo começa aí (Q20). `intent/service.py:52`
2. 🟢 Cada chamada de resposta é tudo ou nada; só o contador de recusas de volume é gravado num erro. `intent/answers.py:149-150`
3. 🟢 Volume de 1 a 10.000; na 3ª recusa seguida vale o padrão 10. `intent/answers.py:119-135`
4. 🟢 Objetivo, estrutura e regras são mascarados antes de qualquer gravação; política inválida bloqueia tudo (código 9). `intent/answers.py:152-168`
5. 🟢 Qualquer resposta nova exige nova confirmação. `intent/answers.py:172-173`
6. 🟢 Guiado sempre confirma; Expresso confirma só com objetivo **e** estrutura indefinidos (Q39). `intent/summary.py:26-34`

### 3.2 Contrato (`schema`)

7. 🟢 O runtime nunca executa código escrito pelo modelo: o agente escreve dados; o código vem de um gerador determinístico com textos escapados. `schema/codegen.py`
8. 🟢 O formato do contrato precisa ser o da intenção. `schema/service.py:114-117`
9. 🟢 Até 100 campos; conversa só em JSON/JSONL; restrições só nos tipos permitidos. `schema/checks.py`
10. 🟢 Em CSV, listas viram 1 coluna com `|`; objetos viram colunas com prefixo; listas de objetos são recusadas (Q35). `schema/csvflat.py`
11. 🟢 Decimal é número exato em JSON e texto com casas fixas em CSV (Q37). `schema/formats.py`
12. 🟢 Estrutura indefinida gera o contrato padrão de 1 campo `descricao`. `schema/intent.py:51`
13. 🟢 Expresso aprova o contrato no `build`; após 5 rodadas sem aprovação, a saída sugere reiniciar. `schema/state.py`
14. 🟡 O `build` não confere a confirmação da intenção (lacuna conhecida desde a feature 003). Decisão (Q56): exigir `confirmed_at`; correção pendente.

### 3.3 Provedores (`providers`)

15. 🟢 Ordem padrão: harness → Ollama → API externa (Q8). `providers/policy.py:19`
16. 🟢 O harness atende até 100 registros por pedido; o lote escolhe o provedor pelo volume total. `providers/selection.py:47`, `batch/service.py:210`
17. 🟢 Todo pedido a provedor automático é mascarado, inclusive no Ollama (Q21, Q30). `providers/factory.py:66-70`
18. 🟢 Acima do teto, ou com preço desconhecido, o custo exige autorização explícita do valor (Q17). `providers/external/provider.py:107-114`
19. 🟢 O custo acumulado nunca passa do autorizado; o teto para a fila com `"teto de custo"`. `providers/decorators/budget.py`
20. 🟢 Só falhas temporárias têm nova tentativa (3 chamadas, 1 s e 2 s) (Q33). `providers/decorators/retrying.py`
21. 🟢 Chaves de API só no ambiente, lidas por chamada; mensagens citam o nome da variável, nunca o valor. `providers/errors.py`, `external/provider.py:57-64`
22. 🟢 Pedido igual tem o mesmo id; por isso cada tentativa ou rodada leva o seu número no texto. `providers/harness/store.py:36`, `sample/request.py`, `batch/request.py`

### 3.4 PII (`pii`)

23. 🟢 7 tipos fixos e padrões extras da política (Q9). `pii/domain.py`
24. 🟢 Telefone só formatado ou com `+55` (Q25). `pii/detectors.py:52-61`
25. 🟢 Valor falso precisa ter o mesmo formato e ser detectável; sem substituto, `***`. `pii/guard.py:116-144`
26. 🟢 Relatórios e mensagens mostram só a prévia (2 caracteres + `***`). `pii/domain.py:71`

### 3.5 Amostra (`sample`)

27. 🟢 Só com contrato aprovado e atual. `sample/service.py:85-116`
28. 🟢 N de 3 a 5, padrão 3 (Q41); 3 tentativas por rodada. `sample/state.py`
29. 🟢 A resposta bruta do harness é apagada depois de lida. `sample/service.py:177-190`
30. 🟢 Expresso aprova sozinho só com N válidos; Guiado aprova parcial com ≥ 1 registro e alerta (Q43). `sample/service.py:220-237`
31. 🟢 A partir da 4ª rodada de ajuste, a saída sugere voltar ao contrato. `sample/service.py:50`

### 3.6 Lote (`batch`)

32. 🟢 Só com amostra aprovada para a mesma versão do contrato. `batch/service.py:161-176`
33. 🟢 Harness: 1 pedido por rodada (Q44); automático: blocos adaptativos (Q46). `batch/engine.py`, `batch/plan.py`
34. 🟢 `concluido` com ≥ 95% do volume; `incompleto`, `interrompido_custo` e `falha_provedor` também geram o arquivo final. `batch/engine.py:58-75`
35. 🟢 Cada bloco é gravado com `fsync` antes do estado; a retomada não repete blocos nem gera custo por eles. `batch/output.py`
36. 🟢 Acima de 100 registros, processo separado; 1 lote por dataset (trava) (Q28, Q45). `batch/lock.py`, `batch/background.py`
37. 🟢 Lote existente nunca é sobrescrito sem `--new`. `batch/service.py:329-378`
38. 🟢 A avaliação roda no fim do lote; o veredito não muda o código do `generate` (Q49). `batch/service.py:505-509`

### 3.7 Avaliação (`quality`)

39. 🟢 `APROVADO` só com conformidade ≥ 95%, unicidades ≥ 90% e 0 vazamentos (Q5, Q16). `quality/metrics.py:117`
40. 🟢 Conformidade sobre o volume pedido pelo lote. `quality/service.py:131`
41. 🟢 Unicidade semântica: Jaccard ≥ 0,8 em 3-gramas de palavras do texto livre; "não aplicável" sem texto livre (Q27, Q47). `quality/semantic.py`, `quality/text.py`
42. 🟢 A meta de tempo (< 10 min até 100 registros) é medida e não entra no veredito (Q20). `quality/metrics.py:111`
43. 🟢 `REPROVADO` termina com 17 e dataset ausente com 18 (Q48). `quality/service.py:55-56`

### 3.8 Instalação (`installer`)

44. 🟢 Node ≥ 18 (Q18); skills sempre em `.agents/skills/` e `.claude/skills/` (Q51). `installer/src/`
45. 🟢 Nenhum arquivo do usuário é substituído sem confirmação; `--yes` nunca substitui a política. `installer/src/plan.js`, `prompt.js`
46. 🟢 Falha no meio desfaz tudo; 2ª execução igual não grava nada. `installer/src/files.js`, `install.js`
47. 🟢 O runtime chega como wheel no pacote npm e roda por `uvx` (Q50). `installer/src/runtime.js`

## 4. Metas do produto (PRD)

| Meta | Valor | Medida em |
|------|-------|-----------|
| Tempo da ideia ao dataset (≤ 100 registros) | < 10 min | `quality/metrics.py` (`duration_min`) |
| Conformidade | ≥ 95% | `quality` e status `concluido` do `batch` |
| Unicidade estrutural e semântica | ≥ 90% | `quality` |
| Vazamentos de PII detectados | 0 | `quality` |

## 5. Lacunas

- 🟡 O `schema build` aceita intenção não confirmada (regra 14). Correção decidida na Q56.
- 🟡 Registro com PII repetido entre tentativas ou depois de uma retomada pode passar como novo, porque os valores falsos diferem.
- 🟡 O ramo Windows (trava `msvcrt`, processo `DETACHED_PROCESS`, lançador `.cmd`) é experimental: sem teste real até existir um runner Windows em CI (Q53).
- 🟢 A diversidade semântica além de quase-duplicados (cobertura de temas, distribuição) fica fora do MVP: as métricas vigentes são as unicidades (Q16), e a dispersão temática entra no roadmap (Q54).
