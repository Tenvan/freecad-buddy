"""Benchmark samples stay consistent: the Markdown shows exactly what the checker uses."""

import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "examples" / "samples"


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, SAMPLES / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_referenzmodell_markdown_matches_the_script() -> None:
    sample = _load("referenzmodell")
    markdown = (SAMPLES / "referenzmodell.md").read_text(encoding="utf-8")

    assert f"```text\n{sample.prompt()}\n```" in markdown, "Prompt im MD veraltet: … referenzmodell.py prompt"
    for stage in sample.STAGE_PARAMETERS:
        values = sample.parameters(stage)
        probe = {**values, "Plate_Length": 240}
        assert f"{sample.expected_volume(values, stage):.1f} mm³" in markdown
        assert f"{sample.expected_volume(probe, stage):.1f} mm³" in markdown
        assert f"| {stage} |" in markdown
        for name in sample.STAGE_PARAMETERS[stage]:
            assert name in markdown
        if stage >= sample.BOX_STAGE:
            assert f"{sample.expected_box_volume(values, stage):.1f} mm³" in markdown
            assert f"{sample.expected_box_volume(probe, stage):.1f} mm³" in markdown
        if stage >= sample.ASSEMBLY_STAGE:
            assert f"{sample.expected_thread_removal(values):.1f} mm³" in markdown
            for addon in sample.STAGE_ADDONS[stage]:
                assert addon.lower() in markdown.lower()
    assert sample.prompt(1).startswith(sample.PROMPT_HEADS[1]), "frühere Stufen behalten ihren Kopf"
    assert sample.LATEST_STAGE == max(sample.STAGE_PARAMETERS) == max(sample.STAGE_PROMPTS)
    assert set(sample.STAGE_FEATURES) == set(sample.STAGE_PARAMETERS)
    assert (SAMPLES / "referenzmodell.png").stat().st_size > 1000
