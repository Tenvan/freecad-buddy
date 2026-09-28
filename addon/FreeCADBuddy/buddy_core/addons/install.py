"""Install addons and macros through FreeCAD's own Addon Manager classes, after the user confirmed.

Flow (spike S3): ``start_install`` only creates a job and schedules the work on the Qt main thread,
so the bridge call returns at once. The job then shows our modal confirmation dialog (default
"Abbrechen"); on consent a workbench is installed with ``AddonInstaller`` in a ``QThread`` (only its
``success`` signal counts - ``run()`` returns True on failures too), a macro with ``MacroInstaller``.
A failed workbench install leaves no half-written ``Mod/<id>`` behind. ``install_status`` polls.

The Addon Manager parts sit behind ``Backend`` so tests can replace them (no network, no dialog).
"""

from __future__ import annotations

import itertools
import shutil
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import FreeCAD

from buddy_core.errors import UNSUPPORTED, CoreError, not_found, validation

FINAL_STATES = frozenset({"declined", "installed", "failed"})
_ids = itertools.count(1)


@dataclass
class Job:
    job_id: int
    addon_id: str
    kind: str
    state: str = "awaiting_confirmation"  # → declined | installing → installed | failed
    message: str = ""
    started: float = field(default_factory=time.time)
    finished: float | None = None
    keep_alive: list[Any] = field(default_factory=list)  # Qt objects that must outlive the call
    cleanup: Path | None = None  # Mod/<id> created by this job: removed again if the install fails

    def finish(self, state: str, message: str) -> None:
        if self.state in FINAL_STATES:
            return
        self.state, self.message, self.finished = state, message, time.time()
        self.keep_alive.clear()
        if state == "failed" and self.cleanup is not None and self.cleanup.exists():
            shutil.rmtree(self.cleanup, ignore_errors=True)  # no half-installed addon (AC-09)

    def as_dict(self) -> dict[str, Any]:
        data = {"job_id": self.job_id, "addon_id": self.addon_id, "kind": self.kind, "state": self.state,
                "message": self.message, "done": self.state in FINAL_STATES}  # fmt: skip
        if self.state == "installed" and self.kind != "macro":
            data["restart_required"] = True
        return data


class Backend(Protocol):
    def available(self) -> str | None:
        """``None`` when installing is possible, else the reason (e.g. no GUI)."""

    def mod_dir(self) -> Path: ...

    def schedule(self, fn: Any) -> None:
        """Run ``fn`` soon on the main thread (after the bridge call returned)."""

    def confirm(self, job: Job, details: dict[str, Any]) -> bool: ...

    def install_workbench(self, job: Job, entry: dict[str, Any], branch: str) -> None:
        """Start the install; must eventually call ``job.finish(...)``."""

    def install_macro(self, job: Job, entry: dict[str, Any]) -> None: ...


class AddonManagerBackend:
    """The real thing: FreeCAD GUI dialog plus the Addon Manager installer classes."""

    def available(self) -> str | None:
        if not FreeCAD.GuiUp:
            return "Installing needs the FreeCAD GUI (confirmation dialog)"
        return None

    def mod_dir(self) -> Path:
        return Path(FreeCAD.getUserAppDataDir()) / "Mod"

    def schedule(self, fn: Any) -> None:
        from PySide import QtCore

        QtCore.QTimer.singleShot(0, fn)

    def confirm(self, job: Job, details: dict[str, Any]) -> bool:
        import FreeCADGui
        from PySide import QtWidgets

        lines = [
            f"Soll FreeCAD Buddy „{details.get('name', job.addon_id)}“ installieren?",
            "",
            f"Art: {details.get('kind', job.kind)}",
            f"Quelle: {details.get('repository') or '–'}",
            f"Lizenz: {details.get('license') or 'unbekannt'}",
            f"Maintainer: {details.get('maintainer') or 'unbekannt'}",
            f"Abhängigkeiten: {', '.join(details.get('addon_dependencies') or []) or 'keine'}",
            "",
            "Addons sind fremder Code, der in FreeCAD ausgeführt wird. Nur installieren, wenn du der Quelle vertraust.",
        ]
        if job.kind != "macro":
            lines.append("Nach der Installation ist ein FreeCAD-Neustart nötig.")
        box = QtWidgets.QMessageBox(FreeCADGui.getMainWindow())
        box.setIcon(QtWidgets.QMessageBox.Warning)
        box.setWindowTitle("FreeCAD Buddy – Addon installieren")
        box.setText("\n".join(lines))
        install = box.addButton("Installieren", QtWidgets.QMessageBox.AcceptRole)
        cancel = box.addButton("Abbrechen", QtWidgets.QMessageBox.RejectRole)
        box.setDefaultButton(cancel)
        box.setEscapeButton(cancel)
        box.exec()
        return box.clickedButton() is install

    def install_workbench(self, job: Job, entry: dict[str, Any], branch: str) -> None:
        import NetworkManager
        from AddonCatalog import AddonCatalog
        from addonmanager_installer import AddonInstaller
        from PySide import QtCore

        NetworkManager.InitializeNetworkManager()  # must happen on the main thread (spike S3)
        addon = AddonCatalog({job.addon_id: [entry]}).get_addon_from_id(job.addon_id, branch)
        installer = AddonInstaller(addon, allow_list=[])  # empty allow list: no blocking constraints fetch
        thread = QtCore.QThread()
        installer.moveToThread(thread)
        installer.success.connect(lambda *_: job.finish("installed", "installed - restart FreeCAD"))
        installer.failure.connect(lambda _addon, message: job.finish("failed", str(message)))

        def done() -> None:
            thread.quit()
            if job.state not in FINAL_STATES:  # no signal at all: judge by the result on disk
                target = self.mod_dir() / job.addon_id
                ok = target.is_dir() and any(target.iterdir())
                job.finish("installed" if ok else "failed", "installed" if ok else "installation failed")

        installer.finished.connect(done)
        thread.started.connect(installer.run)
        job.keep_alive += [installer, thread, addon]
        thread.start()

    def install_macro(self, job: Job, entry: dict[str, Any]) -> None:
        from Addon import Addon
        from addonmanager_installer import MacroInstaller
        from addonmanager_macro import Macro

        addon = Addon.from_macro(Macro.from_cache(entry))
        ok = MacroInstaller(addon).run()  # synchronous and local: the macro code is in the catalog
        job.finish(
            "installed" if ok else "failed",
            "macro installed" if ok else "macro installation failed",
        )


_backend: Backend = AddonManagerBackend()
_jobs: dict[int, Job] = {}
_lock = threading.Lock()


def set_backend(backend: Backend | None) -> None:
    """Tests only: replace (or with ``None`` restore) the Addon Manager backend."""
    global _backend
    _backend = backend if backend is not None else AddonManagerBackend()


def _running_job(addon_id: str) -> Job | None:
    return next((j for j in _jobs.values() if j.addon_id == addon_id and j.state not in FINAL_STATES), None)


def start_install(addon_id: str, kind: str, entry: dict[str, Any], details: dict[str, Any] | None = None,
                  branch: str = "") -> dict[str, Any]:  # fmt: skip
    """Create (or return the running) install job; the work starts after this call returned."""
    if kind not in ("workbench", "macro", "other"):
        raise validation(f"Kind '{kind}' cannot be installed through FreeCAD Buddy", kind=kind)
    reason = _backend.available()
    if reason:
        raise CoreError(UNSUPPORTED, reason)
    with _lock:
        running = _running_job(addon_id)
        if running is not None:
            return running.as_dict()
        job = Job(next(_ids), addon_id, kind)
        _jobs[job.job_id] = job
    _backend.schedule(lambda: _run(job, entry, details or {}, branch))
    return job.as_dict()


def _run(job: Job, entry: dict[str, Any], details: dict[str, Any], branch: str) -> None:
    target = _backend.mod_dir() / job.addon_id
    if job.kind != "macro" and not target.exists():
        job.cleanup = target
    try:
        if not _backend.confirm(job, details):
            job.finish("declined", "declined by the user in FreeCAD")
            return
        job.state = "installing"
        if job.kind == "macro":
            _backend.install_macro(job, entry)
        else:
            _backend.install_workbench(job, entry, branch or str(entry.get("branch_display_name") or ""))
    except Exception as error:  # an addon install must never take the bridge down
        job.finish("failed", f"{type(error).__name__}: {error}")


def install_status(job_id: int) -> dict[str, Any]:
    """Job snapshot; runs on the bridge thread (not the Qt main thread) while the dialog may be open."""
    with _lock:
        job = _jobs.get(int(job_id))
        if job is None:
            raise not_found(f"Install job {job_id}")
        return job.as_dict()
