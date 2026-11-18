import importlib.util
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch, AsyncMock
from pyrogram.enums import ChatType
from helpers import diagnostics as d

class DiagnosticsTests(unittest.TestCase):
    def test_redacts_credentials_and_urls(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(d, 'ROOT', Path(folder)), patch.dict(os.environ, {'STRING_SESSION': 'private-session-value'}):
            (Path(folder) / 'Config.env').write_text('API_HASH=privatehash\n')
            result = d.redact('private-session-value privatehash https://user:pass@host/path?token=abc 123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabc\npassword=hidden')
        for secret in ('private-session-value','privatehash','user:pass','ABCDEFGHIJKLMNOPQRSTUVWXYZ','hidden'):
            self.assertNotIn(secret, result)

    def test_bounded_tail(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(d, 'ROOT', Path(folder)):
            (Path(folder) / 'alice_logs.txt').write_text('old\n' * 50000 + 'last\n')
            self.assertEqual(d.log_snapshot(2), 'old\nlast')

class LogsAccessTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        spec = importlib.util.spec_from_file_location('logs_under_test', 'plugins/logs.py')
        self.module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'core.clients': NS(bot=NS(on_message=lambda *a: lambda f:f)), 'config': NS(Config=NS(OWNER_ID=42))}):
            spec.loader.exec_module(self.module)

    def message(self, user=42, kind=ChatType.PRIVATE, args=None):
        return NS(from_user=NS(id=user), chat=NS(id=user,type=kind),command=['logs']+(args or []),reply_text=AsyncMock(),reply_document=AsyncMock())

    async def test_only_private_owner_reads_logs(self):
        with patch.object(self.module,'log_snapshot',return_value='safe log') as read:
            await self.module.logs_command(None,self.message(7))
            await self.module.logs_command(None,self.message(kind=ChatType.SUPERGROUP))
            read.assert_not_called()
            m=self.message();await self.module.logs_command(None,m)
            m.reply_text.assert_awaited_once()

    async def test_rejects_paths_and_oversized_requests(self):
        with patch.object(self.module,'log_snapshot') as read:
            for args in (['Config.env'], ['501'], ['0'], ['10','extra']):
                await self.module.logs_command(None,self.message(args=args))
            read.assert_not_called()

    async def test_large_logs_are_sent_as_sanitized_document(self):
        with patch.object(self.module,'log_snapshot',return_value='safe\n'*1000):
            m=self.message();await self.module.logs_command(None,m)
            m.reply_document.assert_awaited_once()
            self.assertEqual(m.reply_document.call_args.args[0].getvalue(),b'safe\n'*1000)
