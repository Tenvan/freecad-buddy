"""AC-15 / AC-13 (freecad-buddy-referenzen): every tool is documented in its group, docs are current."""

import asyncio

import gen_tool_docs


def test_every_tool_has_an_example_and_docs_are_current() -> None:
    tools, groups = asyncio.run(gen_tool_docs._catalog())
    names = {tool.name for tool in tools}

    assert len(names) <= 100  # tool budget (Ralf, 2026-09-28)
    assert names == set(gen_tool_docs.EXAMPLES), sorted(names ^ set(gen_tool_docs.EXAMPLES))
    files = gen_tool_docs.render(tools, groups)
    for path, content in files.items():
        assert path.read_text(encoding="utf-8") == content, (
            f"{path.name} veraltet: uv run python tools/gen_tool_docs.py"
        )
    assert gen_tool_docs.stale_files(files) == []


def test_every_tool_belongs_to_exactly_one_group_with_prefix() -> None:
    tools, groups = asyncio.run(gen_tool_docs._catalog())
    grouped = [name for _, members in groups for name in members]

    assert sorted(grouped) == sorted(tool.name for tool in tools)  # no tool twice, none missing
    prefix = {name: group.prefix for group, members in groups for name in members}
    for tool in tools:
        assert (tool.description or "").startswith(f"[{prefix[tool.name]}] "), tool.name


def test_document_tool_replaces_the_five_document_tools() -> None:
    """AC-14 (freecad-buddy-referenzen)."""
    tools = {tool.name: tool for tool in asyncio.run(gen_tool_docs._tools())}

    assert "document" in tools
    assert not {"new_document", "open_document", "save_document", "close_document", "revert_document"} & set(
        tools
    )
    actions = tools["document"].input_schema["properties"]["action"]["enum"]
    assert actions == ["new", "open", "save", "close", "revert"]
