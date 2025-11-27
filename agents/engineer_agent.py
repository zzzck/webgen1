import json
from dataclasses import asdict
from dataclasses import is_dataclass
from core.agent_base import AgentBase

ENGINEER_PROMPT = """
你是一名前端工程师。
根据页面结构生成完整的 HTML5 + CSS，并且只输出纯粹的 HTML 代码，不要包含反引号或额外说明。
"""


class EngineerAgent(AgentBase):
    def __init__(self):
        super().__init__("Engineer", ENGINEER_PROMPT)

    def process(self, page_spec, context=None):
        if is_dataclass(page_spec):
            payload = asdict(page_spec)
        elif isinstance(page_spec, dict):
            payload = page_spec
        else:
            payload = {"brief": page_spec}

        return self.run(json.dumps(payload, ensure_ascii=False), context=context)
