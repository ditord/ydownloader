from pytube import YouTube

# Ask for the YouTube video URL
url = input("Enter the YouTube video URL: ")

# Create a YouTube object
yt = YouTube(url)

# Define the download path
download_path = '/Users/arturpapyan/Downloads'

# Download video
video_stream = yt.streams.get_highest_resolution()
video_stream.download(download_path)

# Download audio
audio_stream = yt.streams.filter(only_audio=True).first()
audio_stream.download(download_path)

print(f"Downloaded video and audio to {download_path}")

