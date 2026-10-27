"""Compatibility bridge for the built-in music provider."""
from config import Config
from helpers.catalog import MusicClient, MusicError

provider = MusicClient(quality=Config.MUSIC_QUALITY, max_mb=Config.MAX_DOWNLOAD_MB)

async def close_catalog():
    await provider.close()

async def resolve_audio(query, _iv=False):
    if _iv:
        raise MusicError("music library provides audio. Video playback is not supported.")
    track = await provider.resolve(query)
    if track["duration"] > Config.MAX_TRACK_MINUTES * 60:
        raise MusicError(f"Choose a track shorter than {Config.MAX_TRACK_MINUTES} minutes.")
    path = await provider.download(track)
    from helpers.media import validate_audio
    try:
        await validate_audio(path, Config.MAX_TRACK_MINUTES * 60)
    except MusicError:
        from pathlib import Path
        Path(path).unlink(missing_ok=True)
        raise
    duration = f"{track['duration'] // 60}:{track['duration'] % 60:02d}"
    return path, track['title'], duration, track['link'], track['thumbnail']
