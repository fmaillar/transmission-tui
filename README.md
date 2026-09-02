# transmission-tui

A lightweight terminal user interface for monitoring and controlling a Transmission daemon.

## Features

- Live torrent list refreshed every second without losing cursor position
- Size, uploaded data, current download/upload rates and ratio
- Aggregate totals in the header
- Search and status filters
- Sort by ID, upload rate, download rate or ratio
- Torrent details view
- Add torrents from magnet links or HTTP(S) `.torrent` URLs
- Pause/resume and verification
- Remove torrents while keeping data, or delete torrent and data with confirmation
- Per-torrent file selection and priority management
- Per-torrent upload/download bandwidth limits
- Move torrent data to another absolute path
- Tracker diagnostics and manual reannounce
- Context-sensitive shortcut bars

## Requirements

- Python 3.11+
- A reachable Transmission RPC endpoint

## Installation

With `uv`:

```bash
uv tool install .
```

For development:

```bash
uv sync
uv run transmission-tui
```

## Usage

By default the application connects to `localhost:9091`:

```bash
transmission-tui
```

Environment variables can override the RPC endpoint:

```bash
TRANSMISSION_HOST=localhost \
TRANSMISSION_PORT=9091 \
transmission-tui
```

If authentication is enabled:

```bash
TRANSMISSION_USER=user \
TRANSMISSION_PASSWORD=secret \
transmission-tui
```

## Main keys

- `Enter`: torrent details
- `a`: add torrent
- `/`: search torrents
- `f`: cycle status filter
- `l`: files
- `b`: bandwidth limits
- `m`: move data
- `t`: trackers
- `Space`: pause/resume
- `v`: verify
- `x`: remove torrent and keep data
- `d`: delete torrent and data
- `r`: refresh immediately
- `i`: sort by torrent ID
- `u`: sort by upload rate
- `D`: sort by download rate
- `p`: sort by ratio
- `q`: quit

Subview shortcut bars only show actions relevant to the current view.

## Version 0.2.0

Version 0.2.0 turns the initial read-only monitor into a practical Transmission management TUI. It adds torrent lifecycle controls, file management, bandwidth limits, data relocation, search/filtering, tracker diagnostics and a cleaner context-sensitive interface.

## License

MIT
