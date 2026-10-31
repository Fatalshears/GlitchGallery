"""Publish/subscribe between processes, modelled on openpilot's cereal/msgq:
each topic is a ring buffer; publishers never block; subscribers read the
newest message and can tell when a publisher is late or dead.
"""

from dataclasses import dataclass, field
from typing import Any


class RingBuffer:
    """Fixed-capacity buffer that overwrites the oldest item when full."""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self._items: list[Any] = [None] * capacity
        self.write_count = 0  # total items ever written

    def push(self, item: Any) -> None:
        self._items[self.write_count % self.capacity] = item
        self.write_count += 1

    def read_from(self, cursor: int) -> tuple[list[Any], int, int]:
        """Items written since `cursor`; returns (items, new_cursor, dropped) — dropped counts
        items overwritten before this reader got to them."""
        oldest = max(0, self.write_count - self.capacity)
        dropped = max(0, oldest - cursor)
        start = max(cursor, oldest)
        items = [self._items[i % self.capacity] for i in range(start, self.write_count)]
        return items, self.write_count, dropped


@dataclass
class Message:
    topic: str
    mono_time: float  # seconds, monotonic clock of the publisher
    data: dict
    valid: bool = True


class Bus:
    def __init__(self, capacity: int = 64):
        self.capacity = capacity
        self.topics: dict[str, RingBuffer] = {}

    def publish(self, msg: Message) -> None:
        self.topics.setdefault(msg.topic, RingBuffer(self.capacity)).push(msg)


@dataclass
class SubMaster:
    """Latest-value view of several topics plus health checks (like openpilot's SubMaster)."""

    bus: Bus
    expected_hz: dict[str, float]
    latest: dict[str, Message] = field(default_factory=dict)
    dropped: dict[str, int] = field(default_factory=dict)
    _cursors: dict[str, int] = field(default_factory=dict)
    updated: set[str] = field(default_factory=set)

    def update(self) -> None:
        self.updated = set()
        for topic in self.expected_hz:
            ring = self.bus.topics.get(topic)
            if ring is None:
                continue
            items, self._cursors[topic], lost = ring.read_from(self._cursors.get(topic, 0))
            self.dropped[topic] = self.dropped.get(topic, 0) + lost
            if items:
                self.latest[topic] = items[-1]
                self.updated.add(topic)

    def alive(self, topic: str, now: float) -> bool:
        """Received recently enough: within 2.5 expected periods (tolerates jitter)."""
        msg = self.latest.get(topic)
        return msg is not None and now - msg.mono_time <= 2.5 / self.expected_hz[topic]

    def all_ok(self, now: float) -> bool:
        return all(self.alive(t, now) and self.latest[t].valid for t in self.expected_hz)
