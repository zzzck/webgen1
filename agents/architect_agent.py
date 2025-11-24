import json
import re
from dataclasses import asdict
from core.agent_base import AgentBase
from core.schemas import Component, ComponentChild, PageSpec

ARCH_PROMPT = """

你是一名网页架构师，负责把 PRD 转化为清晰的页面骨架和组件树。

任务：
1) 依据 PRD 的模块/页面信息，确定整体布局（例：single-column / two-column / hero + content / dashboard）。
2) 给出 3-5 个主色调或配色（HEX 或语义色，如 primary、secondary、background）。
3) 生成组件树：每个组件需有唯一 id（建议 kebab/pinyin）、根 HTML 标签（div/section/header/footer/nav/main/aside 等），并为子元素提供 content_hint（描述应放置的文案/信息类型）。

输出规范：
- 禁止输出 HTML 或 Markdown，不要使用代码块或反引号。
- 允许使用清晰的中文分节文本或 JSON，字段需涵盖 layout、colors、components/children。
- 推荐分节示例（可直接使用）：
  布局：...
  配色：
  - ...
  组件：
  - component_id (html=section)：h1:标题；p:描述

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
