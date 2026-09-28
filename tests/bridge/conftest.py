from collections.abc import Iterator

import pytest

from buddy_bridge.dispatch import InlineDispatcher
from buddy_bridge.methods import build_registry
from buddy_bridge.registry import MethodRegistry
from buddy_bridge.server import BridgeServer

TOKEN = "test-token"


@pytest.fixture
def registry() -> MethodRegistry:
    return build_registry()


@pytest.fixture
def server(registry: MethodRegistry) -> Iterator[BridgeServer]:
    bridge = BridgeServer(registry, InlineDispatcher(), TOKEN, port=0)
    bridge.start()
    yield bridge
    bridge.stop()
