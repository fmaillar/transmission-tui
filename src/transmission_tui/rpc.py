"""Thin adapter around transmission-rpc."""

from __future__ import annotations

from dataclasses import dataclass
import os

from transmission_rpc import Client


@dataclass(frozen=True, slots=True)
class TorrentSnapshot:
    id: int
    name: str
    progress: float
    size: int
    uploaded: int
    rate_down: int
    rate_up: int
    ratio: float
    status: str


class TransmissionClient:
    """Read-only Transmission RPC client used by the TUI."""

    def __init__(self) -> None:
        self._client = Client(
            host=os.environ.get("TRANSMISSION_HOST", "127.0.0.1"),
            port=int(os.environ.get("TRANSMISSION_PORT", "9091")),
            username=os.environ.get("TRANSMISSION_USER") or None,
            password=os.environ.get("TRANSMISSION_PASSWORD") or None,
            timeout=5.0,
        )

    def torrents(self) -> list[TorrentSnapshot]:
        fields = (
            "id",
            "name",
            "percentDone",
            "totalSize",
            "uploadedEver",
            "rateDownload",
            "rateUpload",
            "uploadRatio",
            "status",
        )
        torrents = self._client.get_torrents(arguments=fields)
        snapshots: list[TorrentSnapshot] = []
        for torrent in torrents:
            status = str(torrent.status)
            snapshots.append(
                TorrentSnapshot(
                    id=int(torrent.id),
                    name=str(torrent.name),
                    progress=float(torrent.progress),
                    size=int(_attr(torrent, "total_size", "totalSize", default=0)),
                    uploaded=int(_attr(torrent, "uploaded_ever", "uploadedEver", default=0)),
                    rate_down=int(_attr(torrent, "rate_download", "rateDownload", default=0)),
                    rate_up=int(_attr(torrent, "rate_upload", "rateUpload", default=0)),
                    ratio=float(torrent.ratio),
                    status=status,
                )
            )
        return snapshots


def _attr(obj: object, *names: str, default: object) -> object:
    for name in names:
        try:
            return getattr(obj, name)
        except AttributeError:
            pass
    return default
