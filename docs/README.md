# Documentação Oficial do Sintetica

Bem-vindo à documentação técnica do **Sintetica**, framework para geração de dados sintéticos orientada por intenção conversacional.

---

## 📚 Guias por Módulo e Especificação

A documentação está dividida de acordo com os módulos que compõem o ciclo de vida da geração de dados:

| Módulo | Documento | Descrição |
|--------|-----------|-----------|
| **Instalador e Skills** | [cli-installer.md](cli-installer.md) | Como o pacote Node.js injeta as skills e configura o ambiente. |
| **Entrevista de Intenção** | [intent-interview.md](intent-interview.md) | Fluxos dos modos Guiado e Expresso, estrutura do `intent.json`. |
| **Construtor de Contratos** | [schema-builder.md](schema-builder.md) | Compilação dinâmica de schemas Pydantic v2 e regras de CSV/JSONL. |
| **Provedores de LLM** | [llm-provider.md](llm-provider.md) | Integração com APIs externas, Ollama e o protocolo de harness. |
| **Guarda de Privacidade** | [pii-guard.md](pii-guard.md) | Algoritmos de detecção, validação matemática e substituição segura de PII. |
| **Amostragem Prévia** | [sample-preview.md](sample-preview.md) | Geração de amostras iniciais (3 a 5 registros) para aprovação visual. |
| **Gerador em Lote** | [batch-generator.md](batch-generator.md) | Geração em lote assíncrona, controle de concorrência e processos em segundo plano. |
| **Avaliador de Qualidade** | [quality-evaluator.md](quality-evaluator.md) | Cálculo determinístico de métricas de conformidade, unicidade e relatório final. |

---

## 🏗️ Especificações de Engenharia Reversa (SDD)

Para especificações formais de arquitetura de software, diagramas de máquina de estado e matrizes de rastreabilidade geradas pelo Reversa, consulte:

- **Especificações de Módulos (v2.0):** [_reversa_sdd/sdd/](../_reversa_sdd/sdd/)
- **Documento de Arquitetura C4:** [_reversa_sdd/architecture.md](../_reversa_sdd/architecture.md)
- **Dicionário de Dados:** [_reversa_sdd/data-dictionary.md](../_reversa_sdd/data-dictionary.md)
- **Máquinas de Estado:** [_reversa_sdd/state-machines.md](../_reversa_sdd/state-machines.md)
- **Histórias de Usuário:** [_reversa_sdd/user-stories/](../_reversa_sdd/user-stories/)
- **Registros de Decisões de Arquitetura (ADRs):** [_reversa_sdd/adrs/](../_reversa_sdd/adrs/)

---

## 🛠️ Filosofia de Design e Princípios Técnicos

1. **Clean Code & Tipagem Estrita:** 100% tipado com `mypy --strict` e verificado via `ruff`.
2. **Zero Injeção de Código Não Sanitizado:** O compilador determinístico gera código isolado em Pydantic sem executar código vindo diretamente de modelos.
3. **Privacidade First (LGPD / GDPR):** Nenhum dado pessoal é gravado no disco sem passar pelo processo de sanitização e mascaramento.
4. **Resiliência e Recuperação:** Lotes interrompidos são retomados sem duplicação através da flag `--resume` e do arquivo canônico parcial.
