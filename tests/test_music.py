import base64
import json
from Crypto.Cipher import DES
from Crypto.Util.Padding import pad
import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock

from helpers.catalog import MusicClient, MusicError


def envelope(url):
    return base64.b64encode(DES.new(b'38346591', DES.MODE_ECB).encrypt(pad(url.encode(), 8))).decode()


def song(song_id='abc12345'):
    return dict(id=song_id, type='song', title='Song &amp; Title', perma_url='https://www.jiosaavn.com/song/title/token', image='https://c.saavncdn.com/150x150.jpg', more_info={'duration': '200', '320kbps': 'true', 'encrypted_media_url': envelope('https://aac.saavncdn.com/song_96.mp4'), 'artistMap': {'primary_artists': [{'name': 'Singer'}]}})

class Content:
    def __init__(self, chunks): self.chunks = chunks
    async def iter_chunked(self, size):
        for chunk in self.chunks:
            yield chunk

class Response:
    status = 200
    headers = {'Content-Type': 'audio/mp4'}
    def __init__(self, chunks): self.content = Content(chunks)
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass
    def raise_for_status(self): pass

class Session:
    def __init__(self, response): self.response = response
    def get(self, *args, **kwargs): return self.response

class ProviderTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.client = MusicClient(self.temp.name)
        self.client.request = AsyncMock(return_value={'results': [song()]})
    async def asyncTearDown(self):
        await self.client.close()
        self.temp.cleanup()

    async def test_search_normalization_and_cache(self):
        tracks = await self.client.search('Song')
        self.assertEqual(tracks[0]['title'], 'Song & Title')
        self.assertEqual(tracks[0]['duration'], 200)
        self.assertEqual(tracks[0]['artist'], 'Singer')
        await self.client.search('song')
        self.client.request.assert_awaited_once()

    async def test_empty_result(self):
        self.client.request.return_value = {'results': []}
        with self.assertRaises(MusicError): await self.client.resolve('unknown')

    async def test_live_dilbar_fixture_prefers_popular_film_recording(self):
        # Public search metadata captured 2026-11-03; no stream URLs or secrets.
        fixture = Path(__file__).parent / 'fixtures' / 'dilbar_search.json'
        self.client.request.return_value = json.loads(fixture.read_text())
        for query, expected in [('dilbar dilbar', 'wOTPo9Mc'),
                                ('dilbar', 'wOTPo9Mc'),
                                ('dilbar alka yagnik', '9cCPZgWV'),
                                ('dilbar sirf tum', '9cCPZgWV'),
                                ('dilbar 1999', '9cCPZgWV'),
                                ('dilbar remix', 'r_Bx8bxm')]:
            with self.subTest(query=query):
                self.assertEqual((await self.client.resolve(query))['id'], expected)
        self.client.request.assert_awaited_with('search.getResults', q='dilbar remix', n=30, p=1)

    async def test_ranking_preserves_specific_title_and_missing_metadata(self):
        exact = self.client.track(song('exact'))
        exact['title'] = 'Dilbar Mere'
        broad = dict(exact, id='broad', title='Dilbar', play_count=999999999)
        self.assertGreater(self.client.search_rank(exact, 'dilbar mere'),
                           self.client.search_rank(broad, 'dilbar mere'))
        for invalid in (None, '', 'unknown', -1):
            exact['play_count'] = invalid
            self.client.search_rank(exact, 'dilbar mere')

    async def test_selected_track_is_not_reranked(self):
        self.client.request.return_value = {'songs': [song('chosen')]}
        self.assertEqual((await self.client.resolve('track:chosen'))['id'], 'chosen')
        self.client.request.assert_awaited_once_with('song.getDetails', pids='chosen')

    async def test_reject_external_url(self):
        with self.assertRaises(MusicError): await self.client.resolve('https://evil.test/song/name/id')
        self.client.request.assert_not_awaited()

    async def test_reject_path_in_id(self):
        with self.assertRaises(MusicError): await self.client.resolve('track:../secrets')

    async def test_permalink(self):
        self.client.request.return_value = {'songs': [song()]}
        result = await self.client.resolve('https://www.jiosaavn.com/song/title/token')
        self.assertEqual(result['id'], 'abc12345')
        self.client.request.assert_awaited_with('webapi.get', token='token', type='song')

    async def test_detail_by_id(self):
        self.client.request.return_value = {'songs': [song()]}
        result = await self.client.resolve('track:abc12345')
        self.assertEqual(result['id'], 'abc12345')

    async def prepare_download(self, chunks):
        self.client.request.return_value = {'auth_url': 'https://web.saavncdn.com/song.mp4'}
        self.client.http = AsyncMock(return_value=Session(Response(chunks)))
        return self.client.track(song())

    async def test_download_and_cache(self):
        track = await self.prepare_download([b'x' * 2048])
        path = await self.client.download(track)
        self.assertEqual(Path(path).stat().st_size, 2048)
        self.assertEqual(await self.client.download(track), path)
        self.client.request.assert_not_awaited()
        self.assertEqual(list(Path(self.temp.name).glob('*.part')), [])

    async def test_size_limit_removes_partial(self):
        track = await self.prepare_download([b'x' * 2048])
        self.client.max_bytes = 1024
        with self.assertRaises(MusicError): await self.client.download(track)
        self.assertEqual(list(Path(self.temp.name).iterdir()), [])

    async def test_invalid_audio_removes_partial(self):
        track = await self.prepare_download([b'bad'])
        with self.assertRaises(MusicError): await self.client.download(track)
        self.assertEqual(list(Path(self.temp.name).iterdir()), [])

    async def test_untrusted_stream_rejected(self):
        track = self.client.track(song())
        track['encrypted_url'] = envelope('http://127.0.0.1/private')
        with self.assertRaises(MusicError): await self.client.download(track)

    async def test_simultaneous_requests_share_download(self):
        track = await self.prepare_download([b'x' * 2048])
        first, second = await asyncio.gather(self.client.download(track), self.client.download(track))
        self.assertEqual(first, second)
        self.client.request.assert_not_awaited()

    async def test_local_resolver_quality_and_https(self):
        for quality in (96, 160, 320):
            result = self.client.media_url(envelope('http://aac.saavncdn.com/42/song_96.mp4'), quality)
            self.assertEqual(result, f'https://aac.saavncdn.com/42/song_{quality}.mp4')

    async def test_malformed_and_untrusted_envelopes(self):
        for value in (None, '', 'not-base64', envelope('https://saavncdn.com.evil.test/song_96.mp4'),
                      envelope('https://user:secret@aac.saavncdn.com/song_96.mp4')):
            with self.subTest(value=value), self.assertRaises(MusicError):
                self.client.media_url(value, 320)

    async def test_download_does_not_use_auth_endpoint(self):
        track = await self.prepare_download([b'x' * 2048])
        self.client.request = AsyncMock(side_effect=AssertionError('No auth endpoint expected'))
        await self.client.download(track)
        self.client.request.assert_not_awaited()

    async def test_transient_download_retries(self):
        from helpers.catalog import DownloadError
        self.client._download_once = AsyncMock(side_effect=[DownloadError('temporary'), 'audio.m4a'])
        result = await self.client.download(self.client.track(song()))
        self.assertEqual(result, 'audio.m4a')
        self.assertEqual(self.client._download_once.await_count, 2)

if __name__ == '__main__':
    unittest.main()
