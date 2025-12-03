"""Shared structured payloads for agent collaboration."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class PageSection:
    id: str
    purpose: str
    kpi: str | None = None  # 添加这一行 todo


@dataclass
class PRD:
    product: str
    goals: List[str]
    target_users: List[str]
    page_sections: List[PageSection]


@dataclass
class ComponentChild:
    tag: str
    content_hint: str


@dataclass
class Component:
    id: str
    html: str
    children: List[ComponentChild] = field(default_factory=list)


@dataclass
class PageSpec:
    layout: str
    colors: List[str]
    components: List[Component]


@dataclass
class TaskItem:
    id: str
    description: str
    depends_on: List[str] = field(default_factory=list)
    deliverable: str | None = None


@dataclass
class TaskPlan:
    summary: str
    prioritized_tasks: List[TaskItem]
