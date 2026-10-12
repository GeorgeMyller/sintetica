# User Stories: instalação

> Gerado pelo Redator do Reversa em 2026-10-12. 🟢 CONFORME CÓDIGO (`installer/`, `sdd/cli-installer.md`).

## US-01 — Instalar o sintetica no projeto
**Como** pessoa usuária de um harness de IA, **quero** rodar 1 comando na raiz do projeto **para** ter as skills e o runtime prontos.

```gherkin
Cenário: Instalação limpa
  Dado um projeto com .claude/ e Node.js 18 ou superior
  Quando rodo npx sintetica install
  Então as 5 skills existem em .agents/skills/ e .claude/skills/
  E .sintetica/ tem policy.json, state.json, install-manifest.json, bin/sintetica e o wheel
  E o resumo indica /sintetica-start como próximo passo

Cenário: Runtime ausente não bloqueia
  Dado uma máquina sem uv
  Quando rodo o instalador
  Então o código de saída é 0, state.json tem runtime_ready false
  E a saída mostra o comando de instalação do uv
```
🟢 Prioridade: Must.

## US-02 — Não perder meus arquivos
**Como** pessoa usuária, **quero** que o instalador nunca substitua um arquivo meu sem perguntar **para** não perder personalizações.

```gherkin
Cenário: Skill editada por mim
  Dado .claude/skills/sintetica-start/SKILL.md editado por mim
  Quando rodo o instalador e respondo não
  Então meu arquivo fica intacto e a skill é pulada com aviso

Cenário: Política preservada com --yes
  Dado um .sintetica/policy.json que eu editei
  Quando rodo o instalador com --yes
  Então a política continua com o meu conteúdo

Cenário: Falha no meio
  Dado um disco cheio durante a cópia
  Quando rodo o instalador
  Então nada desta execução fica no projeto e o código é 1
```
🟢 Prioridade: Must.

## US-03 — Reinstalar sem efeitos colaterais
**Como** pessoa usuária, **quero** rodar o instalador de novo ou atualizar a versão **para** manter as skills em dia.

```gherkin
Cenário: Segunda execução igual
  Dado uma instalação concluída
  Quando rodo o instalador de novo
  Então nenhum arquivo muda

Cenário: Versão nova
  Dado uma instalação da versão anterior
  Quando rodo o instalador da versão nova
  Então só os arquivos do manifest sem edição são substituídos
```
🟢 Prioridade: Should.
