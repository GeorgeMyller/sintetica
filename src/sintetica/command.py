"""Prefixo dos comandos citados nas mensagens do runtime (feature 008, D-13).

O lançador `.sintetica/bin/sintetica` define `SINTETICA_CMD` com o próprio caminho; assim, uma
mensagem como "Para retomar: ..." cita o comando que funciona no projeto do usuário. Sem a
variável, vale `uv run sintetica` (repositório de desenvolvimento).
"""

from __future__ import annotations

import os

CMD_ENV = "SINTETICA_CMD"
DEFAULT_CMD = "uv run sintetica"


def cli_command() -> str:
    return os.environ.get(CMD_ENV, "").strip() or DEFAULT_CMD
