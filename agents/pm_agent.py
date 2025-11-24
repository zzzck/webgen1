import json
from core.agent_base import AgentBase
from core.schemas import PRD, PageSection

PM_PROMPT = """
你是一名负责产品需求分析的产品经理代理，需要将输入的需求简报转化为结构化的产品设计文档（PRD）。
严格按照下方 JSON 模型输出，禁止输出 HTML、Markdown 或任何额外说明文字，必须是有效的 JSON 字符串。

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
        output = self.run(brief, json_mode=True)

        if not output or not output.strip():
            raise ValueError("PM agent returned empty output; cannot build PRD")
        try:
            data = json.loads(output)
        except json.JSONDecodeError as exc:
            raise ValueError(f"PM agent response is not valid JSON: {output}") from exc
        sections = [PageSection(**section) for section in data.get("page_sections", [])]
        return PRD(
            product=data.get("product", ""),
            goals=data.get("goals", []),
            target_users=data.get("target_users", []),
            page_sections=sections,
        )
