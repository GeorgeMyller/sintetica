# Relatório de qualidade: clientes-ecommerce

**Veredito:** APROVADO
**Emitido em:** 2026-10-12T11:06:49Z
**Contrato:** 11c0d49071734d2674add843bea4308321f5371a2a01686e9792d2b9033fc61b
**Status do lote:** concluido
**Registros:** 50 lidos, 50 válidos, 50 pedidos

## Métricas

- Conformidade: 100,0% (meta ≥ 95%) [ok]
- Unicidade estrutural: 100,0% (meta ≥ 90%) [ok]
- Unicidade semântica: 100,0% (meta ≥ 90%) [ok]
- Vazamentos de PII: 0 (meta 0) [ok]
- Duração: 1,7 min (meta < 10 min: atingida)

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
