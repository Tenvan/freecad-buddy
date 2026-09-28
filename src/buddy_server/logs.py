"""Route Python logging (mcp SDK, uvicorn) into the event bus.

In TUI mode nothing may write to the terminal directly, or the screen gets corrupted.
"""

from __future__ import annotations

import logging

from buddy_server.events import Console, EventBus

_LEVELS = {logging.WARNING: "warning", logging.ERROR: "error", logging.CRITICAL: "error"}
_LOGGERS = ("", "mcp", "uvicorn", "uvicorn.error", "uvicorn.access")


class BusHandler(logging.Handler):
    def __init__(self, bus: EventBus) -> None:
        super().__init__(level=logging.WARNING)
        self._bus = bus

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = _LEVELS.get(record.levelno, "info")
            self._bus.publish(Console(level, f"{record.name}: {record.getMessage()}"))
        except Exception:
            self.handleError(record)


def route_logging_to_bus(bus: EventBus) -> None:
    handler = BusHandler(bus)
    for name in _LOGGERS:
        logger = logging.getLogger(name)
        logger.handlers = [handler] if name == "" else []
        logger.propagate = name != ""
        if name:
            logger.setLevel(logging.WARNING)
