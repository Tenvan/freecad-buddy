"""Run the bridge without GUI (FreeCAD's python.exe or FreeCADCmd): automation and E2E tests.

Prints ``BRIDGE_READY <port>`` once listening, then serves until stdin closes or it is killed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=9876)
    parser.add_argument("--token-file", type=Path, default=None)
    args = parser.parse_args(argv)

    import FreeCAD  # noqa: F401  (initialises the application)

    from buddy_bridge.dispatch import InlineDispatcher
    from buddy_bridge.service import BridgeService

    # Installing needs the confirmation dialog, so a headless bridge never offers it – whatever the
    # user's FreeCAD preferences say.
    service = BridgeService(
        InlineDispatcher(), token_path=args.token_file, port=args.port, allow_addon_install=False
    )
    service.start()
    print(f"BRIDGE_READY {service.port}", flush=True)
    try:
        sys.stdin.read()  # parent closes stdin (or terminates us) to stop
    except KeyboardInterrupt:
        pass
    finally:
        service.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
