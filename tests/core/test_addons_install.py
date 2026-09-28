"""AC-08/AC-09: install jobs with confirmation, cleanup and the Addon Manager API we rely on."""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from buddy_core.addons import install
from buddy_core.errors import CoreError

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "addon_catalog"


class FakeBackend:
    """No dialog, no network: ``answer`` decides the dialog, ``outcome`` the installer."""

    def __init__(self, mod_dir: Path, answer: bool = True, outcome: str = "installed") -> None:
        self._mod = mod_dir
        self.answer = answer
        self.outcome = outcome
        self.scheduled: list[Any] = []
        self.confirmed: list[dict[str, Any]] = []

    def available(self) -> str | None:
        return None

    def mod_dir(self) -> Path:
        return self._mod

    def schedule(self, fn: Any) -> None:
        self.scheduled.append(fn)

    def run_scheduled(self) -> None:
        while self.scheduled:
            self.scheduled.pop(0)()

    def confirm(self, job: install.Job, details: dict[str, Any]) -> bool:
        self.confirmed.append(details)
        return self.answer

    def install_workbench(self, job: install.Job, entry: dict[str, Any], branch: str) -> None:
        target = self._mod / job.addon_id
        target.mkdir(parents=True)
        (target / "Init.py").write_text("# partial download\n")
        if self.outcome == "installed":
            job.finish("installed", "installiert")
        elif self.outcome == "failed":
            job.finish("failed", "HTTP 404")
        else:
            raise RuntimeError("zip kaputt")

    def install_macro(self, job: install.Job, entry: dict[str, Any]) -> None:
        job.finish("installed", "Makro installiert")


@pytest.fixture
def backend(tmp_path: Path) -> Iterator[FakeBackend]:
    fake = FakeBackend(tmp_path / "Mod")
    install.set_backend(fake)
    yield fake
    install.set_backend(None)


def _entry() -> dict[str, Any]:
    return json.loads((FIXTURE / "addon_catalog_cache.json").read_text(encoding="utf-8"))["lattice2"][0]


def test_job_waits_for_the_dialog_and_installs(backend: FakeBackend) -> None:
    job = install.start_install("lattice2", "workbench", _entry(), {"name": "Lattice2"})
    assert job["state"] == "awaiting_confirmation" and not job["done"]
    assert install.start_install("lattice2", "workbench", _entry())["job_id"] == job["job_id"]  # no duplicate

    backend.run_scheduled()
    done = install.install_status(job["job_id"])
    assert done["state"] == "installed" and done["restart_required"] is True
    assert backend.confirmed == [{"name": "Lattice2"}]
    assert (backend.mod_dir() / "lattice2" / "Init.py").exists()


def test_declined_changes_nothing(backend: FakeBackend) -> None:
    backend.answer = False
    job = install.start_install("Gridfinity", "workbench", _entry())
    backend.run_scheduled()

    assert install.install_status(job["job_id"])["state"] == "declined"
    assert not (backend.mod_dir() / "Gridfinity").exists()


@pytest.mark.parametrize("outcome", ["failed", "exception"])
def test_failed_install_leaves_no_rest(backend: FakeBackend, outcome: str) -> None:
    backend.outcome = outcome
    job = install.start_install("FreeGrid", "workbench", _entry())
    backend.run_scheduled()

    status = install.install_status(job["job_id"])
    assert status["state"] == "failed" and status["message"]
    assert not (backend.mod_dir() / "FreeGrid").exists()


def test_macro_and_guards(backend: FakeBackend) -> None:
    job = install.start_install("FCHoneycombMaker", "macro", {"name": "FCHoneycombMaker"})
    backend.run_scheduled()
    status = install.install_status(job["job_id"])
    assert status["state"] == "installed" and "restart_required" not in status

    with pytest.raises(CoreError):
        install.start_install("Pack", "preference_pack", {})
    with pytest.raises(CoreError):
        install.install_status(999_999)


def test_real_backend_needs_the_gui() -> None:
    install.set_backend(None)
    with pytest.raises(CoreError) as info:
        install.start_install("lattice2", "workbench", _entry())
    assert info.value.name == "unsupported"


def test_addon_manager_api_we_depend_on_is_available() -> None:
    """Compatibility check against the running build (weekly API drift, spike S3)."""
    import NetworkManager
    from Addon import Addon
    from AddonCatalog import AddonCatalog
    from addonmanager_installer import AddonInstaller, MacroInstaller
    from addonmanager_macro import Macro

    assert callable(NetworkManager.InitializeNetworkManager)
    for signal in ("success", "failure", "finished"):
        assert hasattr(AddonInstaller, signal)
    assert callable(MacroInstaller.run)

    addon = AddonCatalog({"lattice2": [_entry()]}).get_addon_from_id("lattice2", "master")
    assert addon.name == "lattice2"
    macro_data = json.loads((FIXTURE / "macro_cache.json").read_text(encoding="utf-8"))["FCHoneycombMaker"]
    assert Addon.from_macro(Macro.from_cache(macro_data)).macro is not None
