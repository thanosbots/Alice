import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from helpers import artwork
from helpers.thumbnail import generate_thumbnail, title_lines, font

class ArtworkTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cache = Path(self.temp.name)
        self.patch = patch.object(artwork, 'CACHE', self.cache)
        self.patch.start()
        self.cover = self.cache / 'cover.jpg'
        Image.new('RGB', (100, 100), '#fe2020').save(self.cover)
        self.track = dict(thumbnail=str(self.cover), title='A song', duration='4:00', requested_by='Listener')

    async def asyncTearDown(self):
        await artwork.close_artwork()
        self.patch.stop()
        self.temp.cleanup()

    async def test_card_contains_actual_cover_and_cache_is_reused(self):
        first = await artwork.artwork_for(self.track)
        before = Path(first).stat().st_mtime_ns
        second = await artwork.artwork_for(self.track)
        self.assertEqual(first, second)
        self.assertEqual(before, Path(second).stat().st_mtime_ns)
        with Image.open(first) as image:
            self.assertEqual(image.size, (1280, 720))
            r, g, b = image.getpixel((280, 350))
            self.assertGreater(r, 200)
            self.assertLess(g, 70)

    async def test_simultaneous_cards_share_render(self):
        with patch.object(artwork, 'generate_thumbnail', wraps=generate_thumbnail) as render:
            a, b = await asyncio.gather(artwork.artwork_for(self.track), artwork.artwork_for(self.track))
            self.assertEqual(a, b)
            self.assertEqual(render.call_count, 1)

    async def test_untrusted_remote_cover_does_not_fetch(self):
        self.track['thumbnail'] = 'https://127.0.0.1/private'
        with patch.object(artwork.aiohttp, 'ClientSession') as session:
            result = await artwork.artwork_for(self.track)
            session.assert_not_called()
        self.assertTrue(Path(result).exists())

    async def test_long_title_stays_inside_card(self):
        lines = title_lines('A very long song title ' * 30, font(48, True), 620)
        self.assertLessEqual(len(lines), 3)
        self.assertTrue(all(font(48, True).getlength(line) <= 620 for line in lines))

    async def test_broken_image_falls_back_to_record(self):
        self.cover.write_text('not an image')
        result = await artwork.artwork_for(self.track)
        with Image.open(result) as image:
            image.verify()

    async def test_remote_song_cover_is_rendered(self):
        from io import BytesIO
        data = BytesIO()
        Image.new('RGB', (100, 100), '#20fe20').save(data, 'JPEG')
        class Response:
            status = 200
            headers = {'Content-Type': 'image/jpeg'}
            content = None
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass
            async def iter_chunked(self, size): yield data.getvalue()
        response = Response()
        response.content = response
        class Session:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass
            def get(self, url, **kwargs): return response
        self.track['thumbnail'] = 'https://c.saavncdn.com/test.jpg'
        with patch.object(artwork.aiohttp, 'ClientSession', return_value=Session()):
            result = await artwork.artwork_for(self.track)
        with Image.open(result) as image:
            r, g, b = image.getpixel((280, 350))
            self.assertGreater(g, 200)
            self.assertLess(r, 70)
        self.assertFalse(list(self.cache.glob('art_*.image')))
