# transmission-tui

A lightweight, keyboard-driven terminal interface for monitoring and managing a
[Transmission](https://transmissionbt.com/) daemon.

```text
Transmission daemon  <-- RPC -->  transmission-tui
```

`transmission-tui` is designed for terminal-centred and remote workflows. It
provides a persistent interactive view of a headless Transmission instance
without requiring a browser or an additional web frontend.

## Features

- Live torrent monitoring with one-second refreshes
- Stable cursor position and scroll state during updates
- Aggregate size, upload, download, activity, and ratio statistics
- Torrent search, status filters, and sortable columns
- Detailed transfer, peer, location, history, and magnet information
- Add torrents from magnet links or HTTP(S) `.torrent` URLs
- Pause, resume, verify, remove, or permanently delete torrents
- Explicit confirmation before deleting downloaded data
- Per-file wanted state and priority management
- Per-torrent upload and download bandwidth limits
- Relocation of torrent data to another absolute path
- Tracker diagnostics, announce results, and manual reannounce
- Context-sensitive keyboard shortcut bars

## Requirements

- Python 3.11 or later
- A reachable Transmission RPC endpoint

The application depends only on
[Textual](https://textual.textualize.io/) and
[transmission-rpc](https://github.com/Trim21/transmission-rpc).

## Installation

Install the current version directly from GitHub with
[uv](https://docs.astral.sh/uv/):

```bash
uv tool install git+https://github.com/fmaillar/transmission-tui.git
```

To install from a local clone:

```bash
git clone https://github.com/fmaillar/transmission-tui.git
cd transmission-tui
uv tool install .
```

The `transmission-tui` command is then available in your shell.

## Usage

By default, the application connects to `127.0.0.1:9091`:

```bash
transmission-tui
```

Connection settings are configured through environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `TRANSMISSION_HOST` | `127.0.0.1` | RPC server hostname or address |
| `TRANSMISSION_PORT` | `9091` | RPC server port |
| `TRANSMISSION_USER` | unset | RPC username |
| `TRANSMISSION_PASSWORD` | unset | RPC password |

For a remote daemon:

```bash
TRANSMISSION_HOST=server.example.net \
TRANSMISSION_PORT=9091 \
transmission-tui
```

With RPC authentication enabled:

```bash
TRANSMISSION_USER=user \
TRANSMISSION_PASSWORD=secret \
transmission-tui
```

## Keyboard controls

### Main view

| Key | Action |
| --- | --- |
| `Enter` | Open torrent details |
| `a` | Add a torrent |
| `/` | Search torrent names |
| `f` | Cycle the status filter |
| `l` | Manage files |
| `b` | Set bandwidth limits |
| `m` | Move torrent data |
| `t` | Inspect trackers |
| `Space` | Pause or resume |
| `v` | Verify local data |
| `x` | Remove the torrent and keep its data |
| `d` | Delete the torrent and its data |
| `r` | Refresh immediately |
| `i` | Sort by torrent ID |
| `u` | Sort by upload rate |
| `D` | Sort by download rate |
| `p` | Sort by ratio |
| `q` | Quit |

Subview shortcut bars display only the actions that apply to the current view.
In the file view, `w` toggles whether a file is wanted and `1`, `2`, and
`3` set low, normal, and high priority. In the tracker view, `a`
requests a manual reannounce.

## Security

Do not expose the Transmission RPC port directly to the public Internet. Prefer
a private network, VPN, or SSH tunnel, and enable RPC authentication when the
daemon is reachable from another machine.

The password is read from the process environment. Avoid placing credentials in
shell history or committing them to configuration files.

## Development

Create the locked development environment and run the application from the
working tree:

```bash
git clone https://github.com/fmaillar/transmission-tui.git
cd transmission-tui
uv sync
uv run transmission-tui
```

The source is organised as a small Python package under
`src/transmission_tui/`. Textual provides the interface and event loop,
while `transmission-rpc` handles communication with the daemon.

## Project status

Version 0.2.0 turns the original read-only monitor into a practical Transmission
management interface. The project is usable for day-to-day administration but
is still evolving; interfaces and behaviour may change before version 1.0.

See [CHANGELOG.md](CHANGELOG.md) for release details.

## License

This project is released under the [MIT License](LICENSE).
