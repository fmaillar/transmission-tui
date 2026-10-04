"""Tests for command-line startup failures."""

from __future__ import annotations

from contextlib import redirect_stderr
from io import StringIO
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from transmission_rpc import TransmissionError

from transmission_tui.__main__ import main


class CommandLineTest(unittest.TestCase):
    def test_invalid_toml_exits_with_configuration_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"XDG_CONFIG_HOME": tmp},
            clear=True,
        ):
            path = Path(tmp) / "transmission-tui" / "config.toml"
            path.parent.mkdir(parents=True)
            path.write_text("[connection\nhost = 'broken'\n", encoding="utf-8")

            stderr = StringIO()
            with redirect_stderr(stderr), self.assertRaises(SystemExit) as context:
                main([])

        self.assertEqual(context.exception.code, 2)
        self.assertIn("configuration error:", stderr.getvalue())
        self.assertIn("Invalid TOML", stderr.getvalue())

    def test_rpc_startup_failure_exits_cleanly(self) -> None:
        stderr = StringIO()
        with (
            patch(
                "transmission_tui.__main__.TransmissionTUI",
                side_effect=TransmissionError("daemon unavailable"),
            ),
            redirect_stderr(stderr),
            self.assertRaises(SystemExit) as context,
        ):
            main([])

        self.assertEqual(context.exception.code, 1)
        self.assertIn("RPC error: daemon unavailable", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
