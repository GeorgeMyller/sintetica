# Máquinas de estado: sintetica

> Gerado pelo Detetive do Reversa em 2026-10-12. 🟢 extraído do código, salvo marcação.

## 1. Intenção (`intent.json`)

🟢 Estado derivado de `Item.status`, `format`, `volume` e `confirmed_at` (`intent/summary.py`).

```mermaid
stateDiagram-v2
    [*] --> Incompleta: sintetica start (started_at)
    Incompleta --> Incompleta: intent set (falta item)
    Incompleta --> AguardandoConfirmacao: intent set completa<br/>Guiado, ou Expresso crítico
    Incompleta --> Pronta: intent set completa<br/>Expresso não crítico
    AguardandoConfirmacao --> Pronta: intent confirm (confirmed_at)
    Pronta --> AguardandoConfirmacao: intent set (zera confirmed_at)<br/>Guiado ou crítico
    Pronta --> Pronta: intent set (Expresso não crítico)
    Pronta --> [*]: schema build
```

| Item de texto | Estados | Transição |
|---------------|---------|-----------|
| `objective`, `structure`, `rules` | `pendente` → `definido` (texto mascarado) ou `indefinido` (`--unknown`) | Qualquer resposta nova substitui |

## 2. Contrato (`schema.state.json`)

```mermaid
stateDiagram-v2
    [*] --> em_revisao: schema build (Guiado), rounds 0
    [*] --> aprovado: schema build (Expresso)
    em_revisao --> em_revisao: build com versão nova (rounds + 1)
    em_revisao --> aprovado: schema approve
    aprovado --> em_revisao: build com versão nova (Guiado)
    aprovado --> aprovado: build com a mesma versão
    aprovado --> aprovado: build com versão nova (Expresso)
```

🟢 Com `rounds ≥ 5` em revisão, a saída sugere reiniciar a entrevista (`schema/state.py:43-45`).

## 3. Amostra (`sample.state.json`)

```mermaid
stateDiagram-v2
    [*] --> aguardando_agente: sample run (pedido gravado)
    aguardando_agente --> aguardando_agente: sample run sem resposta,<br/>ou nova tentativa pendente
    aguardando_agente --> em_revisao: N válidos (Guiado),<br/>ou 3 tentativas (Guiado)
    aguardando_agente --> aprovada: N válidos (Expresso)
    aguardando_agente --> interrompida: 3 tentativas parcial (Expresso)
    em_revisao --> aprovada: sample approve (≥ 1 registro)
    interrompida --> aprovada: sample approve
    em_revisao --> aguardando_agente: sample adjust (rodada + 1)
    interrompida --> aguardando_agente: sample adjust
    aprovada --> [*]: generate
```

🟢 Versão nova do contrato descarta o estado e recomeça (`sample/service.py:313-316`). Provedores automáticos passam direto por `aguardando_agente` (sem pedido pendente).

## 4. Lote (`output/run.json`)

```mermaid
stateDiagram-v2
    [*] --> em_andamento: generate ≤ 100 (automático)
    [*] --> aguardando_agente: generate ≤ 100 (harness)
    [*] --> iniciando: generate > 100
    iniciando --> em_andamento: processo em background grava o PID
    aguardando_agente --> aguardando_agente: rodada extra pendente
    aguardando_agente --> concluido: ≥ 95%
    aguardando_agente --> incompleto: < 95% após 4 rodadas
    em_andamento --> concluido: ≥ 95%
    em_andamento --> incompleto: < 95% após 4 rodadas
    em_andamento --> interrompido_custo: teto de custo
    em_andamento --> falha_provedor: ProviderError
    aguardando_agente --> falha_provedor: ProviderError
    em_andamento --> em_andamento: generate --resume<br/>(processo encerrado ou falha de mascaramento/escrita)
    falha_provedor --> em_andamento: generate --resume
    incompleto --> em_andamento: generate --resume
    interrompido_custo --> em_andamento: generate --resume [--authorize-usd]
    concluido --> [*]: avaliação no fim do lote
    concluido --> em_andamento: generate --new (apaga output/)
```

🟢 Estados finais: `concluido`, `incompleto`, `interrompido_custo`, `falha_provedor` (`batch/state.py:36-38`). "Processo encerrado" não é status: é `em_andamento` (ou `iniciando` há mais de 10 s) com a trava livre (`batch/service.py:231-243`).

## 5. Pedido do harness (`requests/<id>.*`)

```mermaid
stateDiagram-v2
    [*] --> Pendente: save_request (id.json)
    Pendente --> Respondido: sintetica submit (id.response.jsonl)
    Pendente --> Pendente: submit inválido (código 5, nada gravado)
    Respondido --> Lido: sample run / generate lê a resposta
    Lido --> [*]: resposta bruta apagada (PII)
```

## 6. Veredito da avaliação (`report.json`)

🟢 Não há transição persistida: cada `eval` recalcula. `APROVADO` ↔ `REPROVADO` muda só se o dataset, o contrato ou a allowlist mudarem.

## 7. Arquivo no instalador

```mermaid
stateDiagram-v2
    [*] --> Ausente
    Ausente --> Instalado: criar
    Instalado --> Instalado: igual (nada gravado)
    Instalado --> Instalado: substituir (versão nova, sem edição)
    Instalado --> EditadoPeloUsuario: usuário edita
    EditadoPeloUsuario --> Instalado: pergunta respondida sim (ou --yes)
    EditadoPeloUsuario --> EditadoPeloUsuario: resposta não / sem terminal
```

🟢 `policy.json` válido nunca sai de "editado/preservado"; inválido vira `.bak` e volta ao padrão.
