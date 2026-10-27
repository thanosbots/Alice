"""Bounded, cached album artwork. Never called before starting audio."""
import asyncio
import hashlib
import logging
from pathlib import Path
from urllib.parse import urlparse
import aiohttp
from helpers.thumbnail import generate_thumbnail

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'downloads'
_slots = asyncio.Semaphore(2)
_jobs = {}
_notices = set()
log = logging.getLogger(__name__)

async def _build(track):
    source = str(track.get('thumbnail') or '')
    identity = '\0'.join((source, str(track['title']), str(track['duration']), str(track['requested_by']), str(bool(track.get('is_owner')))))
    key = hashlib.sha256(identity.encode()).hexdigest()[:24]
    target = CACHE / f'card_{key}.jpg'
    if target.exists():
        return str(target)
    async with _slots:
        CACHE.mkdir(exist_ok=True)
        cover = CACHE / f'art_{key}.image'
        local_cover = None
        try:
            parsed = urlparse(source)
            if parsed.scheme == 'https' and (parsed.hostname or '').endswith('.saavncdn.com'):
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5, connect=2)) as session:
                    async with session.get(source, allow_redirects=False) as response:
                        if response.status != 200 or not response.headers.get('Content-Type', '').startswith('image/'):
                            raise ValueError('Artwork unavailable')
                        size = 0
                        with cover.open('wb') as output:
                            async for chunk in response.content.iter_chunked(64 * 1024):
                                size += len(chunk)
                                if size > 5 * 1024 * 1024:
                                    raise ValueError('Artwork too large')
                                output.write(chunk)
                        local_cover = cover
            elif not parsed.scheme and source:
                candidate = Path(source).resolve()
                # Only bot-managed local media can become cover art.
                if candidate.is_relative_to(CACHE.resolve()) and candidate.is_file():
                    local_cover = candidate
        except (aiohttp.ClientError, asyncio.TimeoutError, OSError, ValueError):
            pass
        try:
            result = await asyncio.to_thread(generate_thumbnail, local_cover or '', track['title'],
                                            track['duration'], 0, track['requested_by'], 'Alice', target, owner=bool(track.get('is_owner')))
            # Do not cache transient remote-image failures forever.
            if local_cover is None and source.startswith('https:'):
                fallback = target.with_name('fallback_' + target.name)
                target.replace(fallback)
                return str(fallback)
            return result
        finally:
            cover.unlink(missing_ok=True)

async def artwork_for(track):
    key = tuple(str(track.get(k, '')) for k in ('thumbnail', 'title', 'duration', 'requested_by', 'is_owner'))
    task = _jobs.get(key)
    if task is None:
        task = asyncio.create_task(_build(track))
        _jobs[key] = task
        def done(job):
            _jobs.pop(key, None)
            if not job.cancelled():
                job.exception()
        task.add_done_callback(done)
    try:
        return await asyncio.shield(task)
    except Exception:
        return str(ROOT / 'assets/lounge.jpg')

def background_notice(coroutine):
    task = asyncio.create_task(coroutine)
    _notices.add(task)
    def done(job):
        _notices.discard(job)
        if not job.cancelled() and job.exception():
            log.debug('Playback card could not be delivered')
    task.add_done_callback(done)
    return task

async def close_artwork():
    for task in list(_notices):
        task.cancel()
    await asyncio.gather(*list(_notices), return_exceptions=True)
    # Let short, bounded artwork workers finish before executor shutdown.
    await asyncio.gather(*list(_jobs.values()), return_exceptions=True)
