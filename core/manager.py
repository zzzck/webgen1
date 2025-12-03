from core.message_bus import MessageBus
from agents.pm_agent import PMAgent
from agents.architect_agent import ArchitectAgent
from agents.engineer_agent import EngineerAgent
from agents.teamleader_agent import TeamLeaderAgent

# Multi-Agent 协作管理器：负责调度、消息流转与工作流组织
class Manager:
    def __init__(self, cp: bool = True, sp: bool = True):
        """多智能体电商网页制作流程的中央协调者

        Args:
            cp: 是否启用共享上下文（Communication Protocol）
                True：所有 Agent 共享完整对话历史
                False：仅按当前任务输入，不共享对话
            sp: 是否启用完整工作流（Structure Procedure）
                True：包括 TeamLeader → PM → Architect → Engineer
                False：跳过 PM & Architect，由 Engineer 直接开发
        """

        self.cp = cp
        self.sp = sp
        self.bus = MessageBus()

        # 初始化四个角色 Agent（团队角色固定，不新增）
        self.team_leader = TeamLeaderAgent()  # TeamLeader：营销统筹
        self.pm = PMAgent()  # PM：结构化 PRD 输出
        self.arch = ArchitectAgent()  # Architect：营销组件架构设计
        self.eng = EngineerAgent()  # Engineer：前端开发交付页面

        # 构建执行工作流
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        """构建按当前配置生成的角色执行链（Workflow）"""

        available_roles = self._available_roles()
        role_responsibilities = self._role_responsibilities()

        # 1️⃣ TeamLeader 步骤：任务拆解+分配
        steps = [
            {
                "input_topic": "brief",      # 输入：客户需求简述
                "output_topic": "tasks",     # 输出：角色任务分配
                "agent": self.team_leader,
                "description": "Plan work across team roles",
                "kwargs": {
                    "available_roles": available_roles,
                    "role_responsibilities": role_responsibilities,
                },
            }
        ]

        # 是否需要完整工作流程（PM + Architect）
        if self.sp:
            # 2️⃣ PM 步骤：客户需求 → PRD
            steps.append(
                {
                    "input_topic": "brief",
                    "output_topic": "prd",
                    "agent": self.pm,
                    "description": "Convert user brief into structured PRD",
                }
            )

            # 3️⃣ Architect 步骤：PRD → 页面结构规范
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
            # 跳过 PM & Architect 时，Engineer 直接基于 brief 来编码
            engineer_input = "brief"

        # 4️⃣ Engineer 步骤：最终生成 HTML
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
        """返回当前团队所包含的角色顺序（用于任务规划显示）。"""
        base_roles = ["TeamLeader", "Engineer"]
        if self.sp:
            # 插入 PM 和 Architect
            base_roles.insert(1, "PM")
            base_roles.insert(2, "Architect")
        return base_roles

    def _role_responsibilities(self):
        """返回营销电商网页制作团队中各角色职责定义（已做专业优化）"""

        responsibilities = {
            "TeamLeader": {
                "role": "电商营销项目负责人",
                "mission": "理解客户产品卖点与商业目标，统筹营销网页制作全流程",
                "actions": [
                    "挖掘客户营销目标（如提升转化率、拉新等）",
                    "明确核心卖点与人群洞察",
                    "将营销目标拆解为电商网页任务",
                    "分配任务至 PM、Architect、Engineer 并严格把控交付质量"
                ]
            },
            "PM": {
                "role": "营销产品经理",
                "mission": "将营销需求转化为电商网页 PRD，确保产品内容有效促进销售",
                "actions": [
                    "拆解营销策略：主视觉、利益点、促销点、信任状展示",
                    "设计购买路径与决策转化流程（如加入购物车→结算）",
                    "输出包含信息结构与交互要求的 PRD 文档"
                ]
            },
            "Architect": {
                "role": "前端架构设计师",
                "mission": "基于营销目标，设计销售展示页面的信息架构与组件体系",
                "actions": [
                    "规划页面结构（首屏卖点/规格/价格/评价/库存/倒计时等）",
                    "定义可复用的营销组件（如价格组件、优惠组件、购买按钮等）",
                    "制定行为逻辑：库存提醒、倒计时、优惠触发机制",
                    "输出 UI 区块与交互接口说明供工程研发"
                ]
            },
            "Engineer": {
                "role": "前端工程师",
                "mission": "将营销页面落地为高性能、高转化可运行代码",
                "actions": [
                    "实现响应式电商页面（HTML/CSS/JS）",
                    "实现营销关键功能（购物车、库存动态、倒计时、弹窗等）",
                    "保证高加载速度与稳定交互，优化用户转化体验",
                    "交付可上线的销售页面并完成必要测试"
                ]
            }
        }

        # 返回当前团队成员的职责（确保无新增角色）
        return {role: responsibilities.get(role, "职责未提供") for role in self._available_roles()}

    def run(self, brief, cp: bool | None = None, sp: bool | None = None):
        """执行整个网页开发流程

        Args:
            brief: 客户业务需求描述（如“新疆瓜子电商销售页面”）
            cp: 临时覆盖共享上下文设置
            sp: 临时覆盖工作流结构设置
        """

        cp_enabled = self.cp if cp is None else cp
        sp_enabled = self.sp if sp is None else sp

        # 若执行时变更了 sp 策略，则重建工作流
        if sp_enabled != self.sp:
            self.sp = sp_enabled
            self.workflow = self._build_workflow()

        # 初始化输入消息：用户需求
        self.bus.publish("brief", "User", brief)

        # 顺序执行 workflow
        for step in self.workflow:
            incoming = self.bus.latest(step["input_topic"])
            content = incoming["content"] if incoming else None

            # cpEnabled=True 时，所有历史消息共享给 Agent #todo

            context = self.bus.chat_history() if cp_enabled else []

            # # response_format={"type":"json_object"} if json_mode else None,
            # messages = [{"role": "system", "content": [{"type": "text", "text": content}]}]
            # resp = self.client.chat.completions.create(model=self.model, messages=messages)
            resp = " "

            kwargs = step.get("kwargs", {})
            result = step["agent"].process(content, context=context, **kwargs)

            # 每个节点发布输出，供下游 Agent 使用
            self.bus.publish(step["output_topic"], step["agent"].name, result)

        # 返回最终 HTML 页面输出
        final = self.bus.latest("html")
        return final["content"] , resp if final else ""
