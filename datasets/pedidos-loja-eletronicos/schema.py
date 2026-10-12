# Gerado por sintetica.schema; não edite.
# schema_version: ae61eedf7474dbc5e0bdaf79832c5dfc62d6875beb313de28c054bad24b08ef4

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

TipoPedidoChoices = Literal[
    "compra",
    "troca",
    "devolução",
    "garantia",
    "cancelamento",
]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")

    texto_pedido: Annotated[
        str,
        Field(
            min_length=20,
            max_length=600,
            description="Texto do pedido escrito pelo cliente de uma loja de eletrônicos, em português",  # noqa: E501
        ),
    ]
    tipo_pedido: Annotated[
        TipoPedidoChoices,
        Field(
            description="Rótulo do tipo de pedido",
        ),
    ]
    nome_cliente: Annotated[
        str,
        Field(
            min_length=3,
            max_length=80,
            description="Nome completo fictício do cliente",
        ),
    ]
    email: Annotated[
        str,
        Field(
            max_length=120,
            pattern="^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$",
            description="Endereço de e-mail fictício do cliente",
        ),
    ]
    telefone: Annotated[
        str,
        Field(
            pattern="^\\(\\d{2}\\) 9?\\d{4}-\\d{4}$",
            description="Telefone fictício do cliente no formato brasileiro, ex.: (11) 91234-5678",
        ),
    ]
    mensagens_cliente: Annotated[
        str,
        Field(
            min_length=10,
            max_length=1200,
            description="Mensagens adicionais do cliente sobre o pedido, de 1 a 4 mensagens separadas por ' | '",  # noqa: E501
        ),
    ]
