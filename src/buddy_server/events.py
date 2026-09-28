"""Event bus between the server core and its front ends (TUI or headless log).

The core never touches widgets: it publishes events, front ends subscribe.
"""

from __future__ import annotations

import contextlib
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Event:
    at: float = field(default_factory=time.time, kw_only=True)


@dataclass(frozen=True)
class ServerStarted(Event):
    url: str
    allow_python: bool


@dataclass(frozen=True)
class ServerFailed(Event):
    message: str


@dataclass(frozen=True)
class BridgeState(Event):
    state: str  # "connected" | "waiting" | "error"
    message: str = ""
    freecad_version: str | None = None


@dataclass(frozen=True)
class SessionsChanged(Event):
    count: int


@dataclass(frozen=True)
class ToolStarted(Event):
    call_id: int
    name: str


@dataclass(frozen=True)
class ToolFinished(Event):
    call_id: int
    name: str
    duration: float
    ok: bool
    summary: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class Console(Event):
    level: str  # "info" | "warning" | "error"
    text: str


Subscriber = Callable[[Event], Any]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: list[Subscriber] = []

    def subscribe(self, subscriber: Subscriber) -> None:
        self._subscribers.append(subscriber)

    def publish(self, event: Event) -> None:
        for subscriber in list(self._subscribers):
            with contextlib.suppress(Exception):  # a broken front end must never break a tool call
                subscriber(event)
