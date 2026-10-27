"""Exercise request cancellation and control concurrency without Telegram access."""
import asyncio
import importlib.util
import sys
import types
import unittest
from collections import defaultdict
from pathlib import Path
from unittest.mock import AsyncMock, patch

class PlaybackTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.state = types.SimpleNamespace(enqueue=AsyncMock(), mark_active=AsyncMock(), queues={},
            chat_locks=defaultdict(asyncio.Lock), request_locks=defaultdict(asyncio.Lock), request_versions=defaultdict(int))
        bot = types.SimpleNamespace(on_message=lambda *args: lambda handler: handler)
        self.voice = types.SimpleNamespace(join_vc=AsyncMock())
        config = types.SimpleNamespace(Config=types.SimpleNamespace(MAX_QUEUE_SIZE=10, MAX_TRACK_MINUTES=30, MAX_DOWNLOAD_MB=40))
        fake = {'config': config, 'core.clients': types.SimpleNamespace(bot=bot, assistant=None, voice=self.voice),
                'helpers.queue': self.state, 'helpers.player': types.SimpleNamespace(controls=lambda: None),
                'helpers.api': types.SimpleNamespace(resolve_audio=AsyncMock()),
                'database.chats': types.SimpleNamespace(save_chat=AsyncMock()),
                'database.users': types.SimpleNamespace(increment_play_count=AsyncMock(), save_user=AsyncMock())}
        spec = importlib.util.spec_from_file_location('play_under_test', Path(__file__).resolve().parents[1] / 'plugins/play.py')
        self.module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, fake):
            spec.loader.exec_module(self.module)
        self.status = types.SimpleNamespace(edit=AsyncMock())
        self.message = types.SimpleNamespace(chat=types.SimpleNamespace(id=1),
            from_user=types.SimpleNamespace(id=2, first_name='User'), reply_to_message=None,
            command=['play', 'song'], reply_text=AsyncMock(return_value=self.status))

    async def test_stop_during_download_cancels_commit_and_controls_are_free(self):
        started, release = asyncio.Event(), asyncio.Event()
        async def download(query):
            started.set()
            await release.wait()
            return 'audio.m4a', 'Song', '1:00', '', ''
        self.module.resolve_audio = download
        task = asyncio.create_task(self.module.play_request(None, self.message))
        await started.wait()
        # A control handler can acquire this while download is still pending.
        await asyncio.wait_for(self.state.chat_locks[1].acquire(), 0.1)
        self.state.request_versions[1] += 1
        self.state.chat_locks[1].release()
        release.set()
        await task
        self.voice.join_vc.assert_not_awaited()
        self.state.enqueue.assert_not_awaited()
        self.assertIn('cancelled', self.status.edit.call_args.args[0])

    async def test_stop_invalidates_requests_waiting_to_prepare(self):
        await self.state.request_locks[1].acquire()
        self.module.prepare_request = AsyncMock()
        task = asyncio.create_task(self.module.play_request(None, self.message))
        await asyncio.sleep(0)
        self.state.request_versions[1] += 1
        self.state.request_locks[1].release()
        await task
        self.module.prepare_request.assert_not_awaited()
