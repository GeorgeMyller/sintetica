# Interface: `sintetica eval` (avaliação de qualidade)

> Tipo: arquivo + CLI. Origem: RN-01 a RN-11, RF-01 a RF-15, D-02 a D-18. Confidência: 🟡.

## 1. `sintetica eval`

```
uv run sintetica eval <slug> [--project-dir <dir>]
```

| Situação | Resultado | Código de saída |
|----------|-----------|-----------------|
| Dataset ou intenção ausente | Erro | 2 |
| Contrato ausente ou ilegível | Erro que cita `sintetica schema build` | 11 |
| Lote em andamento (trava ocupada) | Erro com o comando `sintetica status` | 16 |
| `output/dataset.<ext>` ausente | Erro que cita `sintetica generate` e `--resume` | 18 |
| Mascaramento de PII indisponível | Nenhum relatório gravado | 9 |
| Falha ao gravar o relatório | Caminho e causa | 10 |
| Veredito `APROVADO` | Bloco curto e caminho de `report.md` | 0 |
| Veredito `REPROVADO` | Bloco curto com as métricas que falharam | 17 |

Saída:

```
Avaliação do dataset <slug>: REPROVADO (falharam: conformidade)
  Conformidade: 94,0% (meta ≥ 95%)
  Unicidade estrutural: 100,0% (meta ≥ 90%)
  Unicidade semântica: 98,9% (meta ≥ 90%)
  Vazamentos de PII: 0 (meta 0)
  Duração: 7,4 min (meta < 10 min: atingida)
Aviso: o lote terminou com status incompleto.
Relatório: /caminho/absoluto/datasets/<slug>/report.md
```

## 2. Mudanças em `sintetica generate`

- 🟡 Em todo status final, depois de gerar `output/dataset.<ext>`, o lote roda a avaliação e acrescenta o mesmo bloco à saída (e ao `worker.log` no background).
- 🟡 O código de saída do `generate` continua o do lote (0, ou 12 em `falha_provedor`).
- 🟡 Erro na avaliação vira aviso: "avaliação não concluída: <causa>; rode uv run sintetica eval <slug>".
- 🟡 A linha "Próximo passo: avaliação de qualidade (feature quality-evaluator)." sai.

## 3. Mudanças em `sintetica status`

- 🟡 Com `report.json`, 1 linha a mais: "Avaliação: <veredito> (<caminho de report.md>)".

## 4. Idempotência

- 🟡 A avaliação nunca altera o dataset, a intenção nem `run.json`.
- 🟡 Rodar 2 vezes gera o mesmo `report.json`, exceto `finished_at`, `duration_min` e `time_target_met`.

## 5. Códigos de saída do comando `sintetica`

| Código | Significado | Origem |
|--------|-------------|--------|
| 0 | Sucesso (no `eval`: `APROVADO`) | todas |
| 2 | Dataset, intenção ou argumento inválido | 002 a 007 |
| 3, 4, 5 | Protocolo do harness | 002 |
| 6, 7 | Contrato de schema | 003 |
| 8 | Resposta inválida na entrevista | 004 |
| 9 | Mascaramento de PII indisponível | 004 a 007 |
| 10 | Falha de escrita | 004 a 007 |
| 11 | Contrato não aprovado, desatualizado ou ilegível | 005 a 007 |
| 12 | Falha do provedor | 005, 006 |
| 13 | Amostra não aprovável no estado atual | 005 |
| 14 | Amostra ausente ou de outra versão do contrato | 006 |
| 15 | Custo exige autorização | 006 |
| 16 | Lote em andamento, interrompido ou já existente | 006, 007 |
| 17 | Dataset `REPROVADO` | 007 |
| 18 | Dataset final ausente | 007 |
