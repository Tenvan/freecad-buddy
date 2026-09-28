import os
from pathlib import Path

import pytest

from freecad_env import AddonInstallError, addon_status, install_addon, uninstall_addon


def _make_source(tmp_path: Path, name: str = "source") -> Path:
    source = tmp_path / name
    source.mkdir()
    (source / "marker.txt").write_text("payload")
    return source


def test_install_creates_junction(tmp_path: Path) -> None:
    mod_dir = tmp_path / "Mod"
    source = _make_source(tmp_path)

    message = install_addon(mod_dir, source)

    link = mod_dir / "FreeCADBuddy"
    assert "installiert" in message
    assert (link / "marker.txt").read_text() == "payload"


def test_install_is_idempotent(tmp_path: Path) -> None:
    mod_dir = tmp_path / "Mod"
    source = _make_source(tmp_path)
    install_addon(mod_dir, source)

    message = install_addon(mod_dir, source)

    assert "bereits installiert" in message


def test_install_rejects_foreign_target_without_force(tmp_path: Path) -> None:
    mod_dir = tmp_path / "Mod"
    source = _make_source(tmp_path, "source")
    other = _make_source(tmp_path, "other")
    install_addon(mod_dir, source)

    with pytest.raises(AddonInstallError, match="zeigt bereits auf"):
        install_addon(mod_dir, other)


def test_install_overwrites_foreign_target_with_force(tmp_path: Path) -> None:
    mod_dir = tmp_path / "Mod"
    source = _make_source(tmp_path, "source")
    other = _make_source(tmp_path, "other")
    install_addon(mod_dir, source)

    message = install_addon(mod_dir, other, force=True)

    link = mod_dir / "FreeCADBuddy"
    assert "installiert" in message
    assert Path(os.path.realpath(link)) == other.resolve()
    # Das alte Ziel bleibt unangetastet, nur der Link wurde umgehängt.
    assert (source / "marker.txt").exists()


def test_install_never_deletes_a_real_directory(tmp_path: Path) -> None:
    mod_dir = tmp_path / "Mod"
    mod_dir.mkdir()
    real_dir = mod_dir / "FreeCADBuddy"
    real_dir.mkdir()
    (real_dir / "keep.txt").write_text("do-not-delete")
    source = _make_source(tmp_path)

    with pytest.raises(AddonInstallError):
        install_addon(mod_dir, source)
    with pytest.raises(AddonInstallError):
        install_addon(mod_dir, source, force=True)

    assert (real_dir / "keep.txt").read_text() == "do-not-delete"


def test_uninstall_removes_only_the_link(tmp_path: Path) -> None:
    mod_dir = tmp_path / "Mod"
    source = _make_source(tmp_path)
    install_addon(mod_dir, source)

    message = uninstall_addon(mod_dir)

    assert "entfernt" in message
    assert not (mod_dir / "FreeCADBuddy").exists()
    assert (source / "marker.txt").read_text() == "payload"


def test_uninstall_reports_not_installed(tmp_path: Path) -> None:
    mod_dir = tmp_path / "Mod"

    assert "nicht installiert" in uninstall_addon(mod_dir)


def test_uninstall_never_deletes_a_real_directory(tmp_path: Path) -> None:
    mod_dir = tmp_path / "Mod"
    mod_dir.mkdir()
    real_dir = mod_dir / "FreeCADBuddy"
    real_dir.mkdir()
    (real_dir / "keep.txt").write_text("do-not-delete")

    with pytest.raises(AddonInstallError):
        uninstall_addon(mod_dir)

    assert (real_dir / "keep.txt").read_text() == "do-not-delete"


def test_status_reports_not_installed(tmp_path: Path) -> None:
    mod_dir = tmp_path / "Mod"
    source = _make_source(tmp_path)

    assert "nicht installiert" in addon_status(mod_dir, source)


def test_status_reports_installed(tmp_path: Path) -> None:
    mod_dir = tmp_path / "Mod"
    source = _make_source(tmp_path)
    install_addon(mod_dir, source)

    assert "installiert" in addon_status(mod_dir, source)


def test_status_reports_foreign_target(tmp_path: Path) -> None:
    mod_dir = tmp_path / "Mod"
    source = _make_source(tmp_path, "source")
    other = _make_source(tmp_path, "other")
    install_addon(mod_dir, source)

    assert "anderes Ziel" in addon_status(mod_dir, other)
