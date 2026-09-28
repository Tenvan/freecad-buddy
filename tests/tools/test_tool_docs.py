"""AC-15: every tool is documented with schema and example, and docs/tools.md is current."""

import asyncio

import gen_tool_docs


def test_every_tool_has_an_example_and_docs_are_current() -> None:
    tools = asyncio.run(gen_tool_docs._tools())
    names = {tool.name for tool in tools}

    assert len(names) <= 40
    assert names == set(gen_tool_docs.EXAMPLES), sorted(names ^ set(gen_tool_docs.EXAMPLES))
    assert gen_tool_docs.TARGET.read_text(encoding="utf-8") == gen_tool_docs.render(tools), (
        "docs/tools.md veraltet: uv run python tools/gen_tool_docs.py"
    )
