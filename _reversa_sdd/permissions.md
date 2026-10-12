# Permissões: sintetica

> Gerado pelo Detetive do Reversa em 2026-10-12.
> 🟢 O sintetica não tem RBAC, contas nem autenticação: é uma ferramenta local que roda com as permissões do usuário do sistema operacional. Este documento registra os atores, o que cada um pode fazer e as barreiras que o código impõe.

## 1. Atores

| Ator | Quem é | Como age |
|------|--------|----------|
| Usuário | Pessoa no harness (as 3 personas) | Responde a entrevista, aprova contrato e amostra, autoriza custo |
| Agente do harness | Assistente de IA que segue as skills | Roda os comandos do runtime, escreve o rascunho do contrato e responde aos pedidos (`submit`) |
| Runtime | `sintetica` (Python) | Valida, mascara, grava estado, chama provedores |
| Processo em background | `python -m sintetica.batch.worker` | Roda o lote acima de 100 registros, com a trava do dataset |
| Provedor externo | OpenAI, Anthropic, Gemini, Ollama | Recebe só pedidos mascarados |
| Instalador | `npx sintetica install` | Escreve skills, lançador, wheel e `.sintetica/` |

## 2. Matriz de ações

| Ação | Usuário | Agente | Runtime | Background | Provedor | Instalador |
|------|---------|--------|---------|------------|----------|------------|
| Responder a entrevista | ✅ | ✅ (registra) | valida e mascara | — | — | — |
| Escrever o rascunho do contrato | — | ✅ (só dados) | valida e gera código | — | — | — |
| Executar código do contrato | — | ❌ | ✅ (código gerado pelo próprio runtime) | ✅ | — | — |
| Aprovar contrato e amostra | ✅ (pelo agente) | executa o comando | grava | — | — | — |
| Autorizar custo acima do teto | ✅ (explícito) | só repassa o valor | bloqueia sem autorização (código 15) | respeita o saldo | — | — |
| Gerar registros | — | ✅ (harness, até 100) | — | — | ✅ (automático) | — |
| Ler dados pessoais originais | ✅ (os próprios) | ✅ (a resposta, antes do runtime) | só em memória | só em memória | ❌ (mascarado) | — |
| Gravar no dataset | — | só `submit` em `requests/` | ✅ | ✅ (com a trava) | — | — |
| Rodar 2 lotes no mesmo dataset | ❌ | ❌ | ❌ (trava, código 16) | ❌ | — | — |
| Ler chaves de API | ✅ (define no ambiente) | — | só no momento da chamada | idem | recebe no cabeçalho | ❌ |
| Substituir arquivo do usuário | ✅ (confirma) | `--yes` só com o usuário | — | — | — | só com confirmação |
| Substituir `.sintetica/policy.json` | ✅ (edita à mão) | — | — | — | — | ❌ (só se inválido, com `.bak`) |

## 3. Barreiras no código

| Barreira | Local | Efeito |
|----------|-------|--------|
| Código do contrato só do gerador | 🟢 `schema/codegen.py` | Texto do agente nunca vira código |
| Mascaramento obrigatório | 🟢 `providers/decorators/masking.py`, `intent/answers.py`, `sample/review.py`, `batch/review.py` | Política inválida bloqueia (códigos 9) |
| Teto de custo | 🟢 `providers/decorators/budget.py`, `batch/service.py:381-436` | Nenhum pedido acima do autorizado |
| Trava do lote | 🟢 `batch/lock.py` | 1 lote por dataset |
| Limite do harness | 🟢 `providers/harness/store.py:19-20` | ≤ 100 registros e ≤ 10 MiB por resposta |
| Confirmação do instalador | 🟢 `installer/src/prompt.js` | Sem terminal interativo, a resposta é não |
| Chaves fora do disco e das mensagens | 🟢 `providers/errors.py`, `external/provider.py` | Só o nome da variável aparece |

## 4. Permissões do sistema de arquivos

- 🟢 O runtime escreve só em `datasets/<slug>/` e lê `.sintetica/`; o instalador escreve em `.agents/skills/`, `.claude/skills/` e `.sintetica/`.
- 🟢 Sem permissão de escrita, o instalador desfaz e termina com 1 (`EACCES`); o runtime termina com 10 citando o caminho.
- 🟡 Não há controle de acesso entre usuários do mesmo sistema: quem lê a pasta do projeto lê os datasets.
