# Gerado por sintetica.schema; não edite.
# schema_version: 11c0d49071734d2674add843bea4308321f5371a2a01686e9792d2b9033fc61b

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

EstadoChoices = Literal[
    "SP",
    "RJ",
    "MG",
    "RS",
    "PR",
    "SC",
    "BA",
    "PE",
    "CE",
    "DF",
]


StatusContaChoices = Literal[
    "ativo",
    "inativo",
    "pendente",
]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_cliente: Annotated[
        str,
        Field(
            min_length=5,
            max_length=36,
            description="Identificador único do cliente (UUID ou código alfanumérico)",
        ),
    ]
    nome: Annotated[
        str,
        Field(
            min_length=3,
            max_length=80,
            description="Nome completo do cliente",
        ),
    ]
    email: Annotated[
        str,
        Field(
            pattern="^[^@]+@[^@]+\\.[^@]+$",
            description="Endereço de e-mail fictício do cliente",
        ),
    ]
    cidade: Annotated[
        str,
        Field(
            min_length=2,
            max_length=50,
            description="Cidade de residência do cliente",
        ),
    ]
    estado: Annotated[
        EstadoChoices,
        Field(
            description="Sigla da Unidade Federativa brasileira",
        ),
    ]
    status_conta: Annotated[
        StatusContaChoices,
        Field(
            description="Estado atual da conta do cliente",
        ),
    ]
    total_pedidos: Annotated[
        int,
        Field(
            ge=0,
            le=50,
            description="Número acumulado de compras realizadas",
        ),
    ]
    valor_gasto: Annotated[
        Decimal,
        Field(
            ge=Decimal("0"),
            le=Decimal("5000"),
            decimal_places=2,
            description="Valor total gasto em reais (BRL)",
        ),
    ]
