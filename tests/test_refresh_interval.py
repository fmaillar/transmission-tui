"""Tests for adjustable refresh interval bounds."""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from transmission_tui.app import TransmissionTUI
from transmission_tui.config import Config


class RefreshIntervalTest(unittest.TestCase):
    def _app(self) -> TransmissionTUI:
        with (
            patch("transmission_tui.app.TransmissionClient"),
            patch(
                "transmission_tui.app.load_config",
                return_value=Config(refresh_interval=1.0),
            ),
        ):
            return TransmissionTUI()

    def test_plus_increases_interval_by_250_ms(self) -> None:
        app = self._app()
        with (
            patch.object(app, "_reset_refresh_timer") as reset_timer,
            patch.object(app, "refresh_data") as refresh_data,
        ):
            app.action_increase_refresh_interval()

        self.assertEqual(app.refresh_interval, 1.25)
        reset_timer.assert_called_once_with()
        refresh_data.assert_called_once_with()

    def test_minus_decreases_interval_by_250_ms(self) -> None:
        app = self._app()
        with (
            patch.object(app, "_reset_refresh_timer") as reset_timer,
            patch.object(app, "refresh_data") as refresh_data,
        ):
            app.action_decrease_refresh_interval()

        self.assertEqual(app.refresh_interval, 0.75)
        reset_timer.assert_called_once_with()
        refresh_data.assert_called_once_with()

    def test_plus_does_not_exceed_maximum(self) -> None:
        app = self._app()
        app.refresh_interval = app.MAX_REFRESH_INTERVAL
        with (
            patch.object(app, "_reset_refresh_timer") as reset_timer,
            patch.object(app, "refresh_data") as refresh_data,
        ):
            app.action_increase_refresh_interval()

        self.assertEqual(app.refresh_interval, app.MAX_REFRESH_INTERVAL)
        reset_timer.assert_not_called()
        refresh_data.assert_not_called()

    def test_minus_does_not_go_below_minimum(self) -> None:
        app = self._app()
        app.refresh_interval = app.MIN_REFRESH_INTERVAL
        with (
            patch.object(app, "_reset_refresh_timer") as reset_timer,
            patch.object(app, "refresh_data") as refresh_data,
        ):
            app.action_decrease_refresh_interval()

        self.assertEqual(app.refresh_interval, app.MIN_REFRESH_INTERVAL)
        reset_timer.assert_not_called()
        refresh_data.assert_not_called()


if __name__ == "__main__":
    unittest.main()
