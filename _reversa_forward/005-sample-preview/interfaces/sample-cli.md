# Interface: `sintetica sample` (amostra para aprovação)

> Tipo: arquivo + CLI. Origem: RN-01 a RN-09, RF-01 a RF-16, D-02 a D-17. Confidência: 🟡.

## 1. `sintetica sample run`

```
uv run sintetica sample run <slug> [--n 3..5] [--project-dir <dir>]
```

| Situação | Resultado | Código de saída |
|----------|-----------|-----------------|
| Dataset ou intenção ausente; `--n` fora de 3 a 5 | Erro | 2 |
| Contrato não aprovado ou desatualizado | Erro que cita `sintetica schema approve` ou `build` | 11 |
| Sem resposta do agente para o pedido atual | Estado `aguardando_agente`; imprime caminho do pedido e comando `submit` | 0 |
| Resposta lida, faltam registros, tentativas < 3 | Mostra os aceitos, os motivos de descarte e o novo pedido com `submit` | 0 |
| N registros válidos (Guiado) | Estado `em_revisao`; mostra a amostra e as 3 opções | 0 |
| N registros válidos (Expresso) | Aprova e grava a semente na mesma chamada | 0 |
| 3 tentativas com faltantes (Guiado) | `em_revisao` parcial; alerta e sugestão de voltar ao contrato | 0 |
| 3 tentativas com faltantes (Expresso) | `interrompida`; nada em `seeds/`; pede decisão | 0 |
| Amostra já aprovada | Mostra a amostra aprovada | 0 |
| Falha do provedor (indisponível, credencial, esgotado) | Mensagem do provedor; estado inalterado | 12 |
| Mascaramento indisponível | Nada gravado | 9 |
| Falha de escrita | Caminho e causa | 10 |

- 🟡 `--n` só vale ao iniciar uma rodada; com a rodada em andamento, é ignorado com aviso.
- 🟡 Versão nova do contrato descarta a rodada anterior com aviso e começa outra.

Saída com amostra em revisão:

```
Amostra do dataset <slug>: 3 de 3 registros válidos (provedor harness: <motivo>)
<tabela ou blocos JSON>
Opções:
  aprovar:   uv run sintetica sample approve <slug>
  ajustar:   uv run sintetica sample adjust <slug> '<pedido>'
  voltar ao contrato: edite schema.draft.json e rode uv run sintetica schema build <slug>
```

## 2. `sintetica sample adjust`

```
uv run sintetica sample adjust <slug> '<pedido>' [--project-dir <dir>]
```

Mascara o pedido, zera aceitos e tentativas, soma 1 rodada e executa `run`. Da 4ª rodada em diante, a saída inclui: "4 rodadas de ajuste sem aprovação. Considere voltar ao contrato." Códigos: os mesmos do `run`; pedido vazio → 2.

## 3. `sintetica sample approve`

| Situação | Resultado | Código de saída |
|----------|-----------|-----------------|
| Sem rodada, aguardando o agente ou já aprovada | Erro com o estado atual | 13 |
| Contrato desatualizado | Erro | 11 |
| 0 registros aceitos | Erro | 13 |
| Sucesso | Grava `seeds/sample.jsonl` e `seeds/sample.meta.json`; parcial gera alerta; indica a geração em lote como próximo passo | 0 |

## 4. `sintetica sample show`

Mostra o estado e a amostra atual. Sem rodada: código 13.

## 5. Códigos de saída do comando `sintetica`

| Código | Significado | Origem |
|--------|-------------|--------|
| 0 | Sucesso | todas |
| 2 | Dataset, intenção ou argumento inválido | 002 a 005 |
| 3, 4, 5 | Protocolo do harness | 002 |
| 6, 7 | Contrato de schema | 003 |
| 8 | Resposta inválida na entrevista | 004 |
| 9 | Mascaramento de PII indisponível | 004, 005 |
| 10 | Falha de escrita | 004, 005 |
| 11 | Contrato não aprovado ou desatualizado | 005 |
| 12 | Falha do provedor | 005 |
| 13 | Amostra não aprovável no estado atual | 005 |
