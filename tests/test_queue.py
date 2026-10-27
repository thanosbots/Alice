"""Load the queue with a fake voice client, without Telegram credentials."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock

spec = importlib.util.spec_from_file_location('queue_under_test', Path(__file__).resolve().parents[1] / 'helpers/queue.py')
queue = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {'core.clients': types.SimpleNamespace(voice=types.SimpleNamespace(leave_vc=AsyncMock()))}):
    spec.loader.exec_module(queue)

class QueueTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        queue.queues.clear()
        queue.repeat_modes.clear()
        queue.queues[1] = [{'title':'a'}, {'title':'b'}, {'title':'c'}]

    async def test_normal_advancement(self):
        self.assertEqual(queue.advance_queue(1)['title'], 'b')
        self.assertEqual(len(queue.queues[1]), 2)

    async def test_repeat_one_and_manual_skip(self):
        queue.repeat_modes[1] = 'one'
        self.assertEqual(queue.advance_queue(1)['title'], 'a')
        self.assertEqual(queue.advance_queue(1, manual=True)['title'], 'b')

    async def test_repeat_all_rotates(self):
        queue.repeat_modes[1] = 'all'
        queue.advance_queue(1)
        self.assertEqual([t['title'] for t in queue.queues[1]], ['b','c','a'])

    async def test_stop_clears_state(self):
        queue.repeat_modes[1] = 'all'
        await queue.stop_playback(1)
        self.assertNotIn(1, queue.queues)
        self.assertNotIn(1, queue.repeat_modes)

    async def test_empty(self):
        self.assertIsNone(queue.advance_queue(99))

    async def test_stop_invalidates_preparing_requests(self):
        before = queue.request_versions[1]
        await queue.stop_playback(1)
        self.assertEqual(queue.request_versions[1], before + 1)
        self.assertIsNot(queue.chat_locks[1], queue.request_locks[1])
