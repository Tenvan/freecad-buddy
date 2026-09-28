"""Command line entry point ``freecad-buddy``."""

from __future__ import annotations

import argparse
import asyncio
import sys
import time

from buddy_server import __version__
from buddy_server.config import DEFAULT_BRIDGE_PORT, DEFAULT_PORT, Settings
from buddy_server.events import (
    BridgeState,
    Console,
    Event,
    EventBus,
    ServerFailed,
    ServerStarted,
    SessionsChanged,
    ToolFinished,
)
from buddy_server.runner import PortInUse, ServerRunner


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="freecad-buddy", description="MCP-Server für FreeCAD (mit TUI)")
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help=f"MCP-HTTP-Port (Standard {DEFAULT_PORT})"
    )
    parser.add_argument(
        "--bridge-port",
        type=int,
        default=DEFAULT_BRIDGE_PORT,
        help=f"Bridge-Port (Standard {DEFAULT_BRIDGE_PORT})",
    )
    parser.add_argument("--headless", action="store_true", help="Ohne TUI starten (Log auf stderr)")
    parser.add_argument(
        "--allow-python",
        action="store_true",
        help="execute_python freischalten (wie FREECAD_BUDDY_ALLOW_PYTHON=1)",
    )
    parser.add_argument("--print-claude-command", action="store_true", help="claude-mcp-add-Befehl ausgeben")
    parser.add_argument("--version", action="version", version=f"freecad-buddy {__version__}")
    return parser.parse_args(argv)


def settings_from(args: argparse.Namespace) -> Settings:
    settings = Settings(port=args.port, bridge_port=args.bridge_port)
    if args.allow_python:
        settings.allow_python = True
    return settings


def format_event(event: Event) -> str | None:
    stamp = time.strftime("%H:%M:%S", time.localtime(event.at))
    match event:
        case ServerStarted():
            return f"{stamp} MCP-Server bereit: {event.url} (execute_python: {'an' if event.allow_python else 'aus'})"
        case ServerFailed():
            return f"{stamp} FEHLER: {event.message}"
        case BridgeState():
            return f"{stamp} Bridge: {event.state} {event.message}".rstrip()
        case SessionsChanged():
            return f"{stamp} MCP-Sessions: {event.count}"
        case ToolFinished():
            status = "ok" if event.ok else "FEHLER"
            return f"{stamp} {event.name} {status} ({event.duration * 1000:.0f} ms) {event.summary}"
        case Console():
            return f"{stamp} [{event.level}] {event.text}"
    return None


def run_headless(settings: Settings) -> int:
    bus = EventBus()

    def log(event: Event) -> None:
        line = format_event(event)
        if line:
            print(line, file=sys.stderr, flush=True)

    bus.subscribe(log)
    runner = ServerRunner(settings, bus)
    try:
        asyncio.run(runner.run())
    except PortInUse:
        return 2
    except KeyboardInterrupt:
        return 0
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    settings = settings_from(args)
    if args.print_claude_command:
        print(settings.claude_add_command())
        return 0
    if args.headless:
        return run_headless(settings)
    from buddy_server.logs import route_logging_to_bus
    from buddy_server.tui import BuddyApp

    bus = EventBus()
    route_logging_to_bus(bus)  # nothing may print to the terminal while the TUI owns it
    BuddyApp(settings, ServerRunner(settings, bus)).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
