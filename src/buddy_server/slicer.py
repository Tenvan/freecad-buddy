"""OrcaSlicer CLI: slice an exported part headless and read print time and filament use.

Used only when OrcaSlicer is installed. Printer, process and filament come from exported Orca preset
files (``FREECAD_BUDDY_ORCA_SETTINGS="machine.json;process.json"``, ``FREECAD_BUDDY_ORCA_FILAMENT``);
without them Orca slices with its defaults. The result is a ``.gcode.3mf`` next to the export whose
``Metadata/slice_info.config`` holds the prediction (CLI reference: orcaslicer.com/wiki/cli).
"""

from __future__ import annotations

import asyncio
import os
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

TIMEOUT_SECONDS = 300.0
_TIME = re.compile(r"(\d+)\s*([dhms])")
_GCODE_TIME = re.compile(
    r";\s*(?:model printing time|estimated printing time[^=:]*)\s*[=:]\s*([^;\n]+)", re.I
)
_GCODE_WEIGHT = re.compile(r";\s*(?:total filament weight \[g\]|filament used \[g\])\s*[=:]\s*([\d.]+)", re.I)


def find_orca(environ: os._Environ[str] | dict[str, str] | None = None) -> Path | None:
    env = os.environ if environ is None else environ
    explicit = env.get("FREECAD_BUDDY_ORCASLICER")
    if explicit:
        return Path(explicit) if Path(explicit).is_file() else None
    for name in ("orca-slicer", "OrcaSlicer"):
        found = shutil.which(name)
        if found:
            return Path(found)
    candidates = [Path("/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer")]
    for var, sub in (("ProgramFiles", ""), ("LOCALAPPDATA", "Programs")):
        if env.get(var):
            candidates.append(Path(env[var], sub, "OrcaSlicer", "orca-slicer.exe"))
    return next((path for path in candidates if path.is_file()), None)


def command(exe: Path, model: Path, output: Path, environ: os._Environ[str] | dict[str, str]) -> list[str]:
    args = [str(exe), "--arrange", "1", "--slice", "0", "--outputdir", str(output.parent),
            "--export-3mf", output.name]  # fmt: skip
    if environ.get("FREECAD_BUDDY_ORCA_SETTINGS"):
        args += ["--load-settings", environ["FREECAD_BUDDY_ORCA_SETTINGS"]]
    if environ.get("FREECAD_BUDDY_ORCA_FILAMENT"):
        args += ["--load-filaments", environ["FREECAD_BUDDY_ORCA_FILAMENT"]]
    return [*args, str(model)]


def _seconds(text: str) -> int | None:
    parts = _TIME.findall(text)
    factor = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    return sum(int(n) * factor[u] for n, u in parts) if parts else None


def _duration(seconds: int) -> str:
    hours, rest = divmod(seconds, 3600)
    return f"{hours} h {rest // 60} min" if hours else f"{rest // 60} min {rest % 60} s"


def read_result(path: Path) -> dict[str, Any]:
    """Print time (s) and filament (g, m) from a sliced .gcode.3mf; G-code header comments as fallback."""
    data: dict[str, Any] = {"file": str(path)}
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if "Metadata/slice_info.config" in names:
            root = ET.fromstring(archive.read("Metadata/slice_info.config"))
            seconds = grams = meters = 0.0
            for plate in root.iter("plate"):
                meta = {m.get("key"): m.get("value") for m in plate.iter("metadata")}
                seconds += float(meta.get("prediction") or 0)
                grams += float(meta.get("weight") or 0)
                meters += sum(float(f.get("used_m") or 0) for f in plate.iter("filament"))
            if seconds:
                data["print_time_s"] = round(seconds)
            if grams:
                data["filament_g"] = round(grams, 2)
            if meters:
                data["filament_m"] = round(meters, 2)
            warnings = [w.get("msg") for w in root.iter("warning") if w.get("msg")]
            if warnings:
                data["slicer_warnings"] = warnings
        gcodes = [n for n in names if n.endswith(".gcode")]
        if gcodes and "print_time_s" not in data:
            raw = archive.read(gcodes[0])  # the prediction is in the header or trailer comments
            head = (raw[:20000] + b"\n" + raw[-20000:]).decode("utf-8", "replace")
            if match := _GCODE_TIME.search(head):
                data["print_time_s"] = _seconds(match.group(1))
            if (match := _GCODE_WEIGHT.search(head)) and "filament_g" not in data:
                data["filament_g"] = float(match.group(1))
    if seconds := data.get("print_time_s"):
        data["print_time"] = _duration(int(seconds))
    return data


async def slice_model(
    model: Path, exe: Path, environ: os._Environ[str] | dict[str, str] | None = None
) -> dict[str, Any]:
    """Run the CLI; raises ``RuntimeError`` with Orca's output tail if it fails."""
    env = os.environ if environ is None else environ
    output = model.with_name(model.stem + ".gcode.3mf")
    output.unlink(missing_ok=True)
    process = await asyncio.create_subprocess_exec(
        *command(exe, model, output, env), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    try:
        out, _ = await asyncio.wait_for(process.communicate(), TIMEOUT_SECONDS)
    except TimeoutError:
        process.kill()
        raise RuntimeError(f"OrcaSlicer did not finish within {TIMEOUT_SECONDS:.0f} s") from None
    if not output.is_file():
        tail = out.decode("utf-8", "replace").strip()[-800:]
        raise RuntimeError(f"OrcaSlicer failed (exit {process.returncode}): {tail or 'no output'}")
    try:
        result = read_result(output)
    except (zipfile.BadZipFile, ET.ParseError, KeyError, ValueError) as error:
        raise RuntimeError(f"OrcaSlicer result {output.name} unreadable: {error}") from None
    if not env.get("FREECAD_BUDDY_ORCA_SETTINGS"):
        result["note"] = (
            "Sliced with OrcaSlicer defaults; set FREECAD_BUDDY_ORCA_SETTINGS and FREECAD_BUDDY_ORCA_FILAMENT "
            "to exported presets of your printer for real values."
        )
    return result
