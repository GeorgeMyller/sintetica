# Requirements: pii-guard (detecção e mascaramento local de PII)

> Identificador: `001-pii-guard`
> Data: `2026-10-09`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA
> Cenário: greenfield. As fontes são artefatos planejados (selo 🟡 PLANEJADO), não código legado. Por isso nenhum item recebe 🟢.

## 1. Resumo executivo

🟡 O `pii-guard` é o módulo local que encontra dados pessoais identificáveis (PII, *Personally Identifiable Information*) em texto e os troca por valores falsos do mesmo tipo.
🟡 Ele atende 5 componentes do sintetica: entrevista, amostra, provedor de LLM, gerador de lote e avaliador.
🟡 Ele resolve 2 problemas: PII real memorizada pelo LLM nos dados gerados, e PII real digitada pelo usuário na entrevista.
🟡 É a primeira feature do ciclo forward porque 4 componentes dependem dela.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/sdd/pii-guard.md#1. Resumo` | Detectores determinísticos de 7 tipos mais padrões configuráveis; troca por valores falsos | 🟡 |
| `_reversa_sdd/sdd/pii-guard.md#6. Requisitos Funcionais` | RF-01 a RF-11: CPF e CNPJ com dígito verificador, cartão com Luhn, allowlist por hash, nunca gravar valor original | 🟡 |
| `_reversa_sdd/sdd/pii-guard.md#11. Edge Cases e Tratamento de Erros` | EC-01 a EC-06: falsos positivos, regex inválida, falha do gerador falso, texto longo, allowlist ausente | 🟡 |
| `_reversa_sdd/prd.md#3. Métricas de sucesso` | Meta de 0 vazamentos de PII detectados; métrica cobre só o que os detectores cobrem | 🟡 |
| `_reversa_sdd/prd.md#6. Restrições` | Privacidade por design alinhada à LGPD (Lei Geral de Proteção de Dados); operação local | 🟡 |
| `_reversa_sdd/questions.md#Q9` | Lista fechada de detectores: CPF, CNPJ, e-mail, telefone, cartão, IPv4/IPv6 e lista de substituição | 🟡 |
| `_reversa_sdd/questions.md#Q21` | Mascaramento obrigatório antes de qualquer envio ao provedor externo | 🟡 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Componentes do sintetica (consumidor direto) | Verificar e mascarar texto antes de gravar ou enviar | 🟡 O provedor externo chama o mascaramento antes de cada pedido à API. |
| `dev-de-testes` | Massa de teste sem dado pessoal real | 🟡 Pede um campo de CPF e recebe CPFs falsos válidos, sem contar como vazamento. |
| `engenheiro-de-ml` | Dataset conversacional sem PII memorizada | 🟡 O avaliador encontra 0 vazamentos em 10.000 conversas. |
| `analista-de-dados` | Configurar um identificador interno como PII | 🟡 Adiciona o padrão de matrícula da empresa na política do projeto. |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** 🟡 A detecção usa apenas regras determinísticas e locais. Nenhum texto sai da máquina durante a detecção.
   - Origem: `_reversa_sdd/questions.md#Q9`, `_reversa_sdd/prd.md#6. Restrições`
   - Tipo: nova
2. **RN-02:** 🟡 Os tipos cobertos são exatamente 7: CPF, CNPJ, e-mail, telefone brasileiro, cartão de pagamento, IPv4 e IPv6. Padrões extras vêm da política do projeto.
   - Origem: `_reversa_sdd/questions.md#Q9`
   - Tipo: nova
3. **RN-03:** 🟡 CPF e CNPJ só contam como achado quando os dígitos verificadores são válidos. Cartão só conta quando passa no algoritmo de Luhn (soma de verificação de números de cartão).
   - Origem: `_reversa_sdd/sdd/pii-guard.md#15. Decisões Tomadas`
   - Tipo: nova
4. **RN-04:** 🟡 O valor original de um achado nunca é gravado em log, relatório ou arquivo.
   - Origem: `_reversa_sdd/sdd/pii-guard.md#6. Requisitos Funcionais` (RF-10)
   - Tipo: nova
5. **RN-05:** 🟡 Um achado conta como vazamento apenas quando o valor não foi inserido pelo próprio mascaramento. O módulo registra uma impressão irreversível (hash) de cada valor falso inserido; o achado cuja impressão está nesse registro não é vazamento.
   - Origem: `_reversa_sdd/sdd/pii-guard.md#14. Open Questions` (OQ-01), resolvida em `_reversa_sdd/questions.md#Q23`
   - Tipo: nova
6. **RN-06:** 🟡 Telefone só conta como achado quando tem formatação (parênteses no código de área, hífen ou espaço) ou prefixo `+55`. Sequências de dígitos corridos não são telefone.
   - Origem: `_reversa_sdd/questions.md#Q25` (clarify da feature 001)
   - Tipo: nova
7. **RN-07:** 🟡 Falha em qualquer etapa do módulo bloqueia a gravação e o envio do texto (falha segura).
   - Origem: `_reversa_sdd/sdd/pii-guard.md#11. Edge Cases e Tratamento de Erros`
   - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O sistema deve detectar CPF com ou sem pontuação e validar os 2 dígitos verificadores. | Must | `529.982.247-25` é detectado; `111.111.111-12` não é. | 🟡 |
| RF-02 | O sistema deve detectar CNPJ com ou sem pontuação e validar os dígitos verificadores. | Must | CNPJ válido é detectado; o mesmo com dígito verificador trocado não é. | 🟡 |
| RF-03 | O sistema deve detectar e-mail; telefone brasileiro com código de área (DDD) e 8 ou 9 dígitos, apenas quando formatado ou com prefixo `+55` (RN-06); cartão de 13 a 19 dígitos válido por Luhn; IPv4; IPv6. | Must | 1 caso positivo e 1 negativo por tipo passam. | 🟡 |
| RF-04 | O sistema deve carregar padrões extras da política do projeto e reportar esses achados com o tipo `custom`. | Must | Com o padrão `MAT-` seguido de 6 dígitos, o texto `MAT-123456` gera 1 achado `custom`. | 🟡 |
| RF-05 | O sistema deve oferecer a operação de verificação, que retorna tipo, posição inicial e posição final de cada achado. | Must | Texto com 1 e-mail retorna 1 achado `email` com as posições corretas. | 🟡 |
| RF-06 | O sistema deve oferecer a operação de mascaramento, que troca cada achado por um valor falso do mesmo tipo e formato, em português do Brasil. | Must | Após mascarar, a verificação não encontra vazamento. | 🟡 |
| RF-07 | O sistema deve registrar uma impressão irreversível (hash) de cada valor falso inserido, por dataset. | Must | Cada valor inserido tem sua impressão no registro do dataset. | 🟡 |
| RF-08 | O sistema deve classificar como vazamento apenas o achado cuja impressão não está no registro do RF-07. | Must | CPF inserido pelo mascaramento não conta como vazamento. Ver RN-05. | 🟡 |
| RF-09 | O sistema deve aceitar uma semente para que o mascaramento seja reproduzível. | Should | Mesma semente e mesmo texto produzem a mesma saída. | 🟡 |
| RF-10 | O sistema nunca deve gravar o valor original de um achado. Relatórios mostram só os 2 primeiros caracteres seguidos de `***`. | Must | A busca do valor original nos arquivos do dataset retorna 0 resultados. | 🟡 |
| RF-11 | O sistema deve informar a lista de tipos cobertos, os padrões extras ativos e os limites conhecidos. | Must | A consulta retorna os 7 tipos, os padrões extras e os limites de NG-02 da spec. | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | Processar 10.000 registros de 1 KB em ≤ 30 s numa máquina de desenvolvimento comum. | `_reversa_sdd/sdd/pii-guard.md#3. Goals` (G-03) | 🟡 |
| Precisão | Detectar 100% dos casos positivos e manter falsos positivos ≤ 5% nos casos negativos do conjunto de referência: 20 casos positivos e 20 negativos por tipo (7 tipos, 280 casos), versionados em `tests/fixtures/`. | `_reversa_sdd/sdd/pii-guard.md#3. Goals` (G-01, G-02), `_reversa_sdd/questions.md#Q24` | 🟡 |
| Segurança | 0 chamadas de rede durante detecção e mascaramento. | `_reversa_sdd/questions.md#Q15` | 🟡 |
| Privacidade | 0 valores originais de PII em disco. | RN-04 | 🟡 |
| Qualidade | Tipagem estrita e lint sem erros; cobertura de testes ≥ 80% no módulo e 100% nos detectores. | `_reversa_sdd/questions.md#Q19` | 🟡 |
| Plataforma | Runtime Python ≥ 3.10. | `_reversa_sdd/questions.md#Q18` | 🟡 |
| Observabilidade | Cada chamada informa a contagem de achados por tipo, sem valores. | `_reversa_sdd/sdd/pii-guard.md#12. Segurança e Privacidade` | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Mascarar CPF real digitado na entrevista
  Dado o texto "Meu CPF é 529.982.247-25"
  Quando o componente chama o mascaramento
  Então o texto devolvido contém outro CPF com dígitos verificadores válidos
  E a contagem informa 1 achado do tipo cpf
  E nenhum arquivo contém "529.982.247-25"

Cenário: Ignorar sequência numérica que não é CPF
  Dado o texto "Pedido 11111111112"
  Quando o componente chama a verificação
  Então a lista de achados está vazia

Cenário: Detectar cartão válido e ignorar número inválido por Luhn
  Dado o texto com "4111 1111 1111 1111" e "4111 1111 1111 1112"
  Quando o componente chama a verificação
  Então há 1 achado do tipo card

Cenário: Detectar CNPJ válido e ignorar CNPJ com dígito verificador errado
  Dado um CNPJ com dígitos verificadores válidos e o mesmo CNPJ com o último dígito trocado
  Quando o componente chama a verificação
  Então há 1 achado do tipo cnpj

Cenário: Ignorar dígitos corridos que parecem telefone
  Dado o texto "Chave 11912345678"
  Quando o componente chama a verificação
  Então a lista de achados está vazia

Cenário: Detectar e-mail, telefone e endereços IP
  Dado o texto "ana@exemplo.com, (11) 91234-5678, 192.168.0.1 e 2001:db8::1"
  Quando o componente chama a verificação
  Então há 1 achado de cada tipo: email, phone, ipv4 e ipv6
  E cada achado traz a posição inicial e final corretas

Cenário: Mascaramento reproduzível com semente
  Dado o mesmo texto com PII e a mesma semente
  Quando o componente chama o mascaramento 2 vezes
  Então as 2 saídas são idênticas

Cenário: Consultar escopo e limites da detecção
  Dado a política do projeto com 1 padrão extra
  Quando o avaliador consulta a cobertura do módulo
  Então a resposta lista os 7 tipos, 1 padrão extra e os limites conhecidos

Cenário: Padrão extra configurado pelo usuário
  Dado a política do projeto com o padrão de matrícula "MAT-" seguido de 6 dígitos
  Quando o componente verifica "MAT-123456"
  Então há 1 achado do tipo custom

Cenário: Valor falso inserido pelo mascaramento não conta como vazamento
  Dado um registro mascarado pelo módulo
  Quando o avaliador verifica o registro
  Então o número de vazamentos é 0

Cenário: Padrão extra inválido na política
  Dado a política do projeto com uma expressão regular que não compila
  Quando o módulo carrega a política
  Então o módulo recusa o carregamento com erro que cita a posição do padrão
  E nenhum texto é processado

Cenário: Registro de valores inseridos ausente
  Dado um dataset cujo registro de impressões foi apagado
  Quando o avaliador verifica o dataset
  Então todo achado conta como vazamento
  E o relatório informa a causa

Cenário: Falha ao gerar valor falso
  Dado um erro interno ao gerar o substituto de um achado
  Quando o componente chama o mascaramento
  Então o valor é trocado por "***" do mesmo tamanho
  E a falha é registrada sem o valor original
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01, RF-02, RF-03 | Must | Cobrem os 7 tipos definidos na Q9. |
| RF-04 | Must | A Q9 inclui lista configurável. |
| RF-05, RF-06 | Must | Operações usadas pelos 5 componentes consumidores. |
| RF-07, RF-08 | Must | Sem eles, campos de PII pedidos de propósito reprovam todo dataset. Dependem da RN-05. |
| RF-09 | Should | Reprodutibilidade ajuda testes; não bloqueia o MVP. |
| RF-10 | Must | Privacidade por design (Q15). |
| RF-11 | Must | O relatório final precisa documentar escopo e limites (Q9). |
| RNF de desempenho | Should | Afeta lotes de 10.000 registros; lotes de teste são pequenos. |
| RNF de precisão | Must | Sustenta a métrica de 0 vazamentos do PRD. |

## 9. Esclarecimentos

### Sessão 2026-10-09

> Respostas do revisor Antigravity em `_reversa_sdd/questions.md` (bloco "Etapa 6, /reversa-clarify da feature 001-pii-guard").

- **Q:** Como o avaliador evita contar como vazamento um valor falso inserido pelo mascaramento (RN-05, RF-08)?
  **R:** Registro de impressões (hash) de cada valor falso inserido. Só conta como vazamento o achado fora do registro.
- **Q:** Quem monta o conjunto de referência da precisão, e com quantos casos?
  **R:** O Claude gera durante o `/reversa-coding`: 20 casos positivos e 20 negativos por tipo (7 tipos, 280 casos), em `tests/fixtures/`. O Antigravity revisa.
- **Q:** Com que rigor detectar telefone (RF-03)?
  **R:** Só com formatação (parênteses no DDD, hífen ou espaço) ou com prefixo `+55`. Dígitos corridos não contam, para evitar falsos positivos com identificadores numéricos e chaves primárias.

## 10. Lacunas

- Nenhuma lacuna aberta. As 2 dúvidas iniciais e a lacuna de rigor do telefone foram resolvidas na sessão de 2026-10-09.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-10-09 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-10-09 | Esclarecimentos Q23 a Q25 integrados; RN-06 (telefone) adicionada e falha segura renumerada para RN-07; dúvidas zeradas | reversa-clarify |
