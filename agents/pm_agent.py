import json
import re
from core.agent_base import AgentBase
from core.schemas import PRD, PageSection

PM_PROMPT = """
你是一名产品经理，需要将需求简报转化为可执行的产品设计方案，覆盖功能规划、信息架构和页面布局。

请直接输出以下 JSON 结构，禁止输出 HTML、Markdown 或代码块：
{
  "product": "一句话产品概述",
  "goals": ["业务/产品目标1", "业务/产品目标2"],
  "target_users": ["主要用户角色及痛点1", "主要用户角色及痛点2"],
  "page_sections": [
    {"id": "module-id", "purpose": "该模块的目的、核心功能或要解决的问题"}
  ]
}

字段要求：
- product：产品定位或一句话概述。
- goals：3-7 个可验证的产品或业务目标，使用字符串数组。
- target_users：主要用户角色及核心痛点或动机，使用字符串数组。
- page_sections：页面/功能模块列表，id 需为英文/拼音/短链式单词，purpose 说明模块目的。
"""


class PMAgent(AgentBase):
    def __init__(self):
        super().__init__("PM", PM_PROMPT)

    def process(self, brief):
        output = self.run(brief, json_mode=False)

        if not output or not output.strip():
            raise ValueError("PM agent returned empty output; cannot build PRD")

        data = self._parse_output(output)
        sections = [PageSection(**section) for section in data.get("page_sections", [])]
        return PRD(
            product=data.get("product", ""),
            goals=data.get("goals", []),
            target_users=data.get("target_users", []),
            page_sections=sections,
        )

    def _parse_output(self, output: str):
        """Accept either JSON or structured Chinese text and normalize to PRD fields."""

        # Fast path: valid JSON
        try:
            data = json.loads(output)
            return {
                "product": data.get("product", ""),
                "goals": data.get("goals", []),
                "target_users": data.get("target_users", []),
                "page_sections": data.get("page_sections", []),
            }
        except json.JSONDecodeError:
            pass

        product = ""
        goals = []
        target_users = []
        page_sections = []
        current_section = None

        heading_patterns = {
            "product": re.compile(r"^(产品(名称)?|product)[:：]\s*(.+)$", re.IGNORECASE),
            "goals": re.compile(r"^(产品)?(目标|goals?)[:：]?$", re.IGNORECASE),
            "target_users": re.compile(r"^((目标)?用户|user(s)?)([:：]?)$", re.IGNORECASE),
            "page_sections": re.compile(r"^(页面|功能|模块)[/、 ]?(列表|规划|结构|sections)?[:：]?$", re.IGNORECASE),
        }

        for raw_line in output.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            product_match = heading_patterns["product"].match(line)
            if product_match:
                product = product_match.group(3).strip()
                current_section = None
                continue

            for section_key in ("goals", "target_users", "page_sections"):
                if heading_patterns[section_key].match(line):
                    current_section = section_key
                    continue

            # Collect items based on the active section
            if current_section:
                text = line
                if text[0] in {"-", "*", "•", "·"}:
                    text = text[1:].strip()

                if current_section == "goals" and text:
                    goals.append(text)
                elif current_section == "target_users" and text:
                    target_users.append(text)
                elif current_section == "page_sections" and text:
                    page_sections.append(self._parse_page_section(text, len(page_sections)))
                continue

            # Fallback: if no heading has been processed, treat the first non-empty line as product name
            if not product:
                product = line

        return {
            "product": product,
            "goals": goals,
            "target_users": target_users,
            "page_sections": page_sections,
        }

    def _parse_page_section(self, text: str, index: int):
        """Split a page/module line into id + purpose with lenient separators."""

        for sep in ("：", ":", "-", "—", "|", "->"):
            if sep in text:
                identifier, purpose = text.split(sep, 1)
                return {"id": identifier.strip() or f"section_{index+1}", "purpose": purpose.strip()}

        # No separator found; use the text as purpose with a generated id
        return {"id": f"section_{index+1}", "purpose": text}
