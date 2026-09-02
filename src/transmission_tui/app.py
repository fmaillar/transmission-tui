"""Textual application for transmission-tui."""

from __future__ import annotations

from operator import attrgetter

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.coordinate import Coordinate
from textual.screen import ModalScreen, Screen
from textual.widgets import DataTable, Footer, Header, Input, Static

from .format import human_bytes, human_rate
from .rpc import AddedTorrent, TorrentDetails, TorrentSnapshot, TransmissionClient


class AddTorrentScreen(ModalScreen[AddedTorrent | None]):
    """Dialog used to add a torrent from an URL or magnet link."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    CSS = """
    AddTorrentScreen { align: center middle; }
    #add-box {
        width: 85%;
        max-width: 110;
        height: auto;
        border: round $accent;
        padding: 1 2;
        background: $surface;
    }
    #add-title {
        height: 1;
        margin-bottom: 1;
        text-style: bold;
    }
    #add-error {
        height: auto;
        min-height: 1;
        margin-top: 1;
        color: $error;
    }
    """

    def __init__(self, rpc: TransmissionClient) -> None:
        super().__init__()
        self.rpc = rpc

    def compose(self) -> ComposeResult:
        with Vertical(id="add-box"):
            yield Static(
                "Add torrent — paste an HTTP(S) .torrent URL or magnet link",
                id="add-title",
            )
            yield Input(
                placeholder="https://…/file.torrent  or  magnet:?xt=urn:btih:…",
                id="add-source",
            )
            yield Static("Enter: add   Esc: cancel", id="add-hint")
            yield Static("", id="add-error")

    def on_mount(self) -> None:
        self.query_one("#add-source", Input).focus()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        try:
            added = self.rpc.add_torrent(event.value)
        except Exception as exc:
            self.query_one("#add-error", Static).update(f"Error: {exc}")
            return
        self.dismiss(added)


class RemoveTorrentScreen(ModalScreen[bool]):
    """Confirmation before removing a torrent, optionally with its data."""

    BINDINGS = [
        ("y", "confirm", "Confirm"),
        ("n", "cancel", "Cancel"),
        ("escape", "cancel", "Cancel"),
    ]

    CSS = """
    RemoveTorrentScreen { align: center middle; }
    #remove-box {
        width: 80%;
        max-width: 100;
        height: auto;
        border: round $warning;
        padding: 1 2;
        background: $surface;
    }
    #remove-title {
        text-style: bold;
        margin-bottom: 1;
    }
    #remove-name { margin-bottom: 1; }
    #remove-warning {
        color: $warning;
        margin-bottom: 1;
    }
    """

    def __init__(
        self, torrent_id: int, torrent_name: str, *, delete_data: bool
    ) -> None:
        super().__init__()
        self.torrent_id = torrent_id
        self.torrent_name = torrent_name
        self.delete_data = delete_data

    def compose(self) -> ComposeResult:
        if self.delete_data:
            title = "Delete torrent and data?"
            warning = (
                "This removes the torrent from Transmission AND deletes its "
                "downloaded files."
            )
            confirm = "y: delete permanently   n / Esc: cancel"
        else:
            title = "Remove torrent from Transmission?"
            warning = "Downloaded files will be kept on disk."
            confirm = "y: remove torrent   n / Esc: cancel"

        with Vertical(id="remove-box"):
            yield Static(title, id="remove-title")
            yield Static(
                f"Torrent {self.torrent_id}: {self.torrent_name}",
                id="remove-name",
                markup=False,
            )
            yield Static(warning, id="remove-warning")
            yield Static(confirm)

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


class TorrentDetailScreen(Screen[None]):
    """Read-only detail view for a single torrent."""

    BINDINGS = [
        ("escape", "back", "Back"),
        ("q", "back", "Back"),
    ]

    CSS = """
    #details {
        height: 1fr;
        padding: 1 2;
        overflow-y: auto;
        overflow-x: auto;
    }
    """

    def __init__(self, details: TorrentDetails) -> None:
        super().__init__()
        self.details = details

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(self._render_details(), id="details", markup=False)
        yield Footer()

    def action_back(self) -> None:
        self.app.pop_screen()

    def _render_details(self) -> str:
        torrent = self.details
        return "\n".join(
            (
                f"Torrent {torrent.id}: {torrent.name}",
                "",
                "TRANSFER",
                f"  Status:             {torrent.status}",
                f"  Progress:           {torrent.progress:.2f}%",
                f"  Total size:         {human_bytes(torrent.total_size)}",
                f"  Size when done:     {human_bytes(torrent.size_when_done)}",
                f"  Have valid:         {human_bytes(torrent.have_valid)}",
                f"  Downloaded:         {human_bytes(torrent.downloaded)}",
                f"  Uploaded:           {human_bytes(torrent.uploaded)}",
                f"  Ratio:              {torrent.ratio:.2f}",
                f"  Download speed:     {human_rate(torrent.rate_down)}",
                f"  Upload speed:       {human_rate(torrent.rate_up)}",
                f"  ETA:                {_human_eta(torrent.eta)}",
                "",
                "PEERS",
                f"  Connected:          {torrent.peers_connected}",
                f"  Downloading from us:{torrent.peers_downloading:>4}",
                f"  Uploading to us:    {torrent.peers_uploading:>4}",
                f"  Webseeds active:    {torrent.webseeds_sending:>4}",
                "",
                "LOCATION",
                f"  Download directory: {torrent.download_dir}",
                f"  Hash:               {torrent.hash_string}",
                "",
                "HISTORY",
                f"  Added:              {torrent.added_date}",
                f"  Started:            {torrent.start_date}",
                f"  Completed:          {torrent.done_date}",
                f"  Last activity:      {torrent.activity_date}",
                "",
                "ORIGIN",
                f"  Creator:            {torrent.creator or '-'}",
                f"  Comment:            {torrent.comment or '-'}",
                "",
                "MAGNET",
                f"  {torrent.magnet_link or '-'}",
            )
        )


def _human_eta(seconds: int) -> str:
    if seconds < 0:
        return "Unknown"
    if seconds == 0:
        return "Done"
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)
    if days:
        return f"{days}d {hours}h {minutes}m"
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


class TransmissionTUI(App[None]):
    TITLE = "Transmission TUI"
    SUB_TITLE = "monitor and control"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("a", "add_torrent", "Add"),
        ("space", "toggle_pause", "Pause/Resume"),
        ("v", "verify_torrent", "Verify"),
        ("x", "remove_torrent", "Remove"),
        ("d", "delete_torrent", "Delete data"),
        ("r", "refresh_now", "Refresh"),
        ("i", "sort_id", "Sort ID"),
        ("u", "sort_up", "Sort Up"),
        ("D", "sort_down", "Sort Down"),
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
        self._row_order: list[str] = []

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
            "ID",
            "Done",
            "Size",
            "Uploaded",
            "Down",
            "Up",
            "Ratio",
            "Status",
            "Name",
        )
        self.set_interval(1.0, self.refresh_data)
        self.refresh_data()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Open details when Enter is pressed on a torrent row."""
        try:
            torrent_id = int(str(event.row_key.value))
            details = self.rpc.torrent_details(torrent_id)
        except Exception as exc:
            self.query_one("#summary", Static).update(f"RPC error: {exc}")
            return
        self.push_screen(TorrentDetailScreen(details))

    def _selected_torrent(self) -> tuple[int, str, str] | None:
        table = self.query_one("#table", DataTable)
        if not table.row_count:
            return None
        try:
            row = table.get_row_at(table.cursor_row)
            return int(str(row[0])), str(row[8]), str(row[7])
        except (IndexError, KeyError, TypeError, ValueError):
            return None

    def action_add_torrent(self) -> None:
        self.push_screen(AddTorrentScreen(self.rpc), self._torrent_added)

    def _torrent_added(self, added: AddedTorrent | None) -> None:
        if added is None:
            return
        self.refresh_data()
        self.query_one("#summary", Static).update(
            f"Added torrent {added.id}: {added.name}"
        )

    def action_toggle_pause(self) -> None:
        selected = self._selected_torrent()
        if selected is None:
            return
        torrent_id, torrent_name, status = selected
        try:
            if status == "stopped":
                self.rpc.start_torrent(torrent_id)
                message = f"Resumed torrent {torrent_id}: {torrent_name}"
            else:
                self.rpc.stop_torrent(torrent_id)
                message = f"Paused torrent {torrent_id}: {torrent_name}"
        except Exception as exc:
            self.query_one("#summary", Static).update(f"RPC error: {exc}")
            return
        self.refresh_data()
        self.query_one("#summary", Static).update(message)

    def action_verify_torrent(self) -> None:
        selected = self._selected_torrent()
        if selected is None:
            return
        torrent_id, torrent_name, _ = selected
        try:
            self.rpc.verify_torrent(torrent_id)
        except Exception as exc:
            self.query_one("#summary", Static).update(f"RPC error: {exc}")
            return
        self.refresh_data()
        self.query_one("#summary", Static).update(
            f"Verification requested for torrent {torrent_id}: {torrent_name}"
        )

    def action_remove_torrent(self) -> None:
        self._confirm_remove(delete_data=False)

    def action_delete_torrent(self) -> None:
        self._confirm_remove(delete_data=True)

    def _confirm_remove(self, *, delete_data: bool) -> None:
        selected = self._selected_torrent()
        if selected is None:
            return
        torrent_id, torrent_name, _ = selected
        self.push_screen(
            RemoveTorrentScreen(
                torrent_id, torrent_name, delete_data=delete_data
            ),
            lambda confirmed: self._torrent_remove_confirmed(
                torrent_id,
                torrent_name,
                delete_data,
                confirmed,
            ),
        )

    def _torrent_remove_confirmed(
        self,
        torrent_id: int,
        torrent_name: str,
        delete_data: bool,
        confirmed: bool,
    ) -> None:
        if not confirmed:
            return
        try:
            self.rpc.remove_torrent(torrent_id, delete_data=delete_data)
        except Exception as exc:
            self.query_one("#summary", Static).update(f"RPC error: {exc}")
            return

        self.refresh_data()
        if delete_data:
            message = f"Deleted torrent {torrent_id} and its data: {torrent_name}"
        else:
            message = f"Removed torrent {torrent_id}; data kept: {torrent_name}"
        self.query_one("#summary", Static).update(message)

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

    @staticmethod
    def _row_values(torrent: TorrentSnapshot) -> tuple[str, ...]:
        return (
            str(torrent.id),
            f"{torrent.progress:.0f}%",
            human_bytes(torrent.size),
            human_bytes(torrent.uploaded),
            human_rate(torrent.rate_down),
            human_rate(torrent.rate_up),
            f"{torrent.ratio:.2f}",
            torrent.status,
            torrent.name,
        )

    def _update_table(self, torrents: list[TorrentSnapshot]) -> None:
        table = self.query_one("#table", DataTable)
        new_order = [str(torrent.id) for torrent in torrents]

        # Normal refresh: update cells in place to keep the viewport stable.
        if table.row_count == len(torrents) and new_order == self._row_order:
            for row_index, torrent in enumerate(torrents):
                for column_index, value in enumerate(self._row_values(torrent)):
                    coordinate = Coordinate(row_index, column_index)
                    if table.get_cell_at(coordinate) != value:
                        table.update_cell_at(coordinate, value)
            return

        # Structural refresh after add/remove/sort: rebuild while preserving
        # the selected torrent and viewport.
        selected_id: str | None = None
        saved_scroll_y = table.scroll_y
        if table.row_count:
            try:
                selected_id = str(table.get_row_at(table.cursor_row)[0])
            except (IndexError, KeyError):
                pass

        table.clear(columns=False)
        selected_row: int | None = None

        for row_index, torrent in enumerate(torrents):
            torrent_id = str(torrent.id)
            table.add_row(*self._row_values(torrent), key=torrent_id)
            if torrent_id == selected_id:
                selected_row = row_index

        self._row_order = new_order

        if selected_row is not None:
            table.move_cursor(row=selected_row)

        self.call_after_refresh(
            lambda: table.scroll_to(y=saved_scroll_y, animate=False)
        )
