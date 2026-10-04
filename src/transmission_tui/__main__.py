"""Command-line entry point."""

from __future__ import annotations

import argparse
from importlib.metadata import version

from .trackers import TransmissionTUI


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="transmission-tui",
        description="Terminal interface for monitoring and controlling Transmission.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version('transmission-tui')}",
    )
    parser.parse_args()

    TransmissionTUI().run()


if __name__ == "__main__":
    main()
