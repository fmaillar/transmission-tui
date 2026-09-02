"""Regression tests for context-sensitive Enter handling."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from textual.widgets import DataTable, Input

from transmission_tui.app import AddTorrentScreen
from transmission_tui.rpc import AddedTorrent
from transmission_tui.trackers import TransmissionTUI


class _FakeRPC:
    def __init__(self) -> None:
        self.added_sources: list[str] = []

    def add_torrent(self, source: str) -> AddedTorrent:
        self.added_sources.append(source)
        return AddedTorrent(id=42, name="Test torrent")


class _TestApp(TransmissionTUI):
    def __init__(self) -> None:
        rpc = _FakeRPC()
        with (
            patch("transmission_tui.app.TransmissionClient", return_value=rpc),
            patch(
                "transmission_tui.trackers.TrackerTransmissionClient",
                return_value=rpc,
            ),
        ):
            super().__init__()
        self.open_details_calls = 0
        self.added: AddedTorrent | None = None

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

    def action_open_details(self) -> None:
        self.open_details_calls += 1

    def _torrent_added(self, added: AddedTorrent | None) -> None:
        self.added = added


class EnterRoutingTest(unittest.IsolatedAsyncioTestCase):
    async def test_enter_submits_add_torrent_modal(self) -> None:
        app = _TestApp()
        source = "magnet:?xt=urn:btih:0123456789abcdef"

        async with app.run_test() as pilot:
            await pilot.press("a")
            await pilot.pause()
            self.assertIsInstance(app.screen, AddTorrentScreen)

            app.screen.query_one("#add-source", Input).value = source
            await pilot.press("enter")
            await pilot.pause()

            self.assertEqual(app.rpc.added_sources, [source])
            self.assertEqual(app.added, AddedTorrent(id=42, name="Test torrent"))
            self.assertEqual(app.open_details_calls, 0)
            self.assertNotIsInstance(app.screen, AddTorrentScreen)

    async def test_enter_on_main_table_opens_details_once(self) -> None:
        app = _TestApp()

        async with app.run_test() as pilot:
            table = app.query_one("#table", DataTable)
            table.add_row(
                "1",
                "100%",
                "1 GB",
                "1 GB",
                "0 B/s",
                "0 B/s",
                "1.00",
                "Seeding",
                "Test torrent",
                key="1",
            )
            table.focus()

            await pilot.press("enter")
            await pilot.pause()

            self.assertEqual(app.open_details_calls, 1)


if __name__ == "__main__":
    unittest.main()
