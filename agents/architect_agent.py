import json
from dataclasses import asdict
from core.agent_base import AgentBase
from core.schemas import Component, ComponentChild, PageSpec

ARCH_PROMPT = """
You are a Web Architect Agent designing the workflow for UI generation.
Use the PRD to design a page structure. Return JSON only matching the schema:
{
  "layout": "string",
  "colors": ["string"],
  "components": [
    {
      "id": "string",
      "html": "string",
      "children": [
        { "tag": "string", "content_hint": "string" }
      ]
    }
  ]
}
"""


class ArchitectAgent(AgentBase):
    def __init__(self):
        super().__init__("Architect", ARCH_PROMPT)

    def process(self, prd):
        output = self.run(json.dumps(asdict(prd), ensure_ascii=False))
        data = json.loads(output)
        components = []
        for comp in data.get("components", []):
            children = [ComponentChild(**child) for child in comp.get("children", [])]
            components.append(
                Component(id=comp.get("id", ""), html=comp.get("html", ""), children=children)
            )
        return PageSpec(
            layout=data.get("layout", ""),
            colors=data.get("colors", []),
            components=components,
        )
