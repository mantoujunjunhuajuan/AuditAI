"""AuditAI pipeline orchestrator.

Sequentially executes the configured agents. For MVP we wire all five agents
in fixed order.
"""

from __future__ import annotations

from typing import List

from agents.base_agent import AgentContext, BaseAgent
from agents.doc_intel import DocIntelAgent
from agents.info_extract import InfoExtractAgent
from agents.report_gen import ReportGenAgent
from agents.risk_analysis import RiskAnalysisAgent
from agents.rule_check import RuleCheckAgent


class Pipeline:
    """Orchestrate AuditAI agents in sequence."""

    def __init__(self, agents: List[BaseAgent] | None = None) -> None:  # noqa: D401
        self._agents: List[BaseAgent] = agents or [
            DocIntelAgent(),
            InfoExtractAgent(),
            RuleCheckAgent(),
            RiskAnalysisAgent(),
            ReportGenAgent(),
        ]

    def run(self, *, document_uris: List[str]) -> AgentContext:  # noqa: D401
        ctx = AgentContext(payload={"documents": document_uris})
        for agent in self._agents:
            ctx = agent.run(ctx)
        return ctx


if __name__ == "__main__":
    # Example usage
    pipeline = Pipeline()
    result_ctx = pipeline.run(document_uris=[
        "gs://auditai-claims-bucket/sample-1.pdf",
        "gs://auditai-claims-bucket/sample-2.pdf",
    ])
    from pprint import pprint

    pprint(result_ctx.payload) 