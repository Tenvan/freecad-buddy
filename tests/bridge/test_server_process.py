import sys
from pathlib import Path

from buddy_bridge.server_process import ServerProcess, child_env, resolve_command


def test_resolve_command_prefers_setting_then_env(tmp_path: Path) -> None:
    exe = tmp_path / "x.exe"
    exe.write_text("")
    assert resolve_command(str(exe), {}) == str(exe)
    assert resolve_command("", {"FREECAD_BUDDY_SERVER_CMD": str(exe)}) == str(exe)
    assert resolve_command(str(tmp_path / "missing"), {"PATH": ""}) is None


def test_child_env_drops_python_variables() -> None:
    env = child_env({"PYTHONHOME": "x", "PYTHONPATH": "y", "VIRTUAL_ENV": "z", "KEEP": "1"})
    assert env == {"KEEP": "1"}


def test_process_lifecycle_and_exit_report(tmp_path: Path) -> None:
    logs: list[tuple[str, str]] = []
    # python rejects --headless with exit code 2, the code freecad-buddy uses for "port in use".
    process = ServerProcess(
        sys.executable, 1, tmp_path / "server.log", lambda lvl, msg: logs.append((lvl, msg))
    )
    process.start()
    assert process._process is not None
    process._process.wait(timeout=20)
    process.check()
    assert any("Port belegt" in message for _, message in logs)
    process.stop()
    assert not process.running
