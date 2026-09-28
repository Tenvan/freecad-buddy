import logging

from buddy_server.events import Console, EventBus
from buddy_server.logs import route_logging_to_bus


def test_warnings_go_to_bus_and_info_is_dropped() -> None:
    bus = EventBus()
    seen: list[object] = []
    bus.subscribe(seen.append)
    root = logging.getLogger()
    saved = (root.handlers[:], root.level)
    try:
        route_logging_to_bus(bus)
        logging.getLogger("mcp.server").info("noise")
        logging.getLogger("uvicorn.error").warning("port trouble")
    finally:
        root.handlers, root.level = saved[0], saved[1]

    assert seen == [Console("warning", "uvicorn.error: port trouble", at=seen[0].at)]  # type: ignore[attr-defined]
