from typing import Any

import FreeCAD
import pytest

from buddy_bridge import protocol
from buddy_bridge.client import BridgeClient
from buddy_bridge.dispatch import InlineDispatcher
from buddy_bridge.methods import build_registry
from buddy_bridge.protocol import RpcError
from buddy_bridge.server import BridgeServer

from .conftest import TOKEN


@pytest.fixture
def client(server: BridgeServer) -> Any:
    with BridgeClient(TOKEN, port=server.port, request_timeout=30) as bridge_client:
        yield bridge_client
    for name in list(FreeCAD.listDocuments()):
        FreeCAD.closeDocument(name)


def test_core_errors_map_to_rpc_codes(client: BridgeClient) -> None:
    client.call("document.new", {"name": "Errors"})

    with pytest.raises(RpcError) as info:
        client.call("sketch.analyze", {"sketch": "Nope"})

    assert info.value.code == protocol.NOT_FOUND
    assert info.value.name == "not_found"


def test_tool_results_are_serialised(client: BridgeClient) -> None:
    client.call("document.new", {"name": "Serialised"})
    result = client.call("parameters.set", {"parameters": {"Width": 10}})

    assert result["ok"] is True
    assert result["parameters"][0]["name"] == "Width"


def test_execute_python_needs_opt_in_on_the_bridge(client: BridgeClient) -> None:
    with pytest.raises(RpcError) as info:
        client.call("python.execute", {"code": "result = 1"})

    assert info.value.code == protocol.METHOD_NOT_FOUND


@pytest.fixture
def python_client() -> Any:
    bridge = BridgeServer(build_registry(allow_python=True), InlineDispatcher(), TOKEN, port=0)
    bridge.start()
    try:
        with BridgeClient(TOKEN, port=bridge.port, request_timeout=30) as bridge_client:
            yield bridge_client
    finally:
        bridge.stop()
        for name in list(FreeCAD.listDocuments()):
            FreeCAD.closeDocument(name)


def test_execute_python_runs_as_one_transaction(python_client: BridgeClient) -> None:
    python_client.call("document.new", {"name": "Python"})
    result = python_client.call(
        "python.execute", {"code": "doc.addObject('App::FeaturePython', 'Probe')\nprint('hi')\nresult = 42"}
    )
    tree = python_client.call("document.tree")

    assert result == {"stdout": "hi\n", "result": 42}
    assert tree["undo"]["names"][0] == "Python-Skript"


def test_exit_in_script_is_rolled_back_and_connection_survives(python_client: BridgeClient) -> None:
    python_client.call("document.new", {"name": "Exit"})

    with pytest.raises(RpcError) as info:
        python_client.call("python.execute", {"code": "doc.addObject('App::FeaturePython', 'X')\nexit()"})

    assert info.value.code == protocol.VALIDATION
    assert python_client.call("system.ping")["pong"] is True
    assert not [o for o in FreeCAD.getDocument("Exit").Objects if o.Name == "X"]


def test_screenshot_without_gui_is_unsupported(client: BridgeClient) -> None:
    client.call("document.new", {"name": "Headless"})

    with pytest.raises(RpcError) as info:
        client.call("view.screenshot")

    assert info.value.code == protocol.UNSUPPORTED


def test_set_view_without_gui_is_unsupported(client: BridgeClient) -> None:
    client.call("document.new", {"name": "HeadlessView"})

    with pytest.raises(RpcError) as info:
        client.call("view.set", {"view": "iso"})
    assert info.value.code == protocol.UNSUPPORTED
