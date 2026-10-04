"""Command-line entry point."""

from __future__ import annotations

import argparse
from importlib.metadata import version

from transmission_rpc import TransmissionError

from .trackers import TransmissionTUI


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="transmission-tui",
        description="Terminal interface for monitoring and controlling Transmission.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Connection:
  By default, connects to 127.0.0.1:9091.

Configuration file:
  ~/.config/transmission-tui/config.toml

Environment variables:
  TRANSMISSION_HOST               RPC host (default: 127.0.0.1)
  TRANSMISSION_PORT               RPC port (default: 9091)
  TRANSMISSION_REFRESH_INTERVAL   refresh interval in seconds
  TRANSMISSION_USER               RPC username
  TRANSMISSION_PASSWORD           RPC password

Environment variables override config.toml.

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
    parser.parse_args(argv)

    try:
        TransmissionTUI().run()
    except ValueError as exc:
        parser.exit(2, f"configuration error: {exc}\n")
    except TransmissionError as exc:
        parser.exit(1, f"RPC error: {exc}\n")


if __name__ == "__main__":
    main()
