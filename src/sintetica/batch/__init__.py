"""batch-generator: geração do lote completo."""

from sintetica.batch.service import generate, status
from sintetica.batch.state import RunState, load_run_state

__all__ = ["RunState", "generate", "load_run_state", "status"]
