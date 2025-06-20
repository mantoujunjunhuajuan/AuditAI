"""Base agent abstraction for the AuditAI pipeline.

Each concrete Agent implements :meth:`_process` to transform the pipeline
payload. Agents should be stateless; any configuration is passed via __init__
params. The pipeline orchestrator is responsible for instantiating and calling
agents in sequence.
"""

from __future__ import annotations

import abc
import logging
from dataclasses import dataclass
from typing import Any, Dict

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:  # pylint: disable=too-many-instance-attributes
    """Shared context object passed between agents."""

    payload: Dict[str, Any]

    def update(self, **kwargs: Any) -> None:
        self.payload.update(kwargs)


class BaseAgent(abc.ABC):
    """Abstract pipeline agent."""

    name: str

    def __init__(self) -> None:  # noqa: D401
        if not hasattr(self, "name"):
            self.name = self.__class__.__name__

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, ctx: AgentContext) -> AgentContext:  # noqa: D401
        logger.info("➡️  [%s] started", self.name)
        try:
            self._process(ctx)
            logger.info("✅  [%s] completed", self.name)
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("❌  [%s] failed: %s", self.name, exc)
            raise
        return ctx

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def _process(self, ctx: AgentContext) -> None:  # noqa: D401
        """Implement agent logic, mutate *ctx* in-place.""" 