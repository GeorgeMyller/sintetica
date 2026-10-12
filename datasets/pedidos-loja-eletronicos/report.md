# Relatório de qualidade: pedidos-loja-eletronicos

**Veredito:** REPROVADO
**Emitido em:** 2026-10-12T14:15:07Z
**Contrato:** ae61eedf7474dbc5e0bdaf79832c5dfc62d6875beb313de28c054bad24b08ef4
**Status do lote:** falha_provedor
**Registros:** 0 lidos, 0 válidos, 1000 pedidos

## Métricas

- Conformidade: 0,0% (meta ≥ 95%) [falhou]
- Unicidade estrutural: 0,0% (meta ≥ 90%) [falhou]
- Unicidade semântica: 0,0% (meta ≥ 90%) [falhou]
- Vazamentos de PII: 0 (meta 0) [ok]
- Duração: 24,6 min

## Avisos

- o lote terminou com status falha_provedor

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
