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
