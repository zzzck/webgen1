import json
import re
from dataclasses import asdict
from core.agent_base import AgentBase
from core.schemas import Component, ComponentChild, PageSpec

ARCH_PROMPT = """

你是一名网页架构师，负责把 PRD 转化为清晰的页面骨架和组件树。

请直接输出以下 JSON 结构，禁止输出 HTML、Markdown 或代码块：
{
  "layout": "single-column | two-column | hero + content | dashboard | ...",
  "colors": ["primary", "secondary", "#F4F4F5"],
  "components": [
    {
      "id": "component-id",
      "html": "section | header | nav | main | aside | footer | div",
      "children": [
        {"tag": "h1", "content_hint": "标题或主旨"},
        {"tag": "p", "content_hint": "补充描述或文案"}
      ]
    }
  ]
}

字段要求：
- layout：依据 PRD 选择的整体布局名称。
- colors：3-5 个主色调或配色（可用 HEX 或语义色）。
- components：组件树，id 需唯一（建议 kebab/pinyin），html 为根标签，children 中包含 tag 与 content_hint。

"""


class ArchitectAgent(AgentBase):
    def __init__(self):
        super().__init__("Architect", ARCH_PROMPT)

    def process(self, prd):
        output = self.run(json.dumps(asdict(prd), ensure_ascii=False), json_mode=False)

        if not output or not output.strip():
            raise ValueError("Architect agent returned empty output; cannot build page spec")

        data = self._parse_output(output)
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

    def _parse_output(self, output: str):
        """Accept either JSON or structured Chinese text and normalize to PageSpec fields."""

        try:
            data = json.loads(output)
            return {
                "layout": data.get("layout", ""),
                "colors": data.get("colors", []),
                "components": data.get("components", []),
            }
        except json.JSONDecodeError:
            pass

        layout = ""
        colors = []
        components = []
        current_section = None

        heading_patterns = {
            "layout": re.compile(r"^(布局|layout)[:：]?(\s+)?(.+)?$", re.IGNORECASE),
            "colors": re.compile(r"^(配色|颜色|colors?)[:：]?$", re.IGNORECASE),
            "components": re.compile(r"^(组件|component[s]?|组件树)[:：]?$", re.IGNORECASE),
        }

        for raw_line in output.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            layout_match = heading_patterns["layout"].match(line)
            if layout_match:
                maybe_layout = layout_match.group(3)
                if maybe_layout:
                    layout = maybe_layout.strip()
                current_section = None
                continue

            for section_key in ("colors", "components"):
                if heading_patterns[section_key].match(line):
                    current_section = section_key
                    continue

            if current_section == "colors":
                color_text = line
                if color_text[0] in {"-", "*", "•", "·"}:
                    color_text = color_text[1:].strip()
                colors.extend([c.strip() for c in re.split(r"[,，、]|\s+", color_text) if c.strip()])
                continue

            if current_section == "components":
                components.append(self._parse_component_line(line, len(components)))
                continue

            if not layout:
                layout = line

        return {
            "layout": layout,
            "colors": colors,
            "components": components,
        }

    def _parse_component_line(self, text: str, index: int):
        """Parse a single component description into id/html/children."""

        match = re.match(r"^(?P<id>[\w-]+)\s*(?:\((?P<html>[^)]+)\))?[:：]?\s*(?P<rest>.*)$", text)
        if match:
            comp_id = match.group("id") or f"component_{index+1}"
            html_tag = (match.group("html") or "div").strip()
            remainder = match.group("rest").strip()
        else:
            comp_id = f"component_{index+1}"
            html_tag = "div"
            remainder = text.strip()

        children = []
        for chunk in re.split(r"[;；|、]", remainder):
            part = chunk.strip()
            if not part:
                continue
            part = re.sub(r"^(子项|child(ren)?|内容|元素)[:：]\s*", "", part, flags=re.IGNORECASE)
            for sep in ("：", ":", "=", "-", "—", "->"):
                if sep in part:
                    tag, hint = part.split(sep, 1)
                    children.append({"tag": tag.strip() or "div", "content_hint": hint.strip()})
                    break
            else:
                children.append({"tag": "div", "content_hint": part})

        return {"id": comp_id, "html": html_tag, "children": children}
