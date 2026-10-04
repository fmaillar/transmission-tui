"""Command-line entry point."""

from __future__ import annotations

import argparse
from importlib.metadata import version

from .trackers import TransmissionTUI


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="transmission-tui",
        description="Terminal interface for monitoring and controlling Transmission.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Connection:
  By default, connects to 127.0.0.1:9091.

Environment variables:
  TRANSMISSION_HOST       RPC host (default: 127.0.0.1)
  TRANSMISSION_PORT       RPC port (default: 9091)
  TRANSMISSION_USER       RPC username
  TRANSMISSION_PASSWORD   RPC password

Main keys:
  Enter   Open torrent details
  a       Add torrent
  /       Search torrent names
  f       Cycle status filter
  l       Manage files
  b       Set bandwidth limits
  m       Move torrent data
  t       Inspect trackers
  Space   Pause or resume
  v       Verify local data
  x       Remove torrent and keep data
  d       Delete torrent and data
  r       Refresh immediately
  + / -   Adjust refresh interval by 250 ms
  i       Sort by torrent ID
  u       Sort by upload rate
  D       Sort by download rate
  p       Sort by ratio
  q       Quit

Examples:
  transmission-tui

  TRANSMISSION_HOST=m710s \\
  TRANSMISSION_PORT=9091 \\
  transmission-tui

Project:
  https://github.com/fmaillar/transmission-tui
""",
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
