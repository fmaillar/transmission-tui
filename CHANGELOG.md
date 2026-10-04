# Changelog

## Unreleased

## 1.0.0 — 2026-10-04

### Added

- Persistent XDG configuration in `~/.config/transmission-tui/config.toml`
- Configurable RPC host, port, and refresh interval
- Runtime refresh interval adjustment in 250 ms steps with `+` and `-`
- Useful `--help` output and `--version`
- Clean startup diagnostics for invalid configuration and RPC failures
- GitHub Actions CI across Python 3.11, 3.13, and 3.14
- Ruff linting and mypy type checking

### Improved

- Remote Transmission usage over private networks such as Tailscale
- RPC credentials can remain in `~/.netrc` while connection settings stay in the XDG config
- Runtime RPC connection loss is reported in the TUI without crashing
- Compatibility and local validation policy documented in the README

### Fixed

- Let `Enter` submit the Add torrent dialog instead of opening torrent details
- Refresh interval controls now follow the displayed value: `+` increases the interval and `-` decreases it
- Type-safety issues found by mypy in configuration, RPC conversion helpers, and tracker views

## 0.2.0 — 2026-09-02

### Added

- Torrent details screen
- Add torrents from magnet links and HTTP(S) `.torrent` URLs
- Pause/resume and verification controls
- Remove torrent while keeping data
- Delete torrent and downloaded data with confirmation
- Torrent search and status filters
- Per-file wanted state and priority management
- Per-torrent upload/download bandwidth limits
- Torrent data relocation
- Tracker diagnostics and manual reannounce
- Context-sensitive shortcut bars with a two-line main footer

### Improved

- Preserve torrent selection and scroll position during live refreshes
- Update table cells in place to avoid cursor jumps
- Resize speed columns during live updates
- Cleaner contextual navigation in Details and Trackers

## 0.1.0

- Initial read-only Transmission monitoring TUI
