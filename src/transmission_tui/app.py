"""Textual application for transmission-tui."""

from __future__ import annotations

from operator import attrgetter

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Footer, Header, Static

from .format import human_bytes, human_rate
from .rpc import TorrentSnapshot, TransmissionClient


class TransmissionTUI(App[None]):
    TITLE = "Transmission TUI"
    SUB_TITLE = "read-only monitor"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh_now", "Refresh"),
        ("i", "sort_id", "Sort ID"),
        ("u", "sort_up", "Sort Up"),
        ("d", "sort_down", "Sort Down"),
        ("p", "sort_ratio", "Sort Ratio"),
    ]

    CSS = """
    Screen { layout: vertical; }
    #summary { height: 3; padding: 0 1; }
    #table { height: 1fr; }
    """

    def __init__(self) -> None:
        super().__init__()
        self.rpc = TransmissionClient()
        self.sort_key = "id"
        self.sort_reverse = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Static("Connecting to Transmission...", id="summary")
            yield DataTable(id="table", zebra_stripes=True)
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#table", DataTable)
        table.cursor_type = "row"
        table.add_columns(
            "ID", "Done", "Size", "Uploaded", "Down", "Up", "Ratio", "Status", "Name"
        )
        self.set_interval(1.0, self.refresh_data)
        self.refresh_data()

    def action_refresh_now(self) -> None:
        self.refresh_data()

    def action_sort_id(self) -> None:
        self._set_sort("id")

    def action_sort_up(self) -> None:
        self._set_sort("rate_up", reverse=True)

    def action_sort_down(self) -> None:
        self._set_sort("rate_down", reverse=True)

    def action_sort_ratio(self) -> None:
        self._set_sort("ratio", reverse=True)

    def _set_sort(self, key: str, reverse: bool = False) -> None:
        if self.sort_key == key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_key = key
            self.sort_reverse = reverse
        self.refresh_data()

    def refresh_data(self) -> None:
        try:
            torrents = self.rpc.torrents()
        except Exception as exc:  # RPC/network errors must not kill the TUI
            self.query_one("#summary", Static).update(f"RPC error: {exc}")
            return

        torrents.sort(key=attrgetter(self.sort_key), reverse=self.sort_reverse)
        self._update_summary(torrents)
        self._update_table(torrents)

    def _update_summary(self, torrents: list[TorrentSnapshot]) -> None:
        size = sum(t.size for t in torrents)
        uploaded = sum(t.uploaded for t in torrents)
        down = sum(t.rate_down for t in torrents)
        up = sum(t.rate_up for t in torrents)
        ratio = uploaded / size if size else 0.0
        active = sum(bool(t.rate_down or t.rate_up) for t in torrents)
        text = (
            f"Torrents: {len(torrents)}  Active: {active}  "
            f"Size: {human_bytes(size)}  Uploaded: {human_bytes(uploaded)}  "
            f"Ratio: {ratio:.2f}\nDown: {human_rate(down)}  Up: {human_rate(up)}  "
            f"Sort: {self.sort_key}{' desc' if self.sort_reverse else ' asc'}"
        )
        self.query_one("#summary", Static).update(text)

    def _update_table(self, torrents: list[TorrentSnapshot]) -> None:
        table = self.query_one("#table", DataTable)

        # DataTable.clear() resets the cursor to the first row. Remember the
        # selected torrent ID so automatic refreshes do not fight navigation.
        selected_id: str | None = None
        if table.row_count:
            try:
                selected_id = str(table.get_row_at(table.cursor_row)[0])
            except (IndexError, KeyError):
                pass

        table.clear(columns=False)
        selected_row: int | None = None

        for row_index, torrent in enumerate(torrents):
            torrent_id = str(torrent.id)
            table.add_row(
                torrent_id,
                f"{torrent.progress:.0f}%",
                human_bytes(torrent.size),
                human_bytes(torrent.uploaded),
                human_rate(torrent.rate_down),
                human_rate(torrent.rate_up),
                f"{torrent.ratio:.2f}",
                torrent.status,
                torrent.name,
                key=torrent_id,
            )
            if torrent_id == selected_id:
                selected_row = row_index

        if selected_row is not None:
            table.move_cursor(row=selected_row)
