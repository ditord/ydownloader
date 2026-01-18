# YDownloader

A modern YouTube downloader with CLI and interactive TUI.

## Features

- **Video & Audio Downloads**: Download videos in various qualities or extract audio only
- **Quality Selection**: Choose specific video quality (720p, 1080p, etc.)
- **Format Options**: Support for mp4, mkv, webm (video) and mp3, m4a, opus, flac (audio)
- **Playlist Support**: Download entire playlists or specific ranges
- **Subtitles**: Download and embed subtitles (including auto-generated)
- **Metadata Embedding**: Automatically embed video metadata and thumbnails
- **Interactive TUI**: Beautiful Rich-based terminal interface
- **Progress Tracking**: Real-time download progress with speed and ETA

## Installation

```bash
pip install .
```

Or for development:

```bash
pip install -e .
```

### Requirements

- Python 3.9+
- ffmpeg (for audio extraction and format conversion)

To install ffmpeg:
- macOS: `brew install ffmpeg`
- Ubuntu/Debian: `sudo apt install ffmpeg`
- Windows: Download from https://ffmpeg.org

## Usage

### Command Line

```bash
# Download video (highest quality)
ydownloader https://youtube.com/watch?v=VIDEO_ID

# Download audio only
ydownloader -a https://youtube.com/watch?v=VIDEO_ID

# Download in specific quality
ydownloader -q 720p https://youtube.com/watch?v=VIDEO_ID

# Download with subtitles
ydownloader --subs https://youtube.com/watch?v=VIDEO_ID

# Download playlist
ydownloader https://youtube.com/playlist?list=PLAYLIST_ID

# Specify output directory
ydownloader -o ~/Videos https://youtube.com/watch?v=VIDEO_ID
```

### Interactive Mode

Launch the interactive TUI:

```bash
ydownloader -i
# or just
ydownloader
```

### All Options

```
Usage: ydownloader [OPTIONS] [URL]

Options:
  -i, --interactive      Run in interactive TUI mode
  -a, --audio           Download audio only
  -q, --quality         Video quality (best, worst, 720p, 1080p)
  --audio-quality       Audio quality (best, worst, 192k, 320k)
  -f, --format          Video format (mp4, mkv, webm)
  --audio-format        Audio format (mp3, m4a, opus, flac)
  -o, --output          Output directory (default: ~/Downloads)
  --subs                Download subtitles
  --subs-lang           Subtitle language(s) (default: en)
  --embed-subs          Embed subtitles in video
  --embed-thumbnail     Embed thumbnail in file
  --no-metadata         Don't embed metadata
  --no-playlist         Download only video, not playlist
  --playlist-start      Start playlist at video N
  --playlist-end        End playlist at video N
  -r, --rate-limit      Download rate limit (e.g., 1M, 500K)
  --quiet               Suppress output
  -v, --verbose         Verbose output
  --version             Show version
```

## Examples

### Download audio as MP3

```bash
ydownloader -a --audio-format mp3 https://youtube.com/watch?v=VIDEO_ID
```

### Download video with embedded subtitles and thumbnail

```bash
ydownloader --subs --embed-subs --embed-thumbnail https://youtube.com/watch?v=VIDEO_ID
```

### Download playlist videos 5-10

```bash
ydownloader --playlist-start 5 --playlist-end 10 https://youtube.com/playlist?list=PLAYLIST_ID
```

### Limit download speed

```bash
ydownloader -r 1M https://youtube.com/watch?v=VIDEO_ID
```

## License

MIT
