"""As 5 perguntas da entrevista, sem jargão, com 1 exemplo por persona (D-13)."""

from __future__ import annotations

from dataclasses import dataclass

from sintetica.intent.model import Mode


@dataclass(frozen=True, slots=True)
class Question:
    item: str
    text: str
    examples: tuple[str, ...]


QUESTIONS: tuple[Question, ...] = (
    Question(
        "objective",
        "Para que você vai usar esses dados?",
        (
            "testar a tela de pedidos do meu sistema",
            "ensinar um modelo a classificar o sentimento de mensagens de suporte",
            "conferir se o painel de vendas soma os valores certos",
        ),
    ),
    Question(
        "structure",
        "O que cada registro deve ter? Liste as informações, colunas ou rótulos.",
        (
            "cliente, bebida, tamanho, valor e data do pedido",
            "conversa entre cliente e atendente, com o rótulo positivo, negativo ou neutro",
            "vendedor, região, mês e total vendido",
        ),
    ),
    Question(
        "rules",
        "Existe alguma regra que os dados precisam seguir?",
        (
            "o valor fica entre 5 e 50 reais",
            "cada conversa tem de 2 a 6 mensagens",
            "a região é Norte, Sul, Leste ou Oeste",
        ),
    ),
    Question(
        "format",
        "Em que formato você quer o arquivo: CSV, JSON ou JSONL?",
        ("JSON", "JSONL", "CSV"),
    ),
    Question(
        "volume",
        "Quantos registros você quer? (de 1 a 10.000)",
        ("50", "2.000", "300"),
    ),
)

_HINT = 'Se não souber alguma resposta, diga "não sei"; a entrevista continua.'


def render_questions(mode: Mode) -> list[str]:
    """Guiado: 1 pergunta por vez, na ordem. Expresso: as 5 num único bloco."""
    if mode == "expresso":
        lines = ["Responda tudo numa única mensagem:"]
        for n, q in enumerate(QUESTIONS, start=1):
            lines.append(f"{n}. {q.text} Ex.: {q.examples[0]}.")
        lines.append(_HINT)
        return lines
    lines = ["Faça 1 pergunta por vez, nesta ordem:"]
    for n, q in enumerate(QUESTIONS, start=1):
        lines.append(f"{n}. {q.text}")
        lines.extend(f"   - ex.: {example}" for example in q.examples)
    lines.append(_HINT)
    return lines
