import pytest

from buddy_core.errors import CoreError
from buddy_core.printing import profile as profile_module


def test_profile_path_prefers_freecad_buddy_home(tmp_path):
    environ = {"FREECAD_BUDDY_HOME": str(tmp_path)}

    assert profile_module.profile_path(environ) == tmp_path / "printer-profile.toml"


def test_profile_path_falls_back_to_appdata(tmp_path):
    environ = {"APPDATA": str(tmp_path)}

    assert profile_module.profile_path(environ) == tmp_path / "FreeCADBuddy" / "printer-profile.toml"


def test_get_printer_profile_returns_defaults_when_file_missing(tmp_path):
    path = tmp_path / "printer-profile.toml"

    profile = profile_module.get_printer_profile(str(path))

    assert profile["build_x"] == 256.0
    assert profile["nozzle"] == 0.4
    assert profile["material"] == "PLA"
    assert profile["path"] == str(path)
    assert not path.exists()


def test_set_and_get_printer_profile_round_trip(tmp_path):
    path = tmp_path / "printer-profile.toml"

    saved = profile_module.set_printer_profile({"nozzle": 0.6, "material": "PETG"}, str(path))

    assert saved["nozzle"] == 0.6
    assert saved["material"] == "PETG"
    assert path.is_file()

    loaded = profile_module.get_printer_profile(str(path))

    assert loaded["nozzle"] == 0.6
    assert loaded["material"] == "PETG"
    assert loaded["build_x"] == 256.0  # untouched defaults survive the round trip


def test_set_printer_profile_rejects_unknown_key(tmp_path):
    path = tmp_path / "printer-profile.toml"

    with pytest.raises(CoreError) as excinfo:
        profile_module.set_printer_profile({"unknown_key": 1}, str(path))

    assert excinfo.value.name == "validation"


def test_set_printer_profile_rejects_non_positive_number(tmp_path):
    path = tmp_path / "printer-profile.toml"

    with pytest.raises(CoreError) as excinfo:
        profile_module.set_printer_profile({"nozzle": 0}, str(path))

    assert excinfo.value.name == "validation"


def test_set_printer_profile_rejects_wrong_type(tmp_path):
    path = tmp_path / "printer-profile.toml"

    with pytest.raises(CoreError) as excinfo:
        profile_module.set_printer_profile({"nozzle": "thick"}, str(path))

    assert excinfo.value.name == "validation"


def test_set_printer_profile_rejects_empty_updates(tmp_path):
    path = tmp_path / "printer-profile.toml"

    with pytest.raises(CoreError) as excinfo:
        profile_module.set_printer_profile({}, str(path))

    assert excinfo.value.name == "validation"
