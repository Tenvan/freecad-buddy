"""Workbench switches: two buttons per setting, only the one that changes something is active."""

import pytest

from buddy_bridge import commands, service


class _Stored:
    def __init__(self, value: bool, forced: bool = False) -> None:
        self.value = value
        self.forced = forced

    def enabled(self) -> bool:
        return self.forced or self.value

    def store(self, value: bool) -> None:
        self.value = value


@pytest.fixture
def messages(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str]]:
    seen: list[tuple[str, str]] = []
    monkeypatch.setattr(service, "console", lambda level, message: seen.append((level, message)))
    return seen


def _pair(stored: _Stored) -> tuple[commands._SetSetting, commands._SetSetting]:
    setting = commands._Setting("Test", stored.enabled, stored.store, "an", "aus")
    return commands._SetSetting(setting, True, "an", ""), commands._SetSetting(setting, False, "aus", "")


def test_only_the_button_that_changes_the_state_is_active(messages: list[tuple[str, str]]) -> None:
    stored = _Stored(False)
    on, off = _pair(stored)
    assert (on.IsActive(), off.IsActive()) == (True, False)

    on.Activated()

    assert stored.value is True
    assert (on.IsActive(), off.IsActive()) == (False, True)
    assert messages == [("info", "Test an")]


def test_a_forced_setting_warns_instead_of_pretending(messages: list[tuple[str, str]]) -> None:
    stored = _Stored(True, forced=True)
    _, off = _pair(stored)

    off.Activated()

    assert stored.value is False
    assert messages[-1][0] == "warning" and "Umgebungsvariable" in messages[-1][1]


def test_every_setting_has_an_on_and_an_off_button() -> None:
    switches = [c for c in commands.COMMANDS.values() if isinstance(c, commands._SetSetting)]
    by_setting: dict[str, set[bool]] = {}
    for switch in switches:
        by_setting.setdefault(switch.setting.name, set()).add(switch.value)
    assert set(by_setting) == {"Autostart", "Python-Ausführung", "Addon-Installation"}
    assert all(values == {True, False} for values in by_setting.values())
    assert not any("Toggle" in name for name in commands.COMMANDS)
