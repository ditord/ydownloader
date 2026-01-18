"""Command-line interface for YDownloader."""

import argparse
import sys
from pathlib import Path

from rich.console import Console

from ydownloader import __version__
from ydownloader.config import Config
from ydownloader.tui import interactive_mode, download_with_progress_cli


console = Console()


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog="ydownloader",
        description="A modern YouTube downloader with CLI and interactive TUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ydownloader https://youtube.com/watch?v=...          Download video
  ydownloader -a https://youtube.com/watch?v=...       Download audio only
  ydownloader -q 720p https://youtube.com/watch?v=...  Download in 720p
  ydownloader -i                                       Interactive mode
  ydownloader --subs https://youtube.com/watch?v=...   Download with subtitles
        """,
    )

    # Positional arguments
    parser.add_argument(
        "url",
        nargs="?",
        help="YouTube URL to download (video or playlist)",
    )

    # Mode selection
    mode_group = parser.add_argument_group("Mode")
    mode_group.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive TUI mode",
    )

    # Download type
    type_group = parser.add_argument_group("Download Type")
    type_group.add_argument(
        "-a", "--audio",
        action="store_true",
        help="Download audio only",
    )

    # Quality options
    quality_group = parser.add_argument_group("Quality")
    quality_group.add_argument(
        "-q", "--quality",
        default="best",
        metavar="QUALITY",
        help="Video quality (best, worst, 720p, 1080p, etc). Default: best",
    )
    quality_group.add_argument(
        "--audio-quality",
        default="best",
        metavar="QUALITY",
        help="Audio quality (best, worst, 192k, 320k, etc). Default: best",
    )

    # Format options
    format_group = parser.add_argument_group("Format")
    format_group.add_argument(
        "-f", "--format",
        dest="video_format",
        default="mp4",
        choices=["mp4", "mkv", "webm"],
        help="Video format. Default: mp4",
    )
    format_group.add_argument(
        "--audio-format",
        default="mp3",
        choices=["mp3", "m4a", "opus", "flac", "wav"],
        help="Audio format (when using --audio). Default: mp3",
    )

    # Output options
    output_group = parser.add_argument_group("Output")
    output_group.add_argument(
        "-o", "--output",
        type=Path,
        default=Path.home() / "Downloads",
        metavar="DIR",
        help="Output directory. Default: ~/Downloads",
    )
    output_group.add_argument(
        "--filename",
        default="%(title)s.%(ext)s",
        metavar="TEMPLATE",
        help="Filename template. Default: %%(title)s.%%(ext)s",
    )

    # Embedding options
    embed_group = parser.add_argument_group("Embedding")
    embed_group.add_argument(
        "--embed-thumbnail",
        action="store_true",
        help="Embed thumbnail in the file",
    )
    embed_group.add_argument(
        "--no-metadata",
        action="store_true",
        help="Don't embed metadata",
    )

    # Subtitle options
    subs_group = parser.add_argument_group("Subtitles")
    subs_group.add_argument(
        "--subs",
        action="store_true",
        help="Download subtitles",
    )
    subs_group.add_argument(
        "--subs-lang",
        default="en",
        metavar="LANG",
        help="Subtitle language(s), comma-separated. Default: en",
    )
    subs_group.add_argument(
        "--embed-subs",
        action="store_true",
        help="Embed subtitles in the video",
    )
    subs_group.add_argument(
        "--no-auto-subs",
        action="store_true",
        help="Don't include auto-generated subtitles",
    )

    # Playlist options
    playlist_group = parser.add_argument_group("Playlist")
    playlist_group.add_argument(
        "--no-playlist",
        action="store_true",
        help="Download only the video, not the playlist",
    )
    playlist_group.add_argument(
        "--playlist-start",
        type=int,
        metavar="N",
        help="Start playlist at video N",
    )
    playlist_group.add_argument(
        "--playlist-end",
        type=int,
        metavar="N",
        help="End playlist at video N",
    )

    # Network options
    net_group = parser.add_argument_group("Network")
    net_group.add_argument(
        "-r", "--rate-limit",
        metavar="RATE",
        help="Download rate limit (e.g., 1M, 500K)",
    )
    net_group.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Number of retries. Default: 3",
    )

    # Output control
    parser.add_argument(
        "--quiet",
        action="store_true",
        dest="quiet_mode",
        help="Suppress output (only errors)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser


def build_config(args: argparse.Namespace) -> Config:
    """Build Config object from parsed arguments."""
    return Config(
        output_dir=args.output,
        filename_template=args.filename,
        audio_only=args.audio,
        quality=args.quality,
        audio_quality=args.audio_quality,
        video_format=args.video_format,
        audio_format=args.audio_format,
        embed_metadata=not args.no_metadata,
        embed_thumbnail=args.embed_thumbnail,
        embed_subtitles=args.embed_subs,
        download_subtitles=args.subs or args.embed_subs,
        subtitle_langs=args.subs_lang.split(","),
        auto_subtitles=not args.no_auto_subs,
        playlist=not args.no_playlist,
        playlist_start=args.playlist_start,
        playlist_end=args.playlist_end,
        rate_limit=args.rate_limit,
        retries=args.retries,
        quiet=args.quiet_mode,
        verbose=args.verbose,
    )


def main():
    """Main entry point for CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Interactive mode
    if args.interactive:
        interactive_mode()
        return

    # Require URL if not in interactive mode
    if not args.url:
        # If no arguments at all, launch interactive mode
        if len(sys.argv) == 1:
            interactive_mode()
            return

        parser.print_help()
        sys.exit(1)

    # Build config and download
    config = build_config(args)

    try:
        download_with_progress_cli(args.url, config, quiet=args.quiet_mode)
    except KeyboardInterrupt:
        console.print("\n[yellow]Download cancelled.[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
