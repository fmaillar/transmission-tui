"""Thin adapter around transmission-rpc."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from transmission_rpc import Client


_MAX_TORRENT_SIZE = 16 * 1024 * 1024


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
class AddedTorrent:
    id: int
    name: str


@dataclass(frozen=True, slots=True)
class TorrentFile:
    id: int
    name: str
    size: int
    completed: int
    wanted: bool
    priority: str


@dataclass(frozen=True, slots=True)
class TorrentLimits:
    download: int | None
    upload: int | None


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
    """Small adapter around the Transmission RPC client."""

    def __init__(self) -> None:
        self._client = Client(
            host=os.environ.get("TRANSMISSION_HOST", "127.0.0.1"),
            port=int(os.environ.get("TRANSMISSION_PORT", "9091")),
            username=os.environ.get("TRANSMISSION_USER") or None,
            password=os.environ.get("TRANSMISSION_PASSWORD") or None,
            timeout=5.0,
        )

    def add_torrent(self, source: str) -> AddedTorrent:
        """Add an HTTP(S) torrent URL or magnet link."""
        source = source.strip()
        if not source:
            raise ValueError("Torrent URL or magnet link is empty")

        if source.startswith("magnet:?"):
            torrent_source: str | bytes = source
        elif source.startswith(("http://", "https://")):
            torrent_source = _download_torrent(source)
        else:
            raise ValueError("Expected an http(s) URL or magnet link")

        torrent = self._client.add_torrent(torrent_source)
        return AddedTorrent(id=_int(torrent.id), name=_str(torrent.name))

    def remove_torrent(self, torrent_id: int, *, delete_data: bool = True) -> None:
        """Remove one torrent, optionally deleting its local data."""
        self._client.remove_torrent(torrent_id, delete_data=delete_data)

    def start_torrent(self, torrent_id: int) -> None:
        """Start or resume one torrent."""
        self._client.start_torrent(torrent_id)

    def stop_torrent(self, torrent_id: int) -> None:
        """Pause one torrent."""
        self._client.stop_torrent(torrent_id)

    def verify_torrent(self, torrent_id: int) -> None:
        """Ask Transmission to verify the local data for one torrent."""
        self._client.verify_torrent(torrent_id)

    def torrent_limits(self, torrent_id: int) -> TorrentLimits:
        """Return current per-torrent download/upload limits in kB/s."""
        torrent = self._client.get_torrent(
            torrent_id,
            arguments=(
                "downloadLimited",
                "downloadLimit",
                "uploadLimited",
                "uploadLimit",
            ),
        )
        download_limited = bool(
            _attr(torrent, "download_limited", "downloadLimited", default=False)
        )
        upload_limited = bool(
            _attr(torrent, "upload_limited", "uploadLimited", default=False)
        )
        return TorrentLimits(
            download=_int(
                _attr(torrent, "download_limit", "downloadLimit", default=0)
            )
            if download_limited
            else None,
            upload=_int(_attr(torrent, "upload_limit", "uploadLimit", default=0))
            if upload_limited
            else None,
        )

    def set_torrent_limits(
        self,
        torrent_id: int,
        *,
        download: int | None,
        upload: int | None,
    ) -> None:
        """Set per-torrent bandwidth limits in kB/s; None means unlimited."""
        if download is not None and download <= 0:
            raise ValueError("Download limit must be positive")
        if upload is not None and upload <= 0:
            raise ValueError("Upload limit must be positive")

        kwargs: dict[str, object] = {
            "download_limited": download is not None,
            "upload_limited": upload is not None,
        }
        if download is not None:
            kwargs["download_limit"] = download
        if upload is not None:
            kwargs["upload_limit"] = upload
        self._client.change_torrent(torrent_id, **kwargs)

    def torrent_files(self, torrent_id: int) -> tuple[str, list[TorrentFile]]:
        """Return file selection, progress and priority for one torrent."""
        torrent = self._client.get_torrent(
            torrent_id,
            arguments=("id", "name", "files", "priorities", "wanted"),
        )
        files: list[TorrentFile] = []
        for file in torrent.get_files():
            priority_value = _int(file.priority)
            priority = {-1: "low", 0: "normal", 1: "high"}.get(
                priority_value, str(priority_value)
            )
            files.append(
                TorrentFile(
                    id=_int(file.id),
                    name=_str(file.name),
                    size=_int(file.size),
                    completed=_int(file.completed),
                    wanted=bool(file.selected),
                    priority=priority,
                )
            )
        return _str(torrent.name), files

    def set_file_wanted(self, torrent_id: int, file_id: int, *, wanted: bool) -> None:
        """Enable or disable downloading of one file in a torrent."""
        if wanted:
            self._client.change_torrent(torrent_id, files_wanted=[file_id])
        else:
            self._client.change_torrent(torrent_id, files_unwanted=[file_id])

    def set_file_priority(self, torrent_id: int, file_id: int, priority: str) -> None:
        """Set one torrent file to low, normal or high priority."""
        if priority == "low":
            self._client.change_torrent(torrent_id, priority_low=[file_id])
        elif priority == "normal":
            self._client.change_torrent(torrent_id, priority_normal=[file_id])
        elif priority == "high":
            self._client.change_torrent(torrent_id, priority_high=[file_id])
        else:
            raise ValueError(f"Unknown file priority: {priority}")

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
            snapshots.append(
                TorrentSnapshot(
                    id=_int(torrent.id),
                    name=str(torrent.name),
                    progress=_float(torrent.progress),
                    size=_int(_attr(torrent, "total_size", "totalSize", default=0)),
                    uploaded=_int(_attr(torrent, "uploaded_ever", "uploadedEver", default=0)),
                    rate_down=_int(_attr(torrent, "rate_download", "rateDownload", default=0)),
                    rate_up=_int(_attr(torrent, "rate_upload", "rateUpload", default=0)),
                    ratio=_float(torrent.ratio),
                    status=str(torrent.status),
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
            id=_int(torrent.id),
            name=str(torrent.name),
            status=str(torrent.status),
            progress=_float(torrent.progress),
            total_size=_int(_attr(torrent, "total_size", "totalSize", default=0)),
            size_when_done=_int(_attr(torrent, "size_when_done", "sizeWhenDone", default=0)),
            have_valid=_int(_attr(torrent, "have_valid", "haveValid", default=0)),
            downloaded=_int(_attr(torrent, "downloaded_ever", "downloadedEver", default=0)),
            uploaded=_int(_attr(torrent, "uploaded_ever", "uploadedEver", default=0)),
            rate_down=_int(_attr(torrent, "rate_download", "rateDownload", default=0)),
            rate_up=_int(_attr(torrent, "rate_upload", "rateUpload", default=0)),
            ratio=_float(torrent.ratio),
            eta=_int(_attr(torrent, "eta", default=-1), default=-1),
            peers_connected=_int(_attr(torrent, "peers_connected", "peersConnected", default=0)),
            peers_downloading=_int(
                _attr(torrent, "peers_getting_from_us", "peersGettingFromUs", default=0)
            ),
            peers_uploading=_int(
                _attr(torrent, "peers_sending_to_us", "peersSendingToUs", default=0)
            ),
            webseeds_sending=_int(
                _attr(torrent, "webseeds_sending_to_us", "webseedsSendingToUs", default=0)
            ),
            download_dir=_str(_attr(torrent, "download_dir", "downloadDir", default="")),
            hash_string=_str(_attr(torrent, "hash_string", "hashString", default="")),
            added_date=_date(_attr(torrent, "added_date", "addedDate", default=0)),
            done_date=_date(_attr(torrent, "done_date", "doneDate", default=0)),
            start_date=_date(_attr(torrent, "start_date", "startDate", default=0)),
            activity_date=_date(_attr(torrent, "activity_date", "activityDate", default=0)),
            comment=_str(_attr(torrent, "comment", default="")),
            creator=_str(_attr(torrent, "creator", default="")),
            magnet_link=_str(_attr(torrent, "magnet_link", "magnetLink", default="")),
        )


def _download_torrent(url: str) -> bytes:
    """Download torrent metainfo locally before passing it to Transmission."""
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 transmission-tui/0.1",
            "Accept": "application/x-bittorrent,application/octet-stream,*/*;q=0.8",
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            content_length = response.headers.get("Content-Length")
            if content_length is not None and int(content_length) > _MAX_TORRENT_SIZE:
                raise ValueError("Torrent file is unexpectedly large")
            data = response.read(_MAX_TORRENT_SIZE + 1)
    except HTTPError as exc:
        raise ValueError(f"HTTP {exc.code}: {exc.reason}") from exc
    except URLError as exc:
        raise ValueError(f"Unable to download torrent: {exc.reason}") from exc

    if len(data) > _MAX_TORRENT_SIZE:
        raise ValueError("Torrent file is unexpectedly large")
    if not data:
        raise ValueError("Downloaded torrent file is empty")
    if not data.startswith(b"d"):
        raise ValueError("Downloaded content is not a valid torrent file")
    return data


def _int(value: object, *, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _float(value: object, *, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _str(value: object) -> str:
    return "" if value is None else str(value)


def _date(value: object) -> str:
    if value is None:
        return "-"
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
