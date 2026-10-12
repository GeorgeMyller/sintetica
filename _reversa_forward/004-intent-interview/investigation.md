# Investigation: intent-interview

> Identificador: `004-intent-interview`
> Data: `2026-10-12`
> Fonte: `_reversa_forward/004-intent-interview/roadmap.md`

## 1. Pesquisa de fundo

### 1.1 Passagem de texto livre por argumento de linha de comando
- 🟢 `argparse` recebe cada argumento já separado pelo shell; aspas, acentos e quebras de linha chegam intactos se o shell citar o valor.
- 🟡 O risco está no lado do agente: aspas duplas internas e `$` sofrem expansão em `"..."`. Aspas simples evitam expansão; uma aspa simples dentro do texto vira `'\''`. A documentação da skill deve indicar esse padrão.
- 🟡 Alternativa avaliada: ler as respostas de um JSON na entrada padrão. Fica como evolução se R-02 se confirmar na prática.

### 1.2 Slug ASCII
- 🟢 `unicodedata.normalize("NFKD", texto).encode("ascii", "ignore")` remove acentos (`Café` → `Cafe`).
- 🟢 `Path.mkdir(exist_ok=False)` levanta `FileExistsError` de forma atômica, útil para resolver colisão sem corrida.

### 1.3 Mascaramento
- 🟢 `PiiGuard.mask` grava os hashes dos valores falsos em `datasets/<slug>/.pii_allowlist` (adendo 001). A entrevista é o 1º componente a gravar nessa allowlist; a geração e a avaliação vão reconhecer esses valores como falsos.
- 🟢 `MaskResult.counts` informa os tipos encontrados sem expor o valor original, o que basta para o aviso ao usuário.

### 1.4 Horário UTC
- 🟢 `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")` gera o ISO 8601 com `Z` já usado nas features 002 e 003.

## 2. Alternativas avaliadas

| Alternativa | Prós | Contras | Veredito |
|-------------|------|---------|----------|
| A skill grava `intent.json` direto, sem comandos | Menos código Python | Sem mascaramento garantido, sem validação, sem início de medição confiável | Descartada |
| Entrevista interativa no terminal (`input()`) | Autônoma | O harness conversa pelo chat, não por terminal interativo | Descartada |
| Comandos por item (`start`, `set`, `show`, `confirm`) chamados pelo agente | Mesmo padrão da Q29; cada passo testável | Agente precisa citar textos no shell | **Escolhida** |
| Orquestrador `sintetica run` | Encadeia tudo | Depende de etapas não implementadas (Q40) | Descartada nesta feature |

## 3. Padrões aplicáveis

- 🟡 **Agente orquestra, runtime valida** (Q29, D-03 da feature 003).
- 🟡 **Falha segura** (adendo 001): nenhuma gravação sem mascaramento.
- 🟡 **Escrita atômica** para todo arquivo de estado.

## 4. Fontes externas

- Documentação Python: `argparse`, `unicodedata`, `pathlib`, `datetime`.
- Manual do Bash: regras de citação com aspas simples.
