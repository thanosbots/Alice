import tempfile
import unittest
import wave
from pathlib import Path
from helpers.media import validate_audio
from helpers.catalog import MusicError

class MediaTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_audio_and_duration_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.wav'
            with wave.open(str(path), 'wb') as output:
                output.setnchannels(2)
                output.setsampwidth(2)
                output.setframerate(48000)
                output.writeframes(b'\0' * 48000 * 4)
            await validate_audio(path, 2)
            with self.assertRaises(MusicError):
                await validate_audio(path, 0.5)

    async def test_reject_large_but_invalid_cached_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.m4a'
            path.write_bytes(b'x' * 4096)
            with self.assertRaises(MusicError):
                await validate_audio(path)
