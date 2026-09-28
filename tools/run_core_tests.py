"""Entry point executed by FreeCAD's bundled ``python.exe`` (not the project venv).

Prepares ``sys.path`` so that FreeCAD, the addon packages and pytest (borrowed from the
project venv, pure Python only) are importable, then hands over to pytest.
"""

import argparse
import os
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freecad-home", required=True)
    parser.add_argument("--site-packages", required=True)
    parser.add_argument("--addon-dir", required=True)
    args, rest = parser.parse_known_args()
    pytest_args = rest[1:] if rest[:1] == ["--"] else rest

    bin_dir = os.path.join(args.freecad_home, "bin")
    os.add_dll_directory(bin_dir)
    # FreeCAD first, addon second, venv last: FreeCAD's own packages must win.
    sys.path[:0] = [bin_dir, os.path.join(args.freecad_home, "lib"), args.addon_dir]
    sys.path.append(args.site_packages)

    import FreeCAD  # noqa: F401  (initialises the application before any test module imports)
    import pytest

    # FreeCAD's init puts the user Mod dirs in front; an installed FreeCADBuddy (e.g. a junction to the
    # main checkout) would then shadow the checkout under test. Put ours first again and drop stale imports.
    sys.path.insert(0, args.addon_dir)
    for name in [m for m in sys.modules if m.split(".")[0] in ("buddy_core", "buddy_bridge")]:
        del sys.modules[name]

    return pytest.main(["-p", "no:cacheprovider", *pytest_args])


if __name__ == "__main__":
    raise SystemExit(main())
