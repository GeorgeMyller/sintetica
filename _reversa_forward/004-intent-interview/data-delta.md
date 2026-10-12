# Data Delta: intent-interview

> Identificador: `004-intent-interview`
> Data: `2026-10-12`
> Base: `_reversa_sdd/sdd/intent-interview.md#9. Modelo de Dados`. Não há modelo extraído de legado (greenfield).

## 1. `datasets/<slug>/intent.json`

```
Intent {
  slug: string
  mode: "guiado" | "expresso"
  started_at: string                       // ISO 8601 UTC com Z (Q20)
  objective: Item
  structure: Item
  rules: Item
  format: "csv" | "json" | "jsonl" | null  // null até a resposta (NOVO: anulável)
  format_source: "usuario" | "padrao" | null
  volume: int | null                       // 1 a 10.000; null até a resposta
  volume_source: "usuario" | "padrao" | null
  volume_rejections: int                   // NOVO: recusas seguidas de volume (D-09)
  pii_masked: boolean                      // true se algum texto foi mascarado
  confirmed_at: string | null              // NOVO: confirmação do resumo (D-11)
  ...                                      // chaves extras de outras features são preservadas (D-02)
}

Item {
  status: "pendente" | "definido" | "indefinido"   // NOVO: "pendente" (D-03)
  text: string | null                               // texto já mascarado; null se não definido
}
```

🟡 Diferenças em relação à spec:
- `pendente` em `Item.status`; `format` e `volume` (com as origens) anuláveis até a resposta.
- `volume_rejections` e `confirmed_at` novos.
- Chaves extras preservadas na regravação.

## 2. Estados derivados (não gravados)

| Estado | Regra |
|--------|-------|
| completa | `objective`, `structure` e `rules` diferentes de `pendente`, e `format` e `volume` preenchidos |
| crítica | `objective.status` e `structure.status` iguais a `indefinido` |
| precisa de confirmação | completa e `confirmed_at` nulo e (modo `guiado` ou crítica) |
| pronta para o schema | completa e não precisa de confirmação |

## 3. Compatibilidade com o `schema-builder` (feature 003)

O leitor `sintetica.schema.intent.load_intent` usa `slug`, `mode`, `format` e `structure.status`. Com a intenção completa, os 4 campos têm os valores que ele espera; `pendente` só ocorre com a intenção incompleta, quando o resumo ainda não indica o `schema build`.

## 4. Arquivos criados por `sintetica start`

| Caminho | Conteúdo |
|---------|----------|
| `datasets/<slug>/` | Pasta do dataset |
| `datasets/<slug>/seeds/` | Pasta vazia (princípio da pasta imediata) |
| `datasets/<slug>/intent.json` | Intenção inicial com os 3 itens `pendente` |
| `datasets/<slug>/.pii_allowlist` | Criado pelo `PiiGuard` só se algum texto for mascarado |

## 5. Migrações necessárias

Nenhuma. Arquivos novos.
