# Investigation: pii-guard

> Identificador: `001-pii-guard`
> Data: `2026-10-09`
> Fonte: `_reversa_forward/001-pii-guard/roadmap.md`

## 1. Pesquisa de fundo

### 1.1 Validação de documentos brasileiros
- 🟢 **CPF:** 11 dígitos. Os 2 últimos são dígitos verificadores calculados por módulo 11, com pesos 10..2 e 11..2. Sequências de dígitos repetidos (`000.000.000-00` a `999.999.999-99`) passam no cálculo, porém são inválidas por regra da Receita Federal e devem ser rejeitadas.
- 🟢 **CNPJ:** 14 dígitos. Os 2 últimos são verificadores por módulo 11, com pesos `5,4,3,2,9,8,7,6,5,4,3,2` e `6,5,4,3,2,9,8,7,6,5,4,3,2`. Sequências repetidas também são rejeitadas.
- 🟡 **CNPJ alfanumérico:** a Receita Federal anunciou CNPJ com letras a partir de julho de 2026. A feature cobre apenas o formato numérico; o alfanumérico fica como limite documentado em `coverage()` e candidato a feature futura.

### 1.2 Cartão de pagamento
- 🟢 **Luhn:** dobra-se cada segundo dígito a partir da direita; somas > 9 subtraem 9; o total deve ser múltiplo de 10. Comprimentos de 13 a 19 dígitos, com espaços ou hífens opcionais entre grupos.

### 1.3 Telefone brasileiro
- 🟢 DDDs válidos ficam entre 11 e 99, com lacunas (ex.: 20, 23, 25 não existem). A feature aceita qualquer DDD de 11 a 99, pois exige formatação (RN-06), o que já reduz falsos positivos.
- 🟢 Celular: 9 dígitos começando com 9. Fixo: 8 dígitos começando com 2 a 5.
- 🟡 Formatos aceitos: `(11) 91234-5678`, `(11) 1234-5678`, `11 91234-5678`, `11 91234 5678`, `+55 11 91234-5678`, `+5511912345678`.

### 1.4 E-mail e IP
- 🟡 **E-mail:** regex pragmática (`parte-local@domínio.tld`, TLD com 2 ou mais letras). Validação completa da RFC 5322 é desnecessária para detecção.
- 🟢 **IPv4 e IPv6:** candidatos extraídos por regex e confirmados com `ipaddress.ip_address()` da biblioteca padrão. Isso descarta octetos > 255 e formas IPv6 malformadas.

## 2. Alternativas avaliadas

| Alternativa | Prós | Contras | Veredito |
|-------------|------|---------|----------|
| Microsoft Presidio | Muitos reconhecedores prontos, NER | Dependência pesada (spaCy), modelos de ML, contraria NG-01 e RN-01 | Descartada |
| `scrubadub` | Leve | Foco em inglês; sem CPF/CNPJ | Descartada |
| `validate-docbr` | Valida CPF e CNPJ | Dependência para ~30 linhas de código puro | Descartada; implementação própria em `checksums.py` |
| Biblioteca `regex` com timeout | Protege contra retrocesso catastrófico | Dependência extra; só afeta padrões custom | Descartada para o MVP (D-11) |
| Detectores por regex + validação própria | Determinístico, sem dependência além do Faker, 100% testável | Manutenção própria | **Escolhida** |

## 3. Padrões aplicáveis

- 🟡 **Ports and Adapters:** `Detector`, `SubstituteGenerator` e `AllowlistStore` como `typing.Protocol`. Os testes usam dublês em memória.
- 🟡 **Fachada:** `PiiGuard` concentra a API para os 5 componentes consumidores.
- 🟡 **Falha segura:** toda exceção não tratada na detecção propaga para o chamador, que bloqueia a gravação e o envio (RN-07).
- 🟡 **Teste por tabela:** os 280 casos do conjunto de referência rodam com `pytest.mark.parametrize`.

## 4. Fontes externas

- Receita Federal: regras de CPF e CNPJ, incluindo o CNPJ alfanumérico.
- ISO/IEC 7812-1: algoritmo de Luhn.
- Anatel: plano de numeração e lista de códigos de área.
- Documentação Python: módulo `ipaddress`.
- Documentação Faker: provedores do locale `pt_BR` (`cpf`, `cnpj`, `email`, `phone_number`, `credit_card_number`, `ipv4`, `ipv6`).
