"""ReportGen Agent: generate final human-readable report."""

from __future__ import annotations

from agents.base_agent import AgentContext, BaseAgent


class ReportGenAgent(BaseAgent):
    """Compile previous agent outputs into a final report structure."""

    name = "ReportGen"

    def _process(self, ctx: AgentContext) -> None:  # noqa: D401
        risk_score = ctx.payload.get("risk_analysis", {}).get("score", 0)
        ctx.update(report={"summary": f"Risk score: {risk_score}"}) 