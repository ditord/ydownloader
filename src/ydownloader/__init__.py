"""
YDownloader - A modern YouTube downloader with CLI and interactive TUI.

Features:
- Video and audio downloads
- Quality and format selection
- Playlist support
- Subtitles download
- Metadata and thumbnail embedding
- Rich interactive TUI mode
"""

__version__ = "2.0.0"
__author__ = "Artur Papyan"

from ydownloader.downloader import YDownloader
from ydownloader.config import Config

__all__ = ["YDownloader", "Config", "__version__"]
