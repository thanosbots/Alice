"""Bounded local audio inspection before handing a file to the voice engine."""
import asyncio
import json
import math
from helpers.catalog import MusicError

async def validate_audio(path, max_duration=3600):
    process = await asyncio.create_subprocess_exec(
        'ffprobe', '-v', 'error', '-select_streams', 'a:0',
        '-show_entries', 'stream=codec_type:format=duration', '-of', 'json', str(path),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        output, _ = await asyncio.wait_for(process.communicate(), timeout=15)
        data = json.loads(output)
        duration = float(data.get('format', {}).get('duration', 0))
        if process.returncode or not data.get('streams') or (not math.isfinite(duration) or duration <= 0):
            raise ValueError('Invalid audio')
        if duration > max_duration:
            raise MusicError('Choose a shorter audio file for this listening room.')
    except (ValueError, asyncio.TimeoutError) as exc:
        raise MusicError('This audio is incomplete or cannot be played. Try another result.') from exc
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()
