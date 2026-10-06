"""Tests for the file-selection panel embedded in torrent details."""

from __future__ import annotations

from dataclasses import replace
import unittest

from textual.app import App
from textual.widgets import DataTable

from transmission_tui.app import TorrentDetailScreen
from transmission_tui.rpc import TorrentDetails, TorrentFile


class _FakeRPC:
    def __init__(self) -> None:
        self.files = [
            TorrentFile(
                id=0,
                name="disc/track-01.flac",
                size=100,
                completed=100,
                wanted=True,
                priority="normal",
            ),
            TorrentFile(
                id=1,
                name="disc/track-02.flac",
                size=200,
                completed=0,
                wanted=False,
                priority="normal",
            ),
        ]
        self.wanted_calls: list[tuple[int, int, bool]] = []

    def torrent_files(self, torrent_id: int) -> tuple[str, list[TorrentFile]]:
        return "Test torrent", list(self.files)

    def set_file_wanted(
        self, torrent_id: int, file_id: int, *, wanted: bool
    ) -> None:
        self.wanted_calls.append((torrent_id, file_id, wanted))
        self.files = [
            replace(file, wanted=wanted) if file.id == file_id else file
            for file in self.files
        ]

    def set_file_priority(
        self, torrent_id: int, file_id: int, priority: str
    ) -> None:
        self.files = [
            replace(file, priority=priority) if file.id == file_id else file
            for file in self.files
        ]


def _details() -> TorrentDetails:
    return TorrentDetails(
        id=7,
        name="Test torrent",
        status="downloading",
        progress=50.0,
        total_size=300,
        size_when_done=300,
        have_valid=100,
        downloaded=100,
        uploaded=0,
        rate_down=0,
        rate_up=0,
        ratio=0.0,
        eta=-1,
        peers_connected=0,
        peers_downloading=0,
        peers_uploading=0,
        webseeds_sending=0,
        download_dir="/srv/torrents",
        hash_string="deadbeef",
        added_date="-",
        done_date="-",
        start_date="-",
        activity_date="-",
        comment="",
        creator="",
        magnet_link="",
    )


class _DetailApp(App[None]):
    def __init__(self, rpc: _FakeRPC) -> None:
        super().__init__()
        self.rpc = rpc

    def on_mount(self) -> None:
        self.push_screen(TorrentDetailScreen(self.rpc, _details()))


class DetailFilesTest(unittest.IsolatedAsyncioTestCase):
    async def test_space_toggles_selected_file_from_details(self) -> None:
        rpc = _FakeRPC()
        app = _DetailApp(rpc)

        async with app.run_test() as pilot:
            await pilot.pause()
            self.assertIsInstance(app.screen, TorrentDetailScreen)

            table = app.screen.query_one("#files-table", DataTable)
            self.assertEqual(table.row_count, 2)
            self.assertEqual(str(table.get_row_at(0)[1]), "[x]")
            self.assertEqual(str(table.get_row_at(1)[1]), "[ ]")

            table.move_cursor(row=1)
            table.focus()
            await pilot.press("space")
            await pilot.pause()

            self.assertEqual(rpc.wanted_calls, [(7, 1, True)])
            self.assertEqual(str(table.get_row_at(1)[1]), "[x]")


if __name__ == "__main__":
    unittest.main()
