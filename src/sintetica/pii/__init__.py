"""pii-guard: detecção e mascaramento local de PII."""

from sintetica.pii.domain import Coverage, MaskResult, PiiFinding, PiiType, PolicyError
from sintetica.pii.guard import PiiGuard

__all__ = ["Coverage", "MaskResult", "PiiFinding", "PiiGuard", "PiiType", "PolicyError"]
