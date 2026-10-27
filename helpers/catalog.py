"""In-process music library provider: no third-party server or API key."""
import asyncio
import html
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import aiohttp


class MusicError(Exception):
    """An actionable music-provider failure safe to show in chat."""


class DownloadError(MusicError):
    """A transient download failure that can be retried."""


class MusicClient:
    endpoint = "https://www.jiosaavn.com/api.php"

    def __init__(self, directory="downloads", quality=320, max_mb=40):
        self.directory = Path(directory)
        self.quality = quality
        self.max_bytes = max_mb * 1024 * 1024
        self.session = None
        self.cache = {}
        self.download_lock = asyncio.Semaphore(3)
        self.inflight = {}

    async def http(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=90, connect=15, sock_read=20),
                connector=aiohttp.TCPConnector(limit=12, limit_per_host=6, ttl_dns_cache=300),
                headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.jiosaavn.com/"},
            )
        return self.session

    async def close(self):
        tasks = list(self.inflight.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        if self.session and not self.session.closed:
            await self.session.close()

    async def request(self, method, **params):
        session = await self.http()
        params.update(__call=method, _format="json", _marker="0", ctx="web6dot0", api_version="4")
        for attempt in range(3):
            try:
                async with session.get(self.endpoint, params=params) as response:
                    if response.status == 429 or response.status >= 500:
                        if attempt < 2:
                            await asyncio.sleep(1 + attempt)
                            continue
                    response.raise_for_status()
                    data = await response.json(content_type=None)
                    if not isinstance(data, dict):
                        raise MusicError("music library returned an unexpected response. Try again later.")
                    return data
            except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as exc:
                if attempt == 2:
                    raise MusicError("music library is unavailable. Please try again shortly.") from exc
                await asyncio.sleep(1 + attempt)

    @staticmethod
    def track(item):
        info = item.get("more_info") or {}
        try:
            duration = int(info.get("duration") or item.get("duration") or 0)
        except (ValueError, TypeError):
            duration = 0
        return {
            "id": str(item.get("id", "")),
            "title": html.unescape(item.get("title") or item.get("song") or "Unknown song"),
            "artist": html.unescape(", ".join(a["name"] for a in info.get("artistMap", {}).get("primary_artists", []) if a.get("name")) or item.get("subtitle", "")),
            "duration": duration,
            "link": item.get("perma_url", "https://www.jiosaavn.com"),
            "thumbnail": (item.get("image") or "").replace("150x150", "500x500"),
            "encrypted_url": info.get("encrypted_media_url") or item.get("encrypted_media_url"),
            "quality": 320 if str(info.get("320kbps", "false")).lower() == "true" else 160,
        }

    async def search(self, query, limit=5):
        query = query.strip()
        if not query or len(query) > 300:
            raise MusicError("Enter a song or artist name (up to 300 characters).")
        key = (query.casefold(), limit)
        cached = self.cache.get(key)
        if cached and cached[0] > time.monotonic():
            return cached[1]
        data = await self.request("search.getResults", q=query, n=limit, p=1)
        tracks = [self.track(i) for i in data.get("results", []) if i.get("type", "song") == "song"][:limit]
        if len(self.cache) >= 200:
            self.cache.pop(next(iter(self.cache)))
        self.cache[key] = (time.monotonic() + 300, tracks)
        return tracks

    async def resolve(self, query):
        if query.startswith("track:"):
            song_id = query[6:]
            if not re.fullmatch(r"[\w-]{1,32}", song_id):
                raise MusicError("Invalid song ID.")
            data = await self.request("song.getDetails", pids=song_id)
            songs = data.get("songs") or [v for v in data.values() if isinstance(v, dict) and v.get("id")]
        elif "://" in query:
            url = urlparse(query)
            parts = url.path.strip("/").split("/")
            if url.hostname not in {"www.jiosaavn.com", "jiosaavn.com"} or len(parts) < 3 or parts[0] != "song":
                raise MusicError("Use a music library song link, or search by song and artist name.")
            data = await self.request("webapi.get", token=parts[-1], type="song")
            songs = data.get("songs") or ([data] if data.get("id") else [])
        else:
            matches = await self.search(query, 1)
            if matches:
                return matches[0]
            songs = []
        if not songs:
            raise MusicError("No matching song found. Try a song and artist name.")
        return self.track(songs[0])

    @staticmethod
    def valid_media_url(url):
        parsed = urlparse(url)
        return parsed.scheme == "https" and (parsed.hostname or "").endswith(".saavncdn.com")

    async def download(self, track):
        key = (track['id'], min(self.quality, track['quality']))
        task = self.inflight.get(key)
        if task is None:
            task = asyncio.create_task(self._download_with_retry(track))
            self.inflight[key] = task
            def finished(done):
                self.inflight.pop(key, None)
                if not done.cancelled():
                    done.exception()  # Retrieve failures even if all callers cancelled.
            task.add_done_callback(finished)
        return await asyncio.shield(task)

    async def _download_with_retry(self, track):
        for attempt in range(3):
            try:
                return await self._download_once(track)
            except DownloadError:
                if attempt == 2:
                    raise
                await asyncio.sleep(0.5 * (2 ** attempt))

    async def _download_once(self, track):
        if not re.fullmatch(r"[\w-]{1,32}", track["id"]):
            raise MusicError("music library returned an invalid song ID.")
        quality = min(self.quality, track["quality"])
        self.directory.mkdir(parents=True, exist_ok=True)
        target = self.directory / f"audio_{track['id']}_{quality}.m4a"
        async with self.download_lock:
            if target.exists() and target.stat().st_size > 1024:
                return str(target)
            if not track["encrypted_url"]:
                raise MusicError("This track has no available audio stream.")
            auth = await self.request("song.generateAuthToken", url=track["encrypted_url"], bitrate=quality, pid=track["id"])
            url = auth.get("auth_url", "")
            if not self.valid_media_url(url):
                raise MusicError("music library could not provide an available audio stream.")
            # Unique temporary files keep concurrent downloads and interruptions safe.
            import uuid
            temporary = target.with_suffix(f".{uuid.uuid4().hex}.part")
            try:
                session = await self.http()
                async with session.get(url, allow_redirects=False) as response:
                    response.raise_for_status()
                    if response.status != 200:
                        raise MusicError("Unexpected audio redirect. Please try another song.")
                    if not any(t in response.headers.get("Content-Type", "") for t in ("audio/", "video/", "octet-stream")):
                        raise MusicError("music library returned invalid audio.")
                    size = 0
                    with temporary.open("wb") as output:
                        async for chunk in response.content.iter_chunked(256 * 1024):
                            size += len(chunk)
                            if size > self.max_bytes:
                                raise MusicError("This track exceeds the configured download size limit.")
                            output.write(chunk)
                    if size < 1024:
                        raise MusicError("The audio download was empty or incomplete.")
                temporary.replace(target)
                return str(target)
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                raise DownloadError("Audio download failed. Please try again.") from exc
            finally:
                temporary.unlink(missing_ok=True)
