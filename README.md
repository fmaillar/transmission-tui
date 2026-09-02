# transmission-tui

A lightweight terminal user interface for monitoring a Transmission daemon.

## Features

- Live torrent list refreshed every second
- Size, uploaded data, current download/upload rates and ratio
- Aggregate totals in the header
- Sortable table
- Read-only first release: no destructive actions

## Requirements

- Python 3.11+
- A reachable Transmission RPC endpoint

## Installation

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
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

## Keys

- `q`: quit
- `r`: refresh immediately
- `i`: sort by torrent ID
- `u`: sort by upload rate
- `d`: sort by download rate
- `p`: sort by ratio

## Scope

Version 0.1 is intentionally read-only. Pause/resume, verification and removal can be added later once the monitoring layer is stable.

## License

MIT
