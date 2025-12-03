import json
from dataclasses import asdict, is_dataclass

from core.agent_base import AgentBase
from core.schemas import TaskItem, TaskPlan


PROJECT_PROMPT = """
You are the Project role in a multi-agent web delivery team.

Mission
- Break down tasks according to the PRD and the architect's technical design.
- Produce a task list that is execution-ready for engineering.
- Analyze task dependencies to ensure work starts with prerequisite modules.

Output strictly in JSON (no Markdown, code fences, or extra text):
{
  "summary": "One sentence on how the PRD will be implemented",
  "prioritized_tasks": [
    {
      "id": "kebab-or-snake-id",
      "description": "Concrete, testable task derived from PRD/design",
      "depends_on": ["task-id-a", "task-id-b"],
      "deliverable": "What must be produced (UI block, logic, data structure, etc.)"
    }
  ]
}

Rules
- Respect dependency order: prerequisites first, then dependent UI/logic modules.
- Keep tasks granular so they can be completed independently when dependencies are met.
- Do not invent new features beyond the PRD/technical design.
"""


class ProjectAgent(AgentBase):
    def __init__(self):
        super().__init__("Project", PROJECT_PROMPT)

    def process(self, page_spec, context=None, prd=None):
        payload = {
            "prd": asdict(prd) if prd is not None and is_dataclass(prd) else prd,
            "page_spec": asdict(page_spec) if is_dataclass(page_spec) else page_spec,
        }

        output = self.run(json.dumps(payload, ensure_ascii=False), context=context)

        if not output or not output.strip():
            raise ValueError("Project agent returned empty output; cannot build task plan")

        data = self._parse_output(output)
        tasks = []
        for idx, task in enumerate(data.get("prioritized_tasks", [])):
            depends_on = task.get("depends_on", [])
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            tasks.append(
                TaskItem(
                    id=task.get("id", f"task-{idx+1}"),
                    description=task.get("description", ""),
                    depends_on=list(depends_on),
                    deliverable=task.get("deliverable"),
                )
            )

        summary = data.get("summary", "")
        if not tasks:
            tasks.append(
                TaskItem(
                    id="task-1",
                    description="Review PRD and architecture to prepare implementation backlog",
                    depends_on=[],
                    deliverable="Ordered task backlog",
                )
            )

        return TaskPlan(summary=summary, prioritized_tasks=tasks)

    def _parse_output(self, output: str):
        try:
            data = json.loads(output)
            return {
                "summary": data.get("summary", ""),
                "prioritized_tasks": data.get("prioritized_tasks", []),
            }
        except json.JSONDecodeError:
            pass

        summary = ""
        tasks = []
        current_section = None
        for raw_line in output.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if line.lower().startswith("summary") or line.startswith("总结"):
                current_section = "summary"
                continue
            if "task" in line.lower() or "任务" in line:
                current_section = "tasks"
                continue

            if current_section == "summary" and not summary:
                summary = line
                continue
            if current_section == "tasks":
                parts = [chunk.strip() for chunk in line.split("-", 1)]
                description = parts[-1] if parts else line
                tasks.append(
                    {
                        "id": f"task-{len(tasks)+1}",
                        "description": description,
                        "depends_on": [],
                        "deliverable": None,
                    }
                )

        return {"summary": summary, "prioritized_tasks": tasks}
