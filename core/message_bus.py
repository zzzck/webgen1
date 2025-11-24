"""Lightweight publish/subscribe message bus.

The message bus enables structured, topic-based communication between agents.
Messages are stored for retrieval (so late subscribers can read history) and
handlers can be registered to react to specific topics. Messages are plain
dictionaries with the following shape::

    {
        "topic": "brief",
        "sender": "PM",
        "content": {...},
    }

This keeps agent interactions explicit and machine-readable, mirroring the
publish–subscribe workflow described in the project goals.
"""

from collections import defaultdict
from dataclasses import asdict, is_dataclass
from typing import Any, Callable, Dict, List


Message = Dict[str, Any]


class MessageBus:
    def __init__(self):
        self._storage: Dict[str, List[Message]] = defaultdict(list)
        self._subscribers: Dict[str, List[Callable[[Message], None]]] = defaultdict(list)

    def publish(self, topic: str, sender: str, content: Any) -> Message:
        """Publish a structured message to a topic and notify subscribers."""
        message: Message = {"topic": topic, "sender": sender, "content": content}
        self._storage[topic].append(message)
        for handler in self._subscribers.get(topic, []):
            handler(message)
        return message

    def subscribe(self, topic: str, handler: Callable[[Message], None]):
        """Register a handler for a topic. Handlers receive past messages too."""
        self._subscribers[topic].append(handler)
        for message in self._storage.get(topic, []):
            handler(message)

    def latest(self, topic: str) -> Message | None:
        """Return the most recent message for a topic, if any."""
        return self._storage.get(topic, [])[-1] if self._storage.get(topic) else None

    def dump(self) -> Dict[str, List[Message]]:
        """Return the full message history for debugging or audits."""
        return {
            topic: [self._jsonable(message) for message in messages]
            for topic, messages in self._storage.items()
        }

    @staticmethod
    def _jsonable(value: Any) -> Any:
        if is_dataclass(value):
            return asdict(value)
        if isinstance(value, dict):
            return {k: MessageBus._jsonable(v) for k, v in value.items()}
        if isinstance(value, list):
            return [MessageBus._jsonable(v) for v in value]
        return value
