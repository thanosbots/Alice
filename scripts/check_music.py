"""Read-only provider smoke check; never connects to Telegram."""
import asyncio
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helpers.catalog import MusicClient

async def main():
    scratch = tempfile.TemporaryDirectory(prefix="alice-music-check-")
    provider = MusicClient(directory=scratch.name)
    try:
        tracks = await provider.search('Chaleya Arijit Singh', 3)
        if not tracks:
            raise RuntimeError('No search results')
        print(f'Search OK: {len(tracks)} results')
        track = await provider.resolve('track:' + tracks[0]['id'])
        print(f'Song details OK: {track["title"]}')
        linked = await provider.resolve(track['link'])
        assert linked['id'] == track['id'], 'Song permalink mismatch'
        print('Song link OK')
        path = await provider.download(track)
        print(f'Audio download OK: {path} ({Path(path).stat().st_size} bytes)')
    finally:
        await provider.close()
        scratch.cleanup()

asyncio.run(main())
