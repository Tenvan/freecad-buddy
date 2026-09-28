import json

import pytest

from buddy_bridge import protocol
from buddy_bridge.protocol import RpcError


def test_encode_is_one_compact_utf8_line() -> None:
    data = protocol.encode(protocol.result_message(1, {"label": "Größe"}))

    assert data.endswith(b"\n")
    assert data.count(b"\n") == 1
    assert json.loads(data) == {"jsonrpc": "2.0", "id": 1, "result": {"label": "Größe"}}


def test_decode_rejects_invalid_json() -> None:
    with pytest.raises(RpcError) as info:
        protocol.decode(b"{nope\n")

    assert info.value.code == protocol.PARSE_ERROR


def test_decode_rejects_oversized_message() -> None:
    with pytest.raises(RpcError) as info:
        protocol.decode(b"x" * (protocol.MAX_MESSAGE_BYTES + 1))

    assert info.value.code == protocol.INVALID_REQUEST


def test_parse_request_with_named_params() -> None:
    request = protocol.parse_request(
        {"jsonrpc": "2.0", "id": "a", "method": "system.ping", "params": {"x": 1}}
    )

    assert (request.id, request.method, request.params) == ("a", "system.ping", {"x": 1})


@pytest.mark.parametrize(
    ("message", "code"),
    [
        ([], protocol.INVALID_REQUEST),
        ({"jsonrpc": "1.0", "id": 1, "method": "m"}, protocol.INVALID_REQUEST),
        ({"jsonrpc": "2.0", "method": "m"}, protocol.INVALID_REQUEST),  # notification
        ({"jsonrpc": "2.0", "id": True, "method": "m"}, protocol.INVALID_REQUEST),
        ({"jsonrpc": "2.0", "id": 1}, protocol.INVALID_REQUEST),
        ({"jsonrpc": "2.0", "id": 1, "method": "m", "params": [1]}, protocol.INVALID_PARAMS),
    ],
)
def test_parse_request_rejects_invalid_messages(message: object, code: int) -> None:
    with pytest.raises(RpcError) as info:
        protocol.parse_request(message)

    assert info.value.code == code


def test_error_roundtrip_keeps_code_name_and_data() -> None:
    error = RpcError(protocol.AMBIGUOUS, "mehrdeutig", {"candidates": ["Face1", "Face2"]})
    message = protocol.error_message(7, error)

    assert message["error"]["data"]["name"] == "ambiguous"
    restored = protocol.error_from_message(message)
    assert (restored.code, restored.message, restored.data) == (
        protocol.AMBIGUOUS,
        "mehrdeutig",
        {"candidates": ["Face1", "Face2"]},
    )
