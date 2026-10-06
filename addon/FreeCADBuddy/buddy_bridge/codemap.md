# addon/FreeCADBuddy/buddy_bridge/

## Responsibility

Transport and RPC gateway running inside the FreeCAD process: a loopback, token-authenticated JSON-RPC server that routes method calls onto the Qt main thread and into `buddy_core`. It contains no modelling logic.

## Design

- Stdlib only (plus FreeCAD's `PySide` shim in `qt_dispatcher`); `protocol`, `tokens`, `client` and `server` do not import FreeCAD and are usable outside it.
- `protocol.py`: JSON-RPC 2.0 over newline-delimited messages (`encode`/`decode`/`parse_request`, `MAX_MESSAGE_BYTES`), `RpcError`, application error codes 1001-1009 (`ERROR_NAMES`).
- `server.py`: `BridgeServer`, thread-per-connection socket server; loopback-only bind, `MAX_CLIENTS`, handshake (`auth.hello` with token) before any call.
- `tokens.py`: token file handling in `buddy_home()` (`load_or_create_token`, `read_token`, constant-time `tokens_match`).
- `dispatch.py`: `Dispatcher` protocol (`call`/`post`) with `InlineDispatcher` (calling thread, serialised; headless/tests).
- `qt_dispatcher.py`: `QtMainThreadDispatcher`, marshals jobs via a queued Qt signal into a `Future`; rejects with `BUSY_USER_TRANSACTION` when the GUI is busy (`busy_check`).
- `registry.py`: `Method`/`MethodRegistry`; `execute` is the single execution path (parameter check, stream snapshot, call, `stream.record` unless the name starts with `NOT_RECORDED`); `invoke` adds the dispatcher hop, timeout and mapping of `CoreError`/exceptions to `RpcError`.
- `methods.py`: `METHODS` table (name -> `buddy_core` function plus options such as `main_thread`, `timeout`) and `build_registry`; `python.execute` and addon install are registered only with opt-in.
- `replay.py`: `replay` rebuilds a document from a design stream through the same registry; allowlist `REPLAYABLE`, exclusion `NEVER_REPLAYED`.
- `service.py`: `BridgeService` lifecycle (token, registry, server), FreeCAD preferences (port, autostart, opt-ins), console logging via `dispatcher.post`, process-wide `get_service()` choosing Qt or inline dispatcher.
- `commands.py`: GUI commands (start/stop/status, settings toggles), `register`, `autostart`.
- `headless.py`: CLI entry (`main`) running the bridge without GUI, prints `BRIDGE_READY <port>`.
- `client.py`: `BridgeClient`, synchronous socket client with handshake; `BridgeConnectionError` tells whether the request was already sent.

## Flow

1. FreeCAD starts the bridge (`commands.autostart`/`_start` or `headless.main`) -> `service.get_service()` -> `BridgeService.start` loads the token and calls `methods.build_registry`.
2. `BridgeServer.start` opens a loopback socket; `_accept_loop` spawns a `buddy-bridge-conn` thread per client.
3. `_handshake` requires `auth.hello` with a matching token (`tokens_match`), else `UNAUTHORIZED` and disconnect.
4. `_serve_connection` reads one line at a time; `_handle_line` runs `protocol.decode` and `parse_request`.
5. `MethodRegistry.invoke` validates the parameters against the function signature, then `dispatcher.call` runs `execute` on the Qt main thread (or inline for `main_thread=False`, e.g. `system.ping`).
6. `execute` snapshots the stream, calls the `buddy_core` function, converts `ToolResult` to a dict and records the call via `stream.record`.
7. Errors become `RpcError` (`CoreError` name -> error code); `_send` writes the `result_message` or `error_message` as one JSON line.

## Integration

- Consumed by: `buddy_server.bridge` (`BridgeClient`, `BridgeConnectionError`, `RpcError`, `UNAUTHORIZED`), `buddy_server.app`, `buddy_server.config` (`tokens`), `buddy_server.tools.base` (`RpcError`); `addon/FreeCADBuddy/InitGui.py` loads `buddy_bridge.commands`.
- Depends on: `buddy_core` (`stream`, `documents`, `errors`, `result`, `transaction` and the modelling modules wired in `methods.py`), `FreeCAD`/`FreeCADGui`, `PySide`.
