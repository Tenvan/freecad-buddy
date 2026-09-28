"""AC-15: masking, binary placeholders, size limits and the JSONL log of tool calls."""

import json
from pathlib import Path

from mcp.types import CallToolResult, ContentBlock, ImageContent, TextContent

from buddy_server.calllog import JsonlLog
from buddy_server.events import ToolFinished, ToolStarted
from buddy_server.payloads import MASK, MAX_DETAIL_CHARS, Masker, describe_result, preview, render_json

TOKEN = "Zq3xT9vLr2Wm8KpA4sYb7NcE1dHf6GjU0oIiQwRtS5"


def test_masker_hides_secret_keys_known_secrets_bearer_and_token_like_strings() -> None:
    mask = Masker(["known-secret-value"])
    data = {
        "api_key": "abc",
        "Authorization": "Bearer something",
        "note": "use known-secret-value here",
        "header": "Authorization: Bearer 123",
        "nested": [{"password": "x"}, TOKEN],
        "label": "Pocket_ScrewHoles",
        "sha": "a" * 64,
    }
    masked = mask(data)

    assert masked["api_key"] == MASK and masked["Authorization"] == MASK
    assert masked["note"] == f"use {MASK} here"
    assert masked["header"] == f"Authorization: Bearer {MASK}"
    assert masked["nested"] == [{"password": MASK}, MASK]
    assert masked["label"] == "Pocket_ScrewHoles" and masked["sha"] == "a" * 64


def test_images_become_placeholders_and_errors_keep_code_and_hints() -> None:
    mask = Masker()
    blocks: list[ContentBlock] = [ImageContent(type="image", data="A" * 4096, mime_type="image/png")]
    image = CallToolResult(content=blocks)
    shown = describe_result(image, mask)
    assert shown.ok and shown.text == "[PNG 3 KB]" and "A" * 20 not in shown.text

    error = CallToolResult(
        content=[TextContent(type="text", text="[recompute_failed] Pad ungültig\nHinweis: Länge prüfen")],
        is_error=True,
    )
    failed = describe_result(error, mask)
    assert (failed.ok, failed.error_code) == (False, "recompute_failed")
    assert "Hinweis: Länge prüfen" in failed.text


def test_structured_results_are_pretty_json_with_summary_and_masked_warnings() -> None:
    result = CallToolResult(
        content=[TextContent(type="text", text="{}")],
        structured_content={"created": [{"label": "Pad_Base"}], "warnings": [f"token {TOKEN}"]},
    )
    shown = describe_result(result, Masker())

    assert shown.summary == "+Pad_Base"
    assert shown.warnings == (f"token {MASK}",)
    assert '"label": "Pad_Base"' in shown.text


def test_size_limits_for_detail_and_preview() -> None:
    huge = render_json({"data": "x" * (MAX_DETAIL_CHARS * 2)})
    assert len(huge) < MAX_DETAIL_CHARS + 100 and "gekürzt" in huge

    shown = preview("\n".join(str(i) for i in range(100)), max_lines=8)
    assert shown.splitlines()[-1].startswith("… (+92 Zeilen")


def test_jsonl_log_writes_masked_records_and_rotates(tmp_path: Path) -> None:
    path = tmp_path / "calls.jsonl"
    log = JsonlLog(path, max_bytes=2_000)
    for i in range(20):
        log(ToolStarted(i, "pad", '{"length": 5}', "claude-code #1"))
        log(ToolFinished(i, "pad", 0.01, True, "+Pad_Base", response="{}"))

    assert path.with_name("calls.jsonl.1").exists()
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert {r["type"] for r in records} <= {"request", "response"}
    assert any(r.get("session") == "claude-code #1" for r in records)


def test_compact_text_shows_key_facts_instead_of_json() -> None:
    from buddy_server.payloads import compact_text

    pad = {"ok": True, "created": [{"label": "Pad_Plate"}], "warnings": [], "hints": [],
           "feature": {"label": "Pad_Plate"}, "volume": 99999.99999999997, "view": "iso"}  # fmt: skip
    text = compact_text(pad)
    assert "erstellt: Pad_Plate" in text and "Volumen 100\u202f000,0 mm³" in text and "view: iso" in text
    assert "{" not in text

    sketch = {"ok": True, "created": [], "modified": [{"label": "Sketch_Plate"}],
              "sketch": {"sketch": "Sketch_Plate", "dof": 0, "fully_constrained": True}}  # fmt: skip
    assert "Sketch_Plate: DoF 0 (vollständig bestimmt)" in compact_text(sketch)

    check = {"ok": True, "issues": [], "hints": ["Unterkante fasen"], "stats": {"volume": 98994.69}}
    assert "keine Befunde" in compact_text(check) and "→ Unterkante fasen" in compact_text(check)
    assert len(compact_text({f"k{i}": i for i in range(50)}).splitlines()) <= 6


def test_error_compact_keeps_code_and_hints() -> None:
    error = CallToolResult(
        content=[
            TextContent(
                type="text", text="[recompute_failed] Pad ungültig\nHinweis: Länge prüfen\nDetails: {}"
            )
        ],
        is_error=True,
    )
    shown = describe_result(error, Masker())
    assert shown.compact == "[recompute_failed] Pad ungültig\nHinweis: Länge prüfen"


def test_compact_arguments_as_key_value_lines() -> None:
    from buddy_server.payloads import compact_arguments

    text = compact_arguments(
        {
            "sketch": "Sketch_CornerHoles",
            "kind": "hole_rect",
            "params": {"width": "Plate_Length - 2*Hole_Edge_Distance", "diameter": "Hole_Diameter"},
            "parameters": {"Count": {"value": 12, "type": "integer"}},
            "features": ["Pocket_A", "Pocket_B"],
        }
    )
    assert text.splitlines() == [
        "sketch: Sketch_CornerHoles",
        "kind: hole_rect",
        "params: width Plate_Length - 2*Hole_Edge_Distance, diameter Hole_Diameter",
        "parameters: Count {value 12, type integer}",
        "features: [Pocket_A, Pocket_B]",
    ]
    assert compact_arguments({}) == "(keine Argumente)"
    assert len(compact_arguments({f"k{i}": i for i in range(20)}).splitlines()) == 6
