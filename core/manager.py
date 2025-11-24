from core.message_bus import MessageBus
from agents.pm_agent import PMAgent
from agents.architect_agent import ArchitectAgent
from agents.engineer_agent import EngineerAgent


class Manager:
    def __init__(self):
        self.bus = MessageBus()
        self.pm = PMAgent()
        self.arch = ArchitectAgent()
        self.eng = EngineerAgent()
        self.workflow = [
            {
                "input_topic": "brief",
                "output_topic": "prd",
                "agent": self.pm,
                "description": "Convert user brief into structured PRD",
            },
            {
                "input_topic": "prd",
                "output_topic": "page_spec",
                "agent": self.arch,
                "description": "Transform PRD into page architecture",
            },
            {
                "input_topic": "page_spec",
                "output_topic": "html",
                "agent": self.eng,
                "description": "Render final HTML",
            },
        ]

    def run(self, brief):
        self.bus.publish("brief", "User", brief)

        for step in self.workflow:
            incoming = self.bus.latest(step["input_topic"])
            content = incoming["content"] if incoming else None
            result = step["agent"].process(content)
            self.bus.publish(step["output_topic"], step["agent"].name, result)

        final = self.bus.latest("html")
        return final["content"] if final else ""
