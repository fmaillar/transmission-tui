"""Tracker diagnostics and reannounce support for transmission-tui."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from .app import TorrentDetailScreen as BaseTorrentDetailScreen
from .location import TransmissionTUI as BaseTransmissionTUI
from .rpc import TransmissionClient as BaseTransmissionClient


@dataclass(frozen=True, slots=True)
class TrackerSnapshot:
    id: int
    tier: int
    host: str
    state: str
    peers: int
    last_announce: str
    next_announce: str
    result: str
    announce: str


_ANNOUNCE_STATES = {
    0: "inactive",
    1: "waiting",
    2: "queued",
    3: "active",
}


class TrackerTransmissionClient(BaseTransmissionClient):
    """Transmission client with tracker diagnostics and reannounce support."""

    def torrent_trackers(self, torrent_id: int) -> tuple[str, list[TrackerSnapshot]]:
        torrent = self._client.get_torrent(
            torrent_id,
            arguments=("name", "trackers", "trackerStats"),
        )
        tracker_defs = _value(torrent, "trackers", default=[]) or []
        tiers = {
            _int(_value(tracker, "id", default=-1), default=-1): _int(
                _value(tracker, "tier", default=0)
            )
            for tracker in tracker_defs
        }

        snapshots: list[TrackerSnapshot] = []
        tracker_stats = _value(torrent, "tracker_stats", "trackerStats", default=[]) or []
        for tracker in tracker_stats:
            tracker_id = _int(_value(tracker, "id", default=-1), default=-1)
            state_value = _int(
                _value(tracker, "announce_state", "announceState", default=0)
            )
            succeeded = bool(
                _value(
                    tracker,
                    "last_announce_succeeded",
                    "lastAnnounceSucceeded",
                    default=False,
                )
            )
            result = _str(
                _value(
                    tracker,
                    "last_announce_result",
                    "lastAnnounceResult",
                    default="",
                )
            )
            if succeeded and not result:
                result = "success"
            elif not result:
                result = "-"

            snapshots.append(
                TrackerSnapshot(
                    id=tracker_id,
                    tier=tiers.get(tracker_id, 0),
                    host=_str(_value(tracker, "host", default="")),
                    state=_ANNOUNCE_STATES.get(state_value, str(state_value)),
                    peers=_int(
                        _value(
                            tracker,
                            "last_announce_peer_count",
                            "lastAnnouncePeerCount",
                            default=0,
                        )
                    ),
                    last_announce=_date(
                        _value(
                            tracker,
                            "last_announce_time",
                            "lastAnnounceTime",
                            default=0,
                        )
                    ),
                    next_announce=_date(
                        _value(
                            tracker,
                            "next_announce_time",
                            "nextAnnounceTime",
                            default=0,
                        )
                    ),
                    result=result,
                    announce=_str(_value(tracker, "announce", default="")),
                )
            )

        return _str(_value(torrent, "name", default="")), snapshots

    def reannounce_torrent(self, torrent_id: int) -> None:
        """Ask Transmission to announce one torrent to its trackers now."""
        self._client.reannounce_torrent(torrent_id)


class _ContextScreenMixin:
    """Hide the main application's docked footer while a subview is open."""

    _main_footer: Footer | None = None

    def _hide_main_footer(self) -> None:
        try:
            footer = self.app.query_one(Footer)
        except Exception:
            return
        self._main_footer = footer
        footer.display = False

    def _restore_main_footer(self) -> None:
        if self._main_footer is not None:
            self._main_footer.display = True
            self._main_footer = None


class ContextTorrentDetailScreen(_ContextScreenMixin, BaseTorrentDetailScreen):
    """Torrent details with only the shortcuts valid in this view."""

    CSS = BaseTorrentDetailScreen.CSS + """
    #context-shortcuts {
        height: 1;
        padding: 0 1;
        background: $panel;
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(self._render_details(), id="details", markup=False)
        yield Static(
            "Esc Back   q Back",
            id="context-shortcuts",
            markup=False,
        )

    def on_mount(self) -> None:
        self._hide_main_footer()

    def on_unmount(self) -> None:
        self._restore_main_footer()


class TorrentTrackersScreen(_ContextScreenMixin, Screen[None]):
    """Display tracker state for one torrent and allow manual reannounce."""

    BINDINGS = [
        ("escape", "back", "Back"),
        ("q", "back", "Back"),
        ("r", "refresh_trackers", "Refresh"),
        ("a", "reannounce", "Reannounce"),
    ]

    CSS = """
    #trackers-summary { height: 2; padding: 0 1; }
    #trackers-table { height: 1fr; }
    #context-shortcuts {
        height: 1;
        padding: 0 1;
        background: $panel;
        color: $text-muted;
    }
    """

    def __init__(
        self,
        rpc: TrackerTransmissionClient,
        torrent_id: int,
        torrent_name: str,
    ) -> None:
        super().__init__()
        self.rpc = rpc
        self.torrent_id = torrent_id
        self.torrent_name = torrent_name

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            f"Torrent {self.torrent_id}: {self.torrent_name}",
            id="trackers-summary",
            markup=False,
        )
        yield DataTable(id="trackers-table", zebra_stripes=True)
        yield Static(
            "Esc Back   q Back   r Refresh   a Reannounce",
            id="context-shortcuts",
            markup=False,
        )

    def on_mount(self) -> None:
        self._hide_main_footer()
        table = self.query_one("#trackers-table", DataTable)
        table.cursor_type = "row"
        table.add_columns(
            "ID",
            "Tier",
            "Host",
            "State",
            "Peers",
            "Last announce",
            "Next announce",
            "Result",
            "Announce URL",
        )
        self.action_refresh_trackers()

    def on_unmount(self) -> None:
        self._restore_main_footer()

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_refresh_trackers(self) -> None:
        table = self.query_one("#trackers-table", DataTable)
        selected_id: int | None = None
        if table.row_count:
            try:
                selected_id = int(str(table.get_row_at(table.cursor_row)[0]))
            except (IndexError, KeyError, TypeError, ValueError):
                pass

        try:
            torrent_name, trackers = self.rpc.torrent_trackers(self.torrent_id)
        except Exception as exc:
            self.query_one("#trackers-summary", Static).update(f"RPC error: {exc}")
            return

        self.torrent_name = torrent_name
        table.clear(columns=False)
        selected_row: int | None = None
        failures = 0

        for row_index, tracker in enumerate(trackers):
            if tracker.result not in ("success", "Success", "-"):
                failures += 1
            table.add_row(
                str(tracker.id),
                str(tracker.tier),
                tracker.host,
                tracker.state,
                str(tracker.peers),
                tracker.last_announce,
                tracker.next_announce,
                tracker.result,
                tracker.announce,
                key=str(tracker.id),
            )
            if tracker.id == selected_id:
                selected_row = row_index

        if selected_row is not None:
            table.move_cursor(row=selected_row)

        self.query_one("#trackers-summary", Static).update(
            f"Torrent {self.torrent_id}: {self.torrent_name}\n"
            f"Trackers: {len(trackers)}  Possible errors: {failures}  "
            "a reannounce  r refresh"
        )

    def action_reannounce(self) -> None:
        try:
            self.rpc.reannounce_torrent(self.torrent_id)
        except Exception as exc:
            self.query_one("#trackers-summary", Static).update(f"RPC error: {exc}")
            return
        self.query_one("#trackers-summary", Static).update(
            f"Reannounce requested for torrent {self.torrent_id}: {self.torrent_name}"
        )
        self.set_timer(1.0, self.action_refresh_trackers)


class TransmissionTUI(BaseTransmissionTUI):
    """Transmission TUI with tracker diagnostics."""

    # Primary actions stay in Textual's Footer. Navigation and secondary
    # management commands are shown in our dedicated line above it instead.
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("a", "add_torrent", "Add"),
        Binding("space", "toggle_pause", "Pause/Resume"),
        Binding("v", "verify_torrent", "Verify"),
        Binding("x", "remove_torrent", "Remove"),
        Binding("d", "delete_torrent", "Delete data"),
        Binding("r", "refresh_now", "Refresh"),
        Binding("i", "sort_id", "Sort ID"),
        Binding("u", "sort_up", "Sort Up"),
        Binding("D", "sort_down", "Sort Down"),
        Binding("p", "sort_ratio", "Sort Ratio"),
        Binding("/", "search_torrents", "Search", show=False),
        Binding("f", "cycle_filter", "Filter", show=False),
        Binding("l", "show_files", "Files", show=False),
        Binding("b", "bandwidth", "Bandwidth", show=False),
        Binding("m", "move_location", "Move data", show=False),
        Binding("t", "show_trackers", "Trackers", show=False),
    ]

    CSS = BaseTransmissionTUI.CSS + """
    #shortcut-extra {
        height: 1;
        padding: 0 1;
        background: $panel;
        color: $text-muted;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.rpc = TrackerTransmissionClient()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Static("Connecting to Transmission...", id="summary")
            yield DataTable(id="table", zebra_stripes=True)
        yield Static(
            "Enter Details   / Search   f Filter   l Files   b Bandwidth   "
            "m Move data   t Trackers",
            id="shortcut-extra",
            markup=False,
        )
        yield Footer()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Open exactly one contextual details view for the selected torrent."""
        event.stop()
        try:
            torrent_id = int(str(event.row_key.value))
            details = self.rpc.torrent_details(torrent_id)
        except Exception as exc:
            self.query_one("#summary", Static).update(f"RPC error: {exc}")
            return
        self.push_screen(ContextTorrentDetailScreen(details))

    def action_show_trackers(self) -> None:
        selected = self._selected_torrent()
        if selected is None:
            return
        torrent_id, torrent_name, _ = selected
        self.push_screen(TorrentTrackersScreen(self.rpc, torrent_id, torrent_name))


def _value(obj: Any, *names: str, default: Any) -> Any:
    for name in names:
        if isinstance(obj, Mapping) and name in obj:
            return obj[name]
        try:
            return getattr(obj, name)
        except AttributeError:
            pass
    return default


def _int(value: Any, *, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _str(value: Any) -> str:
    return "" if value is None else str(value)


def _date(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, datetime):
        timestamp = value.timestamp()
    else:
        try:
            timestamp = int(value)
        except (TypeError, ValueError):
            return "-"
    if timestamp <= 0:
        return "-"
    return datetime.fromtimestamp(timestamp).astimezone().strftime(
        "%Y-%m-%d %H:%M:%S"
    )