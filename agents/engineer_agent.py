import json
from dataclasses import asdict
from dataclasses import is_dataclass
from core.agent_base import AgentBase

# ENGINEER_PROMPT = """
# 你是一名前端工程师。
# 生成完整的 HTML5 + CSS，并且只输出纯粹的 HTML 代码，不要包含反引号或额外说明。
# """
ENGINEER_PROMPT = (
    "你是一名资深前端工程师，专注于为营销电商场景制作结构清晰、可读性强且视觉美观的网页。\n"
    "当用户给出页面需求时，请你：\n"
    "1. 生成一个完整的 HTML5 文档（包含 <!DOCTYPE html>、<html>、<head>、<style> 和 <body> 等结构）。\n"
    "2. 使用语义化标签和整洁的缩进，使代码易读、易维护。\n"
    "3. 在 <style> 中编写 CSS，保证布局合理、层次清晰、视觉美观，并兼顾基本的响应式表现。\n"
    "4. 命名 class 时保持规范、简洁且有意义，便于后续扩展和维护。\n"
    "5. 代码风格应统一、整洁，避免冗余样式和无用标签。\n"
    "6. 输出时只返回纯粹的 HTML 代码内容，不要添加任何解释、注释、Markdown 语法或反引号。\n"
    "除非用户明确要求 JavaScript，否则不要添加 <script>，重点放在 HTML 结构与 CSS 视觉效果上。"
)


class EngineerAgent(AgentBase):
    def __init__(self):
        super().__init__("Engineer", ENGINEER_PROMPT)

    def process(self, page_spec, context=None, **kwargs):
        page_payload = None
        if "page_spec" in kwargs and kwargs["page_spec"] is not None:
            ps = kwargs["page_spec"]
            if is_dataclass(ps):
                page_payload = asdict(ps)
            elif isinstance(ps, dict):
                page_payload = ps

        if is_dataclass(page_spec):
            plan_payload = asdict(page_spec)
        elif isinstance(page_spec, dict):
            plan_payload = page_spec
        else:
            plan_payload = {"brief": page_spec}

        payload = plan_payload
        if page_payload:
            payload = {"task_plan": plan_payload, "page_spec": page_payload}

        return self.run(json.dumps(payload, ensure_ascii=False), context=context)
