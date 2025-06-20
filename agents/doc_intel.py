"""DocIntel Agent: analyse raw documents and summarise metadata."""

from __future__ import annotations

from agents.base_agent import AgentContext, BaseAgent


class DocIntelAgent(BaseAgent):
    """Extract basic metadata from documents (page count, mime types, etc.)."""

    name = "DocIntel"

    def _process(self, ctx: AgentContext) -> None:  # noqa: D401
        # For now, just note that the step ran.
        docs = ctx.payload.get("documents", [])
        ctx.update(doc_intel={"documents_processed": len(docs)}) 