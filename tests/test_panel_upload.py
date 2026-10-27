import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from pyrogram import raw
from helpers.panel_upload import upload_photo, PART_SIZE


class PanelUploadTests(unittest.IsolatedAsyncioTestCase):
    async def test_parts_use_existing_connection_and_return_reusable_id(self):
        data = b'x' * (PART_SIZE + 20)
        client = SimpleNamespace(rnd_id=lambda: 42, invoke=AsyncMock(
            side_effect=[True, True, SimpleNamespace(photo=object())]),
            resolve_peer=AsyncMock(return_value='peer'))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'panel.png'
            path.write_bytes(data)
            with patch('helpers.panel_upload.Photo._parse', return_value=SimpleNamespace(file_id='cached')):
                self.assertEqual(await upload_photo(client, 7, path), 'cached')
        calls = [call.args[0] for call in client.invoke.call_args_list]
        self.assertIsInstance(calls[0], raw.functions.upload.SaveFilePart)
        self.assertEqual([calls[0].file_part, calls[1].file_part], [0, 1])
        self.assertEqual(calls[0].bytes + calls[1].bytes, data)
        self.assertEqual(calls[2].media.file.parts, 2)
        self.assertEqual(calls[2].media.file.md5_checksum, hashlib.md5(data).hexdigest())

    async def test_failed_part_does_not_attach_incomplete_photo(self):
        client = SimpleNamespace(rnd_id=lambda: 42, invoke=AsyncMock(return_value=False))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'panel.png'
            path.write_bytes(b'image')
            with self.assertRaisesRegex(RuntimeError, 'rejected'):
                await upload_photo(client, 7, path)
        client.invoke.assert_awaited_once()
