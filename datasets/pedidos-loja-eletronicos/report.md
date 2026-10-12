# Relatório de qualidade: pedidos-loja-eletronicos

**Veredito:** APROVADO
**Emitido em:** 2026-10-12T14:40:41Z
**Contrato:** ae61eedf7474dbc5e0bdaf79832c5dfc62d6875beb313de28c054bad24b08ef4
**Status do lote:** concluido
**Registros:** 100 lidos, 100 válidos, 100 pedidos

## Métricas

- Conformidade: 100,0% (meta ≥ 95%) [ok]
- Unicidade estrutural: 100,0% (meta ≥ 90%) [ok]
- Unicidade semântica: 100,0% (meta ≥ 90%) [ok]
- Vazamentos de PII: 0 (meta 0) [ok]
- Duração: 50,1 min (meta < 10 min: não atingida)

## Avisos

- nenhum

## Registros com problema

Índices a partir de 0 (posição do registro no dataset).

- Inválidos: nenhum
- Duplicados exatos: nenhum
- Quase-duplicados: nenhum
- Com PII: nenhum

## Escopo e limites da detecção de PII

Tipos cobertos: cpf, cnpj, email, phone, card, ipv4, ipv6.
Padrões extras da política: 0.
A métrica conta só o que esses detectores encontram (Q9). Limites conhecidos:

- Nomes de pessoas não são detectados.
- Endereços em texto livre não são detectados.
- CNPJ alfanumérico não é detectado; só o formato numérico.
- Telefone só é detectado com formatação ou prefixo +55; dígitos corridos não contam.
- Números de versão no formato a.b.c.d podem ser detectados como IPv4 (falso positivo aceito).
- Um CPF ou CNPJ falso válido pode coincidir com um documento real de outra pessoa.
