"""Tests for RPC connection loss while the TUI is running."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from textual.widgets import Static
from transmission_rpc import TransmissionError

from transmission_tui.app import TransmissionTUI
from transmission_tui.config import Config


class _DisconnectedRPC:
    def torrents(self) -> list[object]:
        raise TransmissionError("connection lost")


class RpcDisconnectTest(unittest.IsolatedAsyncioTestCase):
    async def test_refresh_reports_connection_loss_without_crashing(self) -> None:
        with (
            patch(
                "transmission_tui.app.TransmissionClient",
                return_value=_DisconnectedRPC(),
            ),
            patch(
                "transmission_tui.app.load_config",
                return_value=Config(refresh_interval=10.0),
            ),
        ):
            app = TransmissionTUI()

        async with app.run_test() as pilot:
            await pilot.pause()
            summary = app.query_one("#summary", Static)
            self.assertIn("RPC error: connection lost", str(summary.content))


if __name__ == "__main__":
    unittest.main()
