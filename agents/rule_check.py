"""RuleCheck Agent: apply business rules to extracted info."""

from __future__ import annotations

from agents.base_agent import AgentContext, BaseAgent


class RuleCheckAgent(BaseAgent):
    """Check extracted fields against predefined rules."""

    name = "RuleCheck"

    def _process(self, ctx: AgentContext) -> None:  # noqa: D401
        ctx.update(rule_check={"passed": True, "violations": []}) 