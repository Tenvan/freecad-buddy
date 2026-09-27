from pathlib import Path

import pytest

from freecad_env import FreeCADNotFoundError, find_freecad_home, freecad_subprocess_env


def _fake_install(root: Path, name: str) -> Path:
    home = root / name
    (home / "bin").mkdir(parents=True)
    (home / "bin" / "python.exe").touch()
    (home / "bin" / "FreeCAD.pyd").touch()
    return home


def test_explicit_freecad_home_wins(tmp_path: Path) -> None:
    home = _fake_install(tmp_path, "custom")
    _fake_install(tmp_path / "Programs", "FreeCAD 99.0")

    assert find_freecad_home({"FREECAD_HOME": str(home), "LOCALAPPDATA": str(tmp_path)}) == home


def test_invalid_explicit_home_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(FreeCADNotFoundError, match="FREECAD_HOME"):
        find_freecad_home({"FREECAD_HOME": str(tmp_path)})


def test_highest_version_is_selected(tmp_path: Path) -> None:
    programs = tmp_path / "Programs"
    _fake_install(programs, "FreeCAD 1.1")
    newest = _fake_install(programs, "FreeCAD 26.3")
    _fake_install(programs, "FreeCAD 26.2")

    assert find_freecad_home({"LOCALAPPDATA": str(tmp_path)}) == newest


def test_directories_without_python_are_ignored(tmp_path: Path) -> None:
    (tmp_path / "Programs" / "FreeCAD 27.0" / "bin").mkdir(parents=True)
    valid = _fake_install(tmp_path / "Programs", "FreeCAD 26.3")

    assert find_freecad_home({"LOCALAPPDATA": str(tmp_path)}) == valid


def test_nothing_found_raises(tmp_path: Path) -> None:
    with pytest.raises(FreeCADNotFoundError):
        find_freecad_home({"LOCALAPPDATA": str(tmp_path)})


def test_subprocess_env_strips_interpreter_overrides() -> None:
    env = freecad_subprocess_env(
        {"PYTHONHOME": "x", "PYTHONPATH": "y", "VIRTUAL_ENV": "z", "__PYVENV_LAUNCHER__": "w", "PATH": "p"}
    )

    assert env == {"PATH": "p"}
