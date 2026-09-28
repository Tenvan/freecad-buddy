from pathlib import Path

from buddy_bridge.tokens import buddy_home, load_or_create_token, read_token, tokens_match


def test_buddy_home_prefers_override_then_appdata(tmp_path: Path) -> None:
    assert buddy_home({"FREECAD_BUDDY_HOME": str(tmp_path), "APPDATA": "x"}) == tmp_path
    assert buddy_home({"APPDATA": str(tmp_path)}) == tmp_path / "FreeCADBuddy"


def test_token_is_created_once_and_reused(tmp_path: Path) -> None:
    path = tmp_path / "sub" / "bridge-token"

    first = load_or_create_token(path)
    second = load_or_create_token(path)

    assert first == second
    assert len(first) >= 32
    assert read_token(path) == first


def test_empty_token_file_is_regenerated(tmp_path: Path) -> None:
    path = tmp_path / "bridge-token"
    path.write_text("  \n", encoding="utf-8")

    assert load_or_create_token(path).strip()


def test_read_token_never_creates(tmp_path: Path) -> None:
    path = tmp_path / "missing"

    assert read_token(path) is None
    assert not path.exists()


def test_tokens_match_rejects_wrong_values() -> None:
    assert tokens_match("secret", "secret")
    assert not tokens_match("secret", "Secret")
    assert not tokens_match("secret", None)
    assert not tokens_match("secret", 123)
