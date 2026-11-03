"""Live ranking inspection without Telegram login or audio downloads."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helpers.catalog import MusicClient


async def main():
    provider = MusicClient()
    try:
        for query in sys.argv[1:] or [
            'dilbar dilbar', 'dilbar alka yagnik', 'dilbar sirf tum',
            'dilbar remix', 'dilbar mere', 'chaleya arijit singh', 'makhna',
        ]:
            tracks = await provider.search(query, 3)
            print(query, flush=True)
            for track in tracks:
                print(f"  {track['title']} | {track['artist']} | "
                      f"{track['album']} | {track['year']} | {track['id']}", flush=True)
    finally:
        await provider.close()


if __name__ == '__main__':
    asyncio.run(main())
