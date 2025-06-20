"""RiskAnalysis Agent: compute fraud risk score."""

from __future__ import annotations

from agents.base_agent import AgentContext, BaseAgent


class RiskAnalysisAgent(BaseAgent):
    """Analyse rule violations and other signals to produce a risk score."""

    name = "RiskAnalysis"

    def _process(self, ctx: AgentContext) -> None:  # noqa: D401
        # Very naive scoring for now.
        violations = ctx.payload.get("rule_check", {}).get("violations", [])
        score = 100 - len(violations) * 20
        ctx.update(risk_analysis={"score": max(score, 0)}) 