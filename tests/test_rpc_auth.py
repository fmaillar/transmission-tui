"""Tests for Transmission RPC credential resolution."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from transmission_tui.rpc import TransmissionClient


class TransmissionAuthTest(unittest.TestCase):
    def _make_netrc(self, content: str) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        tmp = tempfile.TemporaryDirectory()
        path = Path(tmp.name) / ".netrc"
        path.write_text(content, encoding="utf-8")
        path.chmod(0o600)
        return tmp, path

    def test_uses_netrc_for_default_loopback_host(self) -> None:
        tmp, _path = self._make_netrc(
            "machine localhost\nlogin netrc-user\npassword netrc-password\n"
        )
        self.addCleanup(tmp.cleanup)

        env = {
            "HOME": tmp.name,
            "TRANSMISSION_HOST": "127.0.0.1",
            "TRANSMISSION_PORT": "9091",
        }
        with (
            patch.dict(os.environ, env, clear=True),
            patch("transmission_tui.rpc.Client") as client,
        ):
            TransmissionClient()

        client.assert_called_once_with(
            host="127.0.0.1",
            port=9091,
            username="netrc-user",
            password="netrc-password",
            timeout=5.0,
        )

    def test_environment_credentials_override_netrc(self) -> None:
        tmp, _path = self._make_netrc(
            "machine 127.0.0.1\nlogin netrc-user\npassword netrc-password\n"
        )
        self.addCleanup(tmp.cleanup)

        env = {
            "HOME": tmp.name,
            "TRANSMISSION_HOST": "127.0.0.1",
            "TRANSMISSION_PORT": "9091",
            "TRANSMISSION_USER": "env-user",
            "TRANSMISSION_PASSWORD": "env-password",
        }
        with (
            patch.dict(os.environ, env, clear=True),
            patch("transmission_tui.rpc.Client") as client,
        ):
            TransmissionClient()

        client.assert_called_once_with(
            host="127.0.0.1",
            port=9091,
            username="env-user",
            password="env-password",
            timeout=5.0,
        )


if __name__ == "__main__":
    unittest.main()
