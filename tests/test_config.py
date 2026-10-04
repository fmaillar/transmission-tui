from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from transmission_tui.config import Config, config_path, load_config


class ConfigTests(unittest.TestCase):
    def test_defaults_without_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"XDG_CONFIG_HOME": tmp},
            clear=True,
        ):
            self.assertEqual(load_config(), Config())

    def test_loads_toml_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"XDG_CONFIG_HOME": tmp},
            clear=True,
        ):
            path = config_path()
            path.parent.mkdir(parents=True)
            path.write_text(
                '[connection]\n'
                'host = "100.70.248.101"\n'
                'port = 9091\n'
                '\n'
                '[ui]\n'
                'refresh_interval = 0.5\n',
                encoding="utf-8",
            )

            self.assertEqual(
                load_config(),
                Config(
                    host="100.70.248.101",
                    port=9091,
                    refresh_interval=0.5,
                ),
            )

    def test_environment_overrides_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "XDG_CONFIG_HOME": tmp,
                "TRANSMISSION_HOST": "m710s",
                "TRANSMISSION_PORT": "9092",
                "TRANSMISSION_REFRESH_INTERVAL": "0.75",
            },
            clear=True,
        ):
            path = Path(tmp) / "transmission-tui" / "config.toml"
            path.parent.mkdir(parents=True)
            path.write_text(
                '[connection]\n'
                'host = "127.0.0.1"\n'
                'port = 9091\n'
                '\n'
                '[ui]\n'
                'refresh_interval = 1.0\n',
                encoding="utf-8",
            )

            self.assertEqual(
                load_config(),
                Config(
                    host="m710s",
                    port=9092,
                    refresh_interval=0.75,
                ),
            )

    def test_rejects_out_of_range_refresh_interval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"XDG_CONFIG_HOME": tmp},
            clear=True,
        ):
            path = config_path()
            path.parent.mkdir(parents=True)
            path.write_text(
                '[ui]\nrefresh_interval = 0.1\n',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "between 0.25 and 10.00"):
                load_config()


if __name__ == "__main__":
    unittest.main()
