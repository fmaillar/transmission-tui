"""Persistent configuration for transmission-tui."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import tomllib


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9091
DEFAULT_REFRESH_INTERVAL = 1.0
MIN_REFRESH_INTERVAL = 0.25
MAX_REFRESH_INTERVAL = 10.0


@dataclass(frozen=True, slots=True)
class Config:
    """Resolved application configuration."""

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    refresh_interval: float = DEFAULT_REFRESH_INTERVAL


def config_path() -> Path:
    """Return the XDG configuration file path."""

    config_home = os.environ.get("XDG_CONFIG_HOME")
    base = Path(config_home).expanduser() if config_home else Path.home() / ".config"
    return base / "transmission-tui" / "config.toml"


def load_config() -> Config:
    """Load configuration, then apply environment-variable overrides."""

    path = config_path()
    data: dict[str, object] = {}

    try:
        with path.open("rb") as stream:
            loaded = tomllib.load(stream)
    except FileNotFoundError:
        pass
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"Invalid TOML in {path}: {exc}") from exc
    else:
        data = loaded

    connection = _table(data, "connection")
    ui = _table(data, "ui")

    host = _string(connection.get("host", DEFAULT_HOST), "connection.host")
    port = _port(connection.get("port", DEFAULT_PORT), "connection.port")
    refresh_interval = _refresh_interval(
        ui.get("refresh_interval", DEFAULT_REFRESH_INTERVAL),
        "ui.refresh_interval",
    )

    if "TRANSMISSION_HOST" in os.environ:
        host = _string(os.environ["TRANSMISSION_HOST"], "TRANSMISSION_HOST")
    if "TRANSMISSION_PORT" in os.environ:
        port = _port(os.environ["TRANSMISSION_PORT"], "TRANSMISSION_PORT")
    if "TRANSMISSION_REFRESH_INTERVAL" in os.environ:
        refresh_interval = _refresh_interval(
            os.environ["TRANSMISSION_REFRESH_INTERVAL"],
            "TRANSMISSION_REFRESH_INTERVAL",
        )

    return Config(
        host=host,
        port=port,
        refresh_interval=refresh_interval,
    )


def _table(data: dict[str, object], key: str) -> dict[str, object]:
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be a TOML table")
    return value


def _string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _port(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError(f"{name} must be an integer")
    try:
        port = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if not 1 <= port <= 65535:
        raise ValueError(f"{name} must be between 1 and 65535")
    return port


def _refresh_interval(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{name} must be a number")
    try:
        interval = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    if not MIN_REFRESH_INTERVAL <= interval <= MAX_REFRESH_INTERVAL:
        raise ValueError(
            f"{name} must be between {MIN_REFRESH_INTERVAL:.2f} "
            f"and {MAX_REFRESH_INTERVAL:.2f} seconds"
        )
    return interval
