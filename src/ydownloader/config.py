"""Configuration management for YDownloader."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Configuration options for downloads."""

    # Output settings
    output_dir: Path = field(default_factory=lambda: Path.home() / "Downloads")
    filename_template: str = "%(title)s.%(ext)s"

    # Download type
    audio_only: bool = False

    # Quality settings
    quality: str = "best"  # best, worst, or specific like 720p, 1080p
    audio_quality: str = "best"  # best, worst, or bitrate like 192k

    # Format settings
    video_format: str = "mp4"  # mp4, mkv, webm
    audio_format: str = "mp3"  # mp3, m4a, opus, flac

    # Embedding options
    embed_metadata: bool = True
    embed_thumbnail: bool = False
    embed_subtitles: bool = False

    # Subtitle options
    download_subtitles: bool = False
    subtitle_langs: list[str] = field(default_factory=lambda: ["en"])
    auto_subtitles: bool = True  # Include auto-generated subtitles

    # Playlist options
    playlist: bool = True  # Download full playlist if URL is a playlist
    playlist_start: Optional[int] = None
    playlist_end: Optional[int] = None

    # Network options
    rate_limit: Optional[str] = None  # e.g., "1M" for 1MB/s
    retries: int = 3

    # Misc options
    quiet: bool = False
    verbose: bool = False

    def __post_init__(self):
        """Ensure output_dir is a Path object."""
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir).expanduser()
        self.output_dir = self.output_dir.expanduser()

    def to_yt_dlp_opts(self) -> dict:
        """Convert config to yt-dlp options dictionary."""
        opts = {
            "outtmpl": str(self.output_dir / self.filename_template),
            "retries": self.retries,
            "ignoreerrors": False,
            "no_warnings": self.quiet,
            "quiet": self.quiet,
            "verbose": self.verbose,
        }

        # Format selection
        if self.audio_only:
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": self.audio_format,
                "preferredquality": self._parse_audio_quality(),
            }]
        else:
            opts["format"] = self._build_format_string()
            opts["merge_output_format"] = self.video_format

        # Metadata embedding
        if self.embed_metadata:
            opts.setdefault("postprocessors", []).append({
                "key": "FFmpegMetadata",
                "add_metadata": True,
            })

        # Thumbnail embedding
        if self.embed_thumbnail:
            opts["writethumbnail"] = True
            opts.setdefault("postprocessors", []).append({
                "key": "EmbedThumbnail",
            })

        # Subtitles
        if self.download_subtitles:
            opts["writesubtitles"] = True
            opts["subtitleslangs"] = self.subtitle_langs
            if self.auto_subtitles:
                opts["writeautomaticsub"] = True
            if self.embed_subtitles:
                opts.setdefault("postprocessors", []).append({
                    "key": "FFmpegEmbedSubtitle",
                })

        # Playlist handling
        if not self.playlist:
            opts["noplaylist"] = True
        else:
            if self.playlist_start:
                opts["playliststart"] = self.playlist_start
            if self.playlist_end:
                opts["playlistend"] = self.playlist_end

        # Rate limiting
        if self.rate_limit:
            opts["ratelimit"] = self._parse_rate_limit()

        return opts

    def _build_format_string(self) -> str:
        """Build yt-dlp format string based on quality settings."""
        if self.quality == "best":
            return "bestvideo+bestaudio/best"
        elif self.quality == "worst":
            return "worstvideo+worstaudio/worst"
        else:
            # Parse quality like "720p", "1080p"
            height = self.quality.rstrip("p")
            if height.isdigit():
                return f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
            return "bestvideo+bestaudio/best"

    def _parse_audio_quality(self) -> str:
        """Parse audio quality setting for yt-dlp."""
        if self.audio_quality == "best":
            return "0"  # Best quality in yt-dlp
        elif self.audio_quality == "worst":
            return "9"  # Worst quality
        else:
            # Return bitrate value like "192" from "192k"
            return self.audio_quality.rstrip("kK")

    def _parse_rate_limit(self) -> int:
        """Parse rate limit string to bytes per second."""
        if not self.rate_limit:
            return 0

        rate = self.rate_limit.upper()
        multipliers = {"K": 1024, "M": 1024 * 1024, "G": 1024 * 1024 * 1024}

        for suffix, mult in multipliers.items():
            if rate.endswith(suffix):
                return int(float(rate[:-1]) * mult)

        return int(rate)
