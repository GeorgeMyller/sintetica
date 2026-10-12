# Interface: `sintetica start` e `sintetica intent` (entrevista de intenção)

> Tipo: arquivo + CLI. Origem: RN-01 a RN-09, RF-01 a RF-17, D-05 a D-14. Confidência: 🟡.

## 1. `sintetica start`

```
uv run sintetica start [nome] [--mode guiado|expresso] [--project-dir <dir>]
```

| Situação | Resultado | Código de saída |
|----------|-----------|-----------------|
| Sucesso | Cria `datasets/<slug>/seeds/` e `intent.json`; imprime slug, modo e caminho absoluto | 0 |
| Falha ao criar a pasta ou gravar | Mensagem com o caminho e a causa; nenhuma pergunta | 10 |

Saída:

```
Dataset criado: <slug> (modo <modo>)
Pasta: <caminho absoluto>/datasets/<slug>
Início da medição: <started_at>
Próximo: uv run sintetica intent questions --mode <modo>
```

## 2. `sintetica intent questions`

```
uv run sintetica intent questions [--mode guiado|expresso]
```

Imprime as 5 perguntas sem jargão, com 1 exemplo por persona. No Expresso, em um único bloco numerado. Sempre código 0.

## 3. `sintetica intent set`

```
uv run sintetica intent set <slug> [--objective <texto>] [--structure <texto>] [--rules <texto>]
                                   [--format csv|json|jsonl] [--volume <n>]
                                   [--unknown objective|structure|rules|format|volume]...
                                   [--project-dir <dir>]
```

| Situação | Resultado | Código de saída |
|----------|-----------|-----------------|
| Nenhum item informado | Erro de uso | 2 |
| Dataset ou `intent.json` ausente | Erro que cita `sintetica start` | 2 |
| Mesmo item em `--<item>` e em `--unknown` | Erro de uso | 2 |
| Formato fora de CSV, JSON, JSONL | Erro com a lista dos 3 formatos; nada gravado | 8 |
| Volume fora de 1 a 10.000 (1ª ou 2ª recusa seguida) | Erro com o intervalo; só `volume_rejections` é gravado | 8 |
| Volume inválido na 3ª recusa seguida | Grava volume 10 (`padrao`) com aviso | 0 |
| Política de PII inválida ou allowlist sem gravação | Erro que cita a causa; nada gravado | 9 |
| Falha de escrita | Erro com o caminho e a causa | 10 |
| Sucesso | Grava os itens; imprime avisos (PII, padrões) e o resumo | 0 |

- 🟡 Itens válidos e inválidos na mesma chamada: nada é gravado além de `volume_rejections` (tudo ou nada).
- 🟡 O aviso de PII cita o item e os tipos (`e-mail`, `CPF`…), nunca o valor original.

## 4. `sintetica intent show`

Imprime o resumo. Dataset ou intenção ausente: código 2.

```
Intenção do dataset <slug> (modo <modo>)
Pasta: <caminho absoluto>
  objetivo:  definido  — "<texto até 80 caracteres>…"
  estrutura: indefinido
  regras:    pendente
  formato:   jsonl (padrão)
  volume:    10 (padrão)
<uma das linhas de estado abaixo>
```

| Estado | Linha final |
|--------|-------------|
| Incompleta | `Faltam: <itens>.` |
| Precisa de confirmação (Guiado) | `Confirme a intenção: uv run sintetica intent confirm <slug>` |
| Precisa de confirmação (Expresso crítico) | `Objetivo e estrutura indefinidos: o contrato terá 1 campo genérico. Confirme: uv run sintetica intent confirm <slug>` |
| Pronta | `Próximo passo: uv run sintetica schema build <slug>` |

## 5. `sintetica intent confirm`

| Situação | Resultado | Código de saída |
|----------|-----------|-----------------|
| Intenção incompleta | Erro com os itens que faltam | 8 |
| Sucesso | Grava `confirmed_at` e imprime o resumo com o próximo passo | 0 |

## 6. Códigos de saída do comando `sintetica`

| Código | Significado | Origem |
|--------|-------------|--------|
| 0 | Sucesso | todas |
| 2 | Dataset, intenção ou argumento inválido | 002, 003, 004 |
| 3, 4, 5 | Protocolo do harness | 002 |
| 6, 7 | Contrato de schema | 003 |
| 8 | Resposta inválida na entrevista | 004 |
| 9 | Mascaramento de PII indisponível | 004 |
| 10 | Falha de escrita | 004 |
