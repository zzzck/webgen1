import json
from dataclasses import dataclass
from typing import List

from core.agent_base import AgentBase


@dataclass
class RoleTask:
    role: str
    tasks: List[str]


@dataclass
class TeamPlan:
    available_roles: List[str]
    tasks: List[RoleTask]
TEAMLEADER_PROMPT = """
你是一名电商营销项目的团队负责人（TeamLeader），负责统筹多智能体协作，使整个团队的工作对齐商业目标（如点击率、加购率、成交转化率）。

核心职责：
1. 理解客户提供的业务简报，提炼网页必须呈现的核心卖点与预期转化目标。
2. 列出电商网页制作链路中的关键交付物（如 PRD、页面结构定义、最终代码）。
3. 依据团队角色（TeamLeader / PM / Architect / Engineer）合理分配任务，保证工作连续性与协作规范。
4. 明确任务边界：如果某角色无需参与，也必须明确标注原因（例如：“Architect：无任务（SP 关闭）”）。

⚠ 必须严格按以下 JSON 格式输出：
{
  "available_roles": [
    "TeamLeader",
    "PM",
    "Architect",
    "Engineer"
  ],
  "deliverables": [
    "可量化的最终交付成果，例如：PRD 文档、页面结构规范、可运行 HTML/CSS/JS"
  ],
  "tasks": [
    {
      "role": "角色名称（必须来自 available_roles）",
      "tasks": [
        "任务 1（动词开头，描述输出物与目标）",
        "任务 2"
      ]
    }
  ]
}

字段说明（请严格遵守）：
- available_roles：字符串数组，按实际可用角色列出。
- deliverables：对最终交付成果进行列表清晰描述，用于检验项目成功标准。
- tasks：
  - 每一项都必须来自 available_roles
  - 任务需具体、可执行、结果导向（避免抽象词：如优化/支持/跟进）
  - 建议按顺序分配：TeamLeader → PM → Architect → Engineer

❌ 禁止输出以下内容：
- HTML / CSS / JavaScript
- Markdown 语法，如 ``` 或 #
- 顶部 / 底部额外解释文字
- JSON 结构以外的任何内容
"""

#
# TEAMLEADER_PROMPT = """
# 你是一名团队负责人（TeamLeader），负责统筹多智能体协作。
#
# 职责：
# 1. 接收客户需求，识别可交付成果。
# 2. 列出清晰的任务清单，并明确当前团队中每个角色要做的事情。
# 3. 如果某个角色无需工作，也要显式写明原因，例如“Engineer：无任务（SP 关闭，仅生成草稿）”。
#
# 输出格式（严格遵守 JSON，禁止输出反引号、Markdown 或额外说明）：
# {
#   "available_roles": ["TeamLeader", "Engineer", "PM"],
#   "tasks": [
#     {"role": "TeamLeader", "tasks": ["梳理需求", "划分交付物"]},
#     {"role": "Engineer", "tasks": ["根据规格输出 HTML 页面"]}
#   ]
# }
#
# - available_roles：按列表列出当前可用的角色名称。
# - tasks：数组，每个元素的 role 必须来自 available_roles，tasks 为该角色的待办列表。
# """
#

class TeamLeaderAgent(AgentBase):
    def __init__(self):
        super().__init__("TeamLeader", TEAMLEADER_PROMPT)

    def process(
        self,
        brief: str,
        available_roles: List[str],
        role_responsibilities: dict | None = None,
        context=None,
    ) -> TeamPlan:
        role_responsibilities = role_responsibilities or {}

        role_lines = []
        for role in available_roles:
            duty = role_responsibilities.get(role, "职责未提供，请自行补充")
            role_lines.append(f"- {role}: {duty}")

        user_prompt = (
            "客户需求如下：\n"
            f"{brief}\n\n"
            "当前团队的角色与职责（只使用这些）：\n"
            + "\n".join(role_lines)
            + "\n请按照要求给出 JSON 任务清单。"
        )

        raw_output = self.run(user_prompt, context=context, json_mode=False)

        if not raw_output or not raw_output.strip():
            raise ValueError("TeamLeader agent returned empty output; cannot plan tasks")

        return self._parse_output(raw_output, available_roles)

    def _parse_output(self, output: str, available_roles: List[str]) -> TeamPlan:
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            # Fallback：如果模型未返回合法 JSON，就构造一个最小可用的计划
            return TeamPlan(
                available_roles=available_roles,
                tasks=[
                    RoleTask(role=role, tasks=["未提供具体任务，手动补充"])
                    for role in available_roles
                ],
            )

        parsed_tasks = []
        for task in data.get("tasks", []):
            role = task.get("role", "")
            if not role:
                continue
            role_tasks = task.get("tasks", [])
            if isinstance(role_tasks, str):
                role_tasks = [role_tasks]
            parsed_tasks.append(RoleTask(role=role, tasks=list(role_tasks)))

        roles = data.get("available_roles", available_roles) or available_roles

        # 确保所有可用角色都在任务列表中
        missing_roles = [r for r in roles if r not in {t.role for t in parsed_tasks}]
        for role in missing_roles:
            parsed_tasks.append(RoleTask(role=role, tasks=["无任务或待确认"]))

        return TeamPlan(available_roles=roles, tasks=parsed_tasks)
