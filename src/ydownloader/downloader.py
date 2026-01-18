"""Core download functionality using yt-dlp."""

import yt_dlp
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from ydownloader.config import Config


@dataclass
class VideoInfo:
    """Information about a video."""

    url: str
    title: str
    channel: str
    duration: int  # seconds
    view_count: Optional[int]
    thumbnail: Optional[str]
    description: Optional[str]
    upload_date: Optional[str]
    formats: list[dict]
    is_playlist: bool = False
    playlist_count: Optional[int] = None
    playlist_title: Optional[str] = None

    @property
    def duration_formatted(self) -> str:
        """Return duration as HH:MM:SS or MM:SS."""
        hours, remainder = divmod(self.duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    @property
    def views_formatted(self) -> str:
        """Return view count with commas."""
        if self.view_count is None:
            return "N/A"
        return f"{self.view_count:,}"

    def available_qualities(self) -> list[str]:
        """Get list of available video qualities."""
        heights = set()
        for fmt in self.formats:
            if fmt.get("vcodec") != "none" and fmt.get("height"):
                heights.add(fmt["height"])
        return sorted([f"{h}p" for h in heights], key=lambda x: int(x[:-1]), reverse=True)

    def available_audio_formats(self) -> list[str]:
        """Get list of available audio formats."""
        return ["mp3", "m4a", "opus", "flac", "wav"]


class ProgressHook:
    """Progress hook for tracking download progress."""

    def __init__(
        self,
        on_progress: Optional[Callable[[dict], None]] = None,
        on_complete: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        self.on_progress = on_progress
        self.on_complete = on_complete
        self.on_error = on_error
        self._current_file = None

    def __call__(self, d: dict):
        """Handle progress updates from yt-dlp."""
        status = d.get("status")

        if status == "downloading":
            if self.on_progress:
                progress_info = {
                    "status": "downloading",
                    "filename": d.get("filename", ""),
                    "downloaded_bytes": d.get("downloaded_bytes", 0),
                    "total_bytes": d.get("total_bytes") or d.get("total_bytes_estimate", 0),
                    "speed": d.get("speed", 0),
                    "eta": d.get("eta", 0),
                    "percent": 0,
                }
                if progress_info["total_bytes"]:
                    progress_info["percent"] = (
                        progress_info["downloaded_bytes"] / progress_info["total_bytes"] * 100
                    )
                self.on_progress(progress_info)

        elif status == "finished":
            self._current_file = d.get("filename", "")
            if self.on_progress:
                self.on_progress({
                    "status": "processing",
                    "filename": self._current_file,
                    "percent": 100,
                })

        elif status == "error":
            if self.on_error:
                self.on_error(str(d.get("error", "Unknown error")))


class YDownloader:
    """Main downloader class using yt-dlp."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._progress_hook: Optional[ProgressHook] = None

    def set_progress_callback(
        self,
        on_progress: Optional[Callable[[dict], None]] = None,
        on_complete: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        """Set callbacks for progress tracking."""
        self._progress_hook = ProgressHook(on_progress, on_complete, on_error)

    def get_info(self, url: str) -> VideoInfo:
        """Fetch video/playlist information without downloading."""
        opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": "in_playlist",
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

            is_playlist = info.get("_type") == "playlist"

            if is_playlist:
                # Get info from first video for display
                entries = info.get("entries", [])
                first_entry = entries[0] if entries else {}
                return VideoInfo(
                    url=url,
                    title=first_entry.get("title", "Unknown"),
                    channel=info.get("uploader") or first_entry.get("uploader", "Unknown"),
                    duration=first_entry.get("duration", 0) or 0,
                    view_count=first_entry.get("view_count"),
                    thumbnail=info.get("thumbnail") or first_entry.get("thumbnail"),
                    description=info.get("description"),
                    upload_date=first_entry.get("upload_date"),
                    formats=first_entry.get("formats", []),
                    is_playlist=True,
                    playlist_count=len(entries),
                    playlist_title=info.get("title", "Unknown Playlist"),
                )

            return VideoInfo(
                url=url,
                title=info.get("title", "Unknown"),
                channel=info.get("uploader") or info.get("channel", "Unknown"),
                duration=info.get("duration", 0) or 0,
                view_count=info.get("view_count"),
                thumbnail=info.get("thumbnail"),
                description=info.get("description"),
                upload_date=info.get("upload_date"),
                formats=info.get("formats", []),
                is_playlist=False,
            )

    def download(self, url: str, config: Optional[Config] = None) -> list[Path]:
        """
        Download video(s) from URL.

        Args:
            url: YouTube URL (video or playlist)
            config: Optional config override

        Returns:
            List of downloaded file paths
        """
        cfg = config or self.config
        opts = cfg.to_yt_dlp_opts()

        downloaded_files: list[Path] = []

        def track_file(d: dict):
            if d.get("status") == "finished":
                filepath = d.get("filename")
                if filepath:
                    downloaded_files.append(Path(filepath))

        # Set up progress hooks
        opts["progress_hooks"] = [track_file]
        if self._progress_hook:
            opts["progress_hooks"].append(self._progress_hook)

        # Ensure output directory exists
        cfg.output_dir.mkdir(parents=True, exist_ok=True)

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        return downloaded_files

    def download_audio(self, url: str, config: Optional[Config] = None) -> list[Path]:
        """Download audio only from URL."""
        cfg = config or Config(**vars(self.config))
        cfg.audio_only = True
        return self.download(url, cfg)

    def download_video(self, url: str, config: Optional[Config] = None) -> list[Path]:
        """Download video from URL."""
        cfg = config or Config(**vars(self.config))
        cfg.audio_only = False
        return self.download(url, cfg)

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is a valid YouTube URL."""
        extractors = [
            "youtube.com",
            "youtu.be",
            "youtube.com/shorts",
            "music.youtube.com",
        ]
        return any(ext in url.lower() for ext in extractors)

    @staticmethod
    def is_playlist_url(url: str) -> bool:
        """Check if URL is a playlist URL."""
        return "list=" in url or "/playlist" in url
