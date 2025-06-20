"""InfoExtract Agent: structured information extraction."""

from __future__ import annotations

from agents.base_agent import AgentContext, BaseAgent
from services.gemini_client import generate_content


class InfoExtractAgent(BaseAgent):
    """Extract key entities and fields from document text."""

    name = "InfoExtract"

    def _process(self, ctx: AgentContext) -> None:  # noqa: D401
        documents = ctx.payload.get("documents", [])
        prompt = (
            "You are an insurance claim assistant. Extract policy number, insured name,"
            " claim amount and date from the following documents: "
            f"{documents}. Return JSON."
        )
        try:
            content = generate_content(prompt=prompt)
            ctx.update(info_extract={"fields": content})
        except Exception as exc:  # noqa: BLE001
            ctx.update(info_extract={"error": str(exc)}) 