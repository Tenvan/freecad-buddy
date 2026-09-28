"""Entry point executed by FreeCAD's bundled ``python.exe``: start the bridge without GUI."""

import argparse
import os
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freecad-home", required=True)
    parser.add_argument("--addon-dir", required=True)
    args, rest = parser.parse_known_args()

    bin_dir = os.path.join(args.freecad_home, "bin")
    os.add_dll_directory(bin_dir)
    sys.path[:0] = [bin_dir, os.path.join(args.freecad_home, "lib"), args.addon_dir]

    from buddy_bridge import headless

    return headless.main(rest)


if __name__ == "__main__":
    raise SystemExit(main())
