"""Benchmark samples stay consistent: the Markdown shows the numbers the checker expects."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "examples" / "samples"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SAMPLES / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_testplatte_markdown_matches_checker() -> None:
    sample = _load("testplatte_griff")
    markdown = (SAMPLES / "testplatte-griff.md").read_text(encoding="utf-8")

    assert f"{sample.expected_volume(sample.PARAMETERS):.1f} mm³" in markdown
    probe = {**sample.PARAMETERS, "Plate_Length": 240}
    assert f"{sample.expected_volume(probe):.1f} mm³" in markdown
    for name in sample.PARAMETERS:
        assert name in markdown
    assert (SAMPLES / "testplatte-griff.png").stat().st_size > 1000
