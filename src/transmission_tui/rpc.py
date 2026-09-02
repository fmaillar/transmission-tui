"""Thin adapter around transmission-rpc."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
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


@dataclass(frozen=True, slots=True)
class TorrentDetails:
    id: int
    name: str
    status: str
    progress: float
    total_size: int
    size_when_done: int
    have_valid: int
    downloaded: int
    uploaded: int
    rate_down: int
    rate_up: int
    ratio: float
    eta: int
    peers_connected: int
    peers_downloading: int
    peers_uploading: int
    webseeds_sending: int
    download_dir: str
    hash_string: str
    added_date: str
    done_date: str
    start_date: str
    activity_date: str
    comment: str
    creator: str
    magnet_link: str


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

    def torrent_details(self, torrent_id: int) -> TorrentDetails:
        """Return a richer snapshot for one torrent."""
        fields = (
            "id",
            "name",
            "status",
            "percentDone",
            "totalSize",
            "sizeWhenDone",
            "haveValid",
            "downloadedEver",
            "uploadedEver",
            "rateDownload",
            "rateUpload",
            "uploadRatio",
            "eta",
            "peersConnected",
            "peersGettingFromUs",
            "peersSendingToUs",
            "webseedsSendingToUs",
            "downloadDir",
            "hashString",
            "addedDate",
            "doneDate",
            "startDate",
            "activityDate",
            "comment",
            "creator",
            "magnetLink",
        )
        torrent = self._client.get_torrent(torrent_id, arguments=fields)
        return TorrentDetails(
            id=int(torrent.id),
            name=str(torrent.name),
            status=str(torrent.status),
            progress=float(torrent.progress),
            total_size=int(_attr(torrent, "total_size", "totalSize", default=0)),
            size_when_done=int(_attr(torrent, "size_when_done", "sizeWhenDone", default=0)),
            have_valid=int(_attr(torrent, "have_valid", "haveValid", default=0)),
            downloaded=int(_attr(torrent, "downloaded_ever", "downloadedEver", default=0)),
            uploaded=int(_attr(torrent, "uploaded_ever", "uploadedEver", default=0)),
            rate_down=int(_attr(torrent, "rate_download", "rateDownload", default=0)),
            rate_up=int(_attr(torrent, "rate_upload", "rateUpload", default=0)),
            ratio=float(torrent.ratio),
            eta=int(_attr(torrent, "eta", default=-1)),
            peers_connected=int(_attr(torrent, "peers_connected", "peersConnected", default=0)),
            peers_downloading=int(
                _attr(torrent, "peers_getting_from_us", "peersGettingFromUs", default=0)
            ),
            peers_uploading=int(
                _attr(torrent, "peers_sending_to_us", "peersSendingToUs", default=0)
            ),
            webseeds_sending=int(
                _attr(torrent, "webseeds_sending_to_us", "webseedsSendingToUs", default=0)
            ),
            download_dir=str(_attr(torrent, "download_dir", "downloadDir", default="")),
            hash_string=str(_attr(torrent, "hash_string", "hashString", default="")),
            added_date=_date(_attr(torrent, "added_date", "addedDate", default=0)),
            done_date=_date(_attr(torrent, "done_date", "doneDate", default=0)),
            start_date=_date(_attr(torrent, "start_date", "startDate", default=0)),
            activity_date=_date(_attr(torrent, "activity_date", "activityDate", default=0)),
            comment=str(_attr(torrent, "comment", default="")),
            creator=str(_attr(torrent, "creator", default="")),
            magnet_link=str(_attr(torrent, "magnet_link", "magnetLink", default="")),
        )


def _date(value: object) -> str:
    if isinstance(value, datetime):
        return value.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    try:
        timestamp = int(value)
    except (TypeError, ValueError):
        return "-"
    if timestamp <= 0:
        return "-"
    return datetime.fromtimestamp(timestamp).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def _attr(obj: object, *names: str, default: object) -> object:
    for name in names:
        try:
            return getattr(obj, name)
        except AttributeError:
            pass
    return default
