from core.message_bus import MessageBus
from agents.pm_agent import PMAgent
from agents.architect_agent import ArchitectAgent
from agents.engineer_agent import EngineerAgent
from agents.teamleader_agent import TeamLeaderAgent


class Manager:
    def __init__(self, cp: bool = True, sp: bool = True):
        """Central coordinator for the multi-agent workflow.

        Args:
            cp: Whether agents should share full conversation history (True)
                or operate in isolation with only their current input (False).
            sp: Whether to include the Architect agent step (True) or skip it
                and connect PM output directly to the Engineer (False).
        """

        self.cp = cp
        self.sp = sp
        self.bus = MessageBus()
        self.team_leader = TeamLeaderAgent()
        self.pm = PMAgent()
        self.arch = ArchitectAgent()
        self.eng = EngineerAgent()
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        available_roles = self._available_roles()
        role_responsibilities = self._role_responsibilities()

        steps = [
            {
                "input_topic": "brief",
                "output_topic": "tasks",
                "agent": self.team_leader,
                "description": "Plan work across team roles",
                "kwargs": {
                    "available_roles": available_roles,
                    "role_responsibilities": role_responsibilities,
                },
            }
        ]

        if self.sp:
            steps.append(
                {
                    "input_topic": "brief",
                    "output_topic": "prd",
                    "agent": self.pm,
                    "description": "Convert user brief into structured PRD",
                }
            )
            steps.append(
                {
                    "input_topic": "prd",
                    "output_topic": "page_spec",
                    "agent": self.arch,
                    "description": "Transform PRD into page architecture",
                }
            )
            engineer_input = "page_spec"
        else:
            engineer_input = "brief"
        steps.append(
            {
                "input_topic": engineer_input,
                "output_topic": "html",
                "agent": self.eng,
                "description": "Render final HTML",
            }
        )

        return steps

    def _available_roles(self):
        base_roles = ["TeamLeader", "Engineer"]
        if self.sp:
            base_roles.insert(1, "PM")
            base_roles.insert(2, "Architect")
        return base_roles

    def _role_responsibilities(self):
        responsibilities = {
            "TeamLeader": "梳理客户需求，拆解任务并分配到各角色",
            "PM": "将客户需求整理为结构化 PRD",
            "Architect": "基于 PRD 设计页面信息架构与组件方案",
            "Engineer": "根据规格实现最终的 HTML/CSS/JS 输出",
        }

        # 仅返回当前团队包含的角色职责
        return {role: responsibilities.get(role, "职责未提供") for role in self._available_roles()}

    def run(self, brief, cp: bool | None = None, sp: bool | None = None):
        cp_enabled = self.cp if cp is None else cp
        sp_enabled = self.sp if sp is None else sp

        if sp_enabled != self.sp:
            # Rebuild workflow when the sp override differs from initialization
            self.sp = sp_enabled
            self.workflow = self._build_workflow()

        self.bus.publish("brief", "User", brief)

        for step in self.workflow:
            incoming = self.bus.latest(step["input_topic"])
            content = incoming["content"] if incoming else None
            context = self.bus.chat_history() if cp_enabled else []
            kwargs = step.get("kwargs", {})
            result = step["agent"].process(content, context=context, **kwargs)
            self.bus.publish(step["output_topic"], step["agent"].name, result)

        final = self.bus.latest("html")
        return final["content"] if final else ""
