"""Command line entry point ``freecad-buddy``."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import threading
import time
from pathlib import Path

from buddy_server import __version__
from buddy_server.config import DEFAULT_BRIDGE_PORT, DEFAULT_PORT, Settings
from buddy_server.events import (
    BridgeState,
    Console,
    DesignToolProposed,
    Event,
    EventBus,
    ServerFailed,
    ServerStarted,
    SessionsChanged,
    ToolFinished,
    ToolStarted,
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
    parser.add_argument(
        "--allow-addon-install",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="install_addon anbieten (Standard an; aus mit --no-allow-addon-install oder "
        "FREECAD_BUDDY_ALLOW_ADDON_INSTALL=0). FreeCAD braucht eigene Freischaltung und fragt jedes Mal nach",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        metavar="PFAD",
        help="Tool-Aufrufe (Anfrage und Antwort, Geheimnisse maskiert) als JSONL mitschreiben, rotiert ab 10 MB",
    )
    parser.add_argument("--print-claude-command", action="store_true", help="claude-mcp-add-Befehl ausgeben")
    parser.add_argument("--version", action="version", version=f"freecad-buddy {__version__}")
    return parser.parse_args(argv)


def settings_from(args: argparse.Namespace) -> Settings:
    settings = Settings(port=args.port, bridge_port=args.bridge_port)
    if args.allow_python:
        settings.allow_python = True
    if args.allow_addon_install is not None:
        settings.allow_addon_install = args.allow_addon_install
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
        case ToolStarted():
            arguments = " ".join(event.arguments.split())
            arguments = arguments if len(arguments) <= 300 else arguments[:299] + "…"
            return f"{stamp} → {event.name} [{event.session}] {arguments}"
        case ToolFinished():
            status = "ok" if event.ok else "FEHLER"
            line = f"{stamp} ← {event.name} {status} ({event.duration * 1000:.0f} ms) {event.summary}"
            return line + "".join(f" ⚠ {warning}" for warning in event.warnings)
        case DesignToolProposed():
            return f"{stamp} Design-Tool-Vorschlag: {event.name} ({event.count}×) – {event.problem}"
        case Console():
            return f"{stamp} [{event.level}] {event.text}"
    return None


def run_headless(settings: Settings, log_file: Path | None = None) -> int:
    bus = _bus(log_file)

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


def _bus(log_file: Path | None) -> EventBus:
    bus = EventBus()
    if log_file is not None:
        from buddy_server.calllog import JsonlLog

        bus.subscribe(JsonlLog(log_file))
    return bus


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    settings = settings_from(args)
    if args.print_claude_command:
        print(settings.claude_add_command())
        return 0
    if args.headless:
        return run_headless(settings, args.log_file)
    from buddy_server.logs import route_logging_to_bus
    from buddy_server.tui import BuddyApp

    bus = _bus(args.log_file)
    route_logging_to_bus(bus)  # nothing may print to the terminal while the TUI owns it
    BuddyApp(settings, ServerRunner(settings, bus)).run()
    _exit_despite_stuck_threads()
    return 0


def _exit_despite_stuck_threads(grace: float = 2.0) -> None:
    """A thread blocked in a bridge call would keep the process alive after the TUI closed."""
    deadline = time.monotonic() + grace
    stuck = _live_threads()
    while stuck and time.monotonic() < deadline:
        time.sleep(0.1)
        stuck = _live_threads()
    if stuck:
        names = ", ".join(thread.name for thread in stuck)
        print(f"freecad-buddy: beende trotz hängender Threads ({names})", file=sys.stderr, flush=True)
        os._exit(0)


def _live_threads() -> list[threading.Thread]:
    main = threading.main_thread()
    return [t for t in threading.enumerate() if t is not main and not t.daemon and t.is_alive()]


if __name__ == "__main__":
    raise SystemExit(main())
