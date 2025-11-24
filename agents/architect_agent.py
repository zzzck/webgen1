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
        output = self.run(json.dumps(asdict(prd), ensure_ascii=False), json_mode=True)

        if not output or not output.strip():
            raise ValueError("Architect agent returned empty output; cannot build page spec")
        try:
            data = json.loads(output)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Architect agent response is not valid JSON: {output}") from exc
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
