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
        self._timeline: List[Message] = []

    def publish(self, topic: str, sender: str, content: Any) -> Message:
        """Publish a structured message to a topic and notify subscribers."""
        message: Message = {"topic": topic, "sender": sender, "content": content}
        self._storage[topic].append(message)
        self._timeline.append(message)
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

    def history(self, topic: str | None = None) -> List[Message]:
        """Return chronological messages, optionally filtered by topic."""
        if topic is None:
            return list(self._timeline)
        return [msg for msg in self._timeline if msg.get("topic") == topic]

    def chat_history(self) -> List[Dict[str, Any]]:
        """Return timeline encoded as chat messages for agent context."""

        chat_messages: List[Dict[str, Any]] = []
        for msg in self._timeline:
            sender = msg.get("sender", "Agent")
            topic = msg.get("topic", "")
            role = "user" if sender.lower() == "user" else "assistant"
            content_text = (
                f"Topic: {topic}\nSender: {sender}\nContent:\n"
                f"{self._json_dump(msg.get('content'))}"
            )
            chat_messages.append(
                {"role": role, "content": [{"type": "text", "text": content_text}]}
            )
        return chat_messages

    @staticmethod
    def _jsonable(value: Any) -> Any:
        if is_dataclass(value):
            return asdict(value)
        if isinstance(value, dict):
            return {k: MessageBus._jsonable(v) for k, v in value.items()}
        if isinstance(value, list):
            return [MessageBus._jsonable(v) for v in value]
        return value

    @staticmethod
    def _json_dump(value: Any) -> str:
        import json

        try:
            return json.dumps(MessageBus._jsonable(value), ensure_ascii=False, indent=2)
        except TypeError:
            return str(value)
