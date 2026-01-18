"""Rich-based TUI for interactive mode."""

import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    TaskID,
)
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from rich import box

from ydownloader.config import Config
from ydownloader.downloader import YDownloader, VideoInfo


console = Console()


def format_bytes(size: float) -> str:
    """Format bytes to human readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def print_header():
    """Print application header."""
    console.print()
    console.print(
        Panel(
            "[bold cyan]YDownloader[/bold cyan] [dim]v2.0.0[/dim]\n"
            "[dim]A modern YouTube downloader[/dim]",
            box=box.ROUNDED,
            padding=(0, 2),
        )
    )
    console.print()


def print_video_info(info: VideoInfo):
    """Display video information in a formatted panel."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="bold cyan")
    table.add_column("Value")

    if info.is_playlist:
        table.add_row("Playlist", info.playlist_title or "Unknown")
        table.add_row("Videos", str(info.playlist_count))
    else:
        table.add_row("Title", info.title)
        table.add_row("Channel", info.channel)
        table.add_row("Duration", info.duration_formatted)
        table.add_row("Views", info.views_formatted)

        qualities = info.available_qualities()
        if qualities:
            table.add_row("Quality", ", ".join(qualities[:5]))

    console.print(Panel(table, title="[bold]Video Info[/bold]", box=box.ROUNDED))


def select_option(prompt: str, options: list[str], default: int = 0) -> str:
    """Display options and let user select one."""
    console.print(f"\n[bold]{prompt}[/bold]")
    for i, opt in enumerate(options):
        marker = "[cyan]>[/cyan]" if i == default else " "
        console.print(f"  {marker} [{i + 1}] {opt}")

    while True:
        choice = Prompt.ask(
            "Select option",
            default=str(default + 1),
            console=console,
        )
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass
        console.print("[red]Invalid selection. Try again.[/red]")


def interactive_mode():
    """Run interactive TUI mode."""
    print_header()

    while True:
        # Get URL
        console.print("[bold cyan]Enter YouTube URL[/bold cyan] [dim](or 'quit' to exit)[/dim]")
        url = Prompt.ask(">", console=console).strip()

        if url.lower() in ("quit", "exit", "q"):
            console.print("\n[dim]Goodbye![/dim]\n")
            break

        if not url:
            console.print("[yellow]Please enter a URL.[/yellow]")
            continue

        if not YDownloader.is_valid_url(url):
            console.print("[red]Invalid YouTube URL. Please try again.[/red]")
            continue

        # Fetch video info
        downloader = YDownloader()

        with console.status("[bold cyan]Fetching video info...[/bold cyan]"):
            try:
                info = downloader.get_info(url)
            except Exception as e:
                console.print(f"[red]Error fetching video info: {e}[/red]")
                continue

        print_video_info(info)

        # Select download type
        download_type = select_option(
            "What would you like to download?",
            ["Video (highest quality)", "Video (select quality)", "Audio only"],
            default=0,
        )

        config = Config()

        if "Audio" in download_type:
            config.audio_only = True
            audio_format = select_option(
                "Select audio format:",
                ["mp3", "m4a", "opus", "flac"],
                default=0,
            )
            config.audio_format = audio_format

        elif "select quality" in download_type:
            qualities = info.available_qualities()
            if qualities:
                quality = select_option("Select video quality:", qualities, default=0)
                config.quality = quality
            else:
                console.print("[yellow]No quality info available, using best.[/yellow]")

        # Ask about subtitles
        if Confirm.ask("Download subtitles?", default=False, console=console):
            config.download_subtitles = True
            if Confirm.ask("Embed subtitles in video?", default=True, console=console):
                config.embed_subtitles = True

        # Ask about thumbnail
        if Confirm.ask("Embed thumbnail?", default=False, console=console):
            config.embed_thumbnail = True

        # Output directory
        default_dir = str(Path.home() / "Downloads")
        output = Prompt.ask(
            "Output directory",
            default=default_dir,
            console=console,
        )
        config.output_dir = Path(output).expanduser()

        # Confirm and download
        console.print()
        if not Confirm.ask("Start download?", default=True, console=console):
            console.print("[dim]Download cancelled.[/dim]")
            continue

        # Download with progress
        _download_with_progress(downloader, url, config, info)

        console.print()
        if not Confirm.ask("Download another?", default=True, console=console):
            console.print("\n[dim]Goodbye![/dim]\n")
            break


def _download_with_progress(
    downloader: YDownloader,
    url: str,
    config: Config,
    info: VideoInfo,
):
    """Download with Rich progress bar."""
    console.print()

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    )

    task_id: Optional[TaskID] = None
    current_status = {"last_percent": 0}

    def on_progress(progress_info: dict):
        nonlocal task_id

        if progress_info["status"] == "downloading":
            total = progress_info["total_bytes"]
            downloaded = progress_info["downloaded_bytes"]
            percent = progress_info["percent"]

            if task_id is None:
                task_id = progress.add_task(
                    description=info.title[:50] + "..." if len(info.title) > 50 else info.title,
                    total=total or 100,
                )
            else:
                progress.update(task_id, completed=downloaded if total else percent)

            current_status["last_percent"] = percent

        elif progress_info["status"] == "processing":
            if task_id is not None:
                progress.update(task_id, description="[yellow]Processing...[/yellow]")

    downloader.set_progress_callback(on_progress=on_progress)

    try:
        with progress:
            files = downloader.download(url, config)

        console.print()
        console.print(
            Panel(
                f"[bold green]Download complete![/bold green]\n\n"
                f"[dim]Saved to:[/dim] {config.output_dir}",
                box=box.ROUNDED,
            )
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Download cancelled.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Download failed: {e}[/red]")


def download_with_progress_cli(
    url: str,
    config: Config,
    quiet: bool = False,
):
    """Download with progress bar for CLI mode."""
    downloader = YDownloader(config)

    if quiet:
        downloader.download(url, config)
        return

    # Fetch info first
    with console.status("[bold cyan]Fetching video info...[/bold cyan]"):
        try:
            info = downloader.get_info(url)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)

    # Print info
    if info.is_playlist:
        console.print(
            f"[bold]Playlist:[/bold] {info.playlist_title} "
            f"[dim]({info.playlist_count} videos)[/dim]"
        )
    else:
        console.print(f"[bold]Title:[/bold] {info.title}")
        console.print(f"[bold]Channel:[/bold] {info.channel}")
        console.print(f"[bold]Duration:[/bold] {info.duration_formatted}")
    console.print()

    _download_with_progress(downloader, url, config, info)
