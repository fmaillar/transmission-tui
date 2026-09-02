"""Torrent data relocation support for the Textual application."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Static

from .app import TransmissionTUI as BaseTransmissionTUI


class MoveLocationScreen(ModalScreen[str | None]):
    """Prompt for a new on-disk location for one torrent."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    CSS = """
    MoveLocationScreen { align: center middle; }
    #move-box {
        width: 82%;
        max-width: 110;
        height: auto;
        border: round $warning;
        padding: 1 2;
        background: $surface;
    }
    #move-title {
        text-style: bold;
        margin-bottom: 1;
    }
    #move-error {
        min-height: 1;
        color: $error;
        margin-top: 1;
    }
    """

    def __init__(
        self,
        torrent_id: int,
        torrent_name: str,
        current_location: str,
    ) -> None:
        super().__init__()
        self.torrent_id = torrent_id
        self.torrent_name = torrent_name
        self.current_location = current_location

    def compose(self) -> ComposeResult:
        with Vertical(id="move-box"):
            yield Static(
                f"Move data — torrent {self.torrent_id}: {self.torrent_name}",
                id="move-title",
                markup=False,
            )
            yield Static(
                "Transmission will move the torrent data to this directory."
            )
            yield Input(
                value=self.current_location,
                placeholder="/absolute/path/to/destination",
                id="move-location",
            )
            yield Static("Enter: move   Esc: cancel")
            yield Static("", id="move-error")

    def on_mount(self) -> None:
        field = self.query_one("#move-location", Input)
        field.focus()
        field.action_end()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        location = event.value.strip()
        if not location:
            self.query_one("#move-error", Static).update(
                "Destination directory cannot be empty"
            )
            return
        if not location.startswith("/"):
            self.query_one("#move-error", Static).update(
                "Destination must be an absolute path"
            )
            return
        if location == self.current_location:
            self.dismiss(None)
            return
        self.dismiss(location)


class TransmissionTUI(BaseTransmissionTUI):
    """Transmission TUI with torrent data relocation support."""

    BINDINGS = [
        *BaseTransmissionTUI.BINDINGS,
        ("m", "move_location", "Move data"),
    ]

    def action_move_location(self) -> None:
        selected = self._selected_torrent()
        if selected is None:
            return
        torrent_id, torrent_name, _ = selected
        try:
            details = self.rpc.torrent_details(torrent_id)
        except Exception as exc:
            self.query_one("#summary", Static).update(f"RPC error: {exc}")
            return

        self.push_screen(
            MoveLocationScreen(
                torrent_id,
                torrent_name,
                details.download_dir,
            ),
            lambda location: self._location_applied(
                torrent_id,
                torrent_name,
                location,
            ),
        )

    def _location_applied(
        self,
        torrent_id: int,
        torrent_name: str,
        location: str | None,
    ) -> None:
        if location is None:
            return
        try:
            self.rpc.move_torrent_data(torrent_id, location)
        except Exception as exc:
            self.query_one("#summary", Static).update(f"RPC error: {exc}")
            return
        self.query_one("#summary", Static).update(
            f"Moving torrent {torrent_id}: {torrent_name} to {location}"
        )
