import json
from core.agent_base import AgentBase
from core.schemas import PRD, PageSection

PM_PROMPT = """
You are a Product Manager Agent responsible for workflow design.
Convert the brief into a structured PRD and stick to the JSON schema.
No prose, only JSON.

{
  "product": "string",
  "goals": ["string"],
  "target_users": ["string"],
  "page_sections": [
      { "id": "string", "purpose": "string" }
  ]
}
"""


class PMAgent(AgentBase):
    def __init__(self):
        super().__init__("PM", PM_PROMPT)

    def process(self, brief):
        output = self.run(brief)
        data = json.loads(output)
        sections = [PageSection(**section) for section in data.get("page_sections", [])]
        return PRD(
            product=data.get("product", ""),
            goals=data.get("goals", []),
            target_users=data.get("target_users", []),
            page_sections=sections,
        )
