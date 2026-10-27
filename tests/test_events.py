import asyncio
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock
from collections import defaultdict

class EventTests(unittest.IsolatedAsyncioTestCase):
    async def test_only_one_transition_for_simultaneous_end_events(self):
        state = {1: [{'title': 'a'}, {'title': 'b'}]}
        locks = defaultdict(asyncio.Lock)
        async def next_track(chat_id):
            state[chat_id].pop(0)
        advance = AsyncMock(side_effect=next_track)
        handlers = []
        class Voice:
            def on_update(self, event_filter):
                def register(handler):
                    handlers.append(handler)
                    return handler
                return register
        fake_queue = types.SimpleNamespace(queues=state, mark_inactive=AsyncMock(), chat_locks=locks, repeat_modes={})
        spec = importlib.util.spec_from_file_location('events_under_test', Path(__file__).resolve().parents[1] / 'core/decorators.py')
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'helpers.queue': fake_queue, 'helpers.player': types.SimpleNamespace(advance=advance)}):
            spec.loader.exec_module(module)
        await module.register_voice_handlers(types.SimpleNamespace(vcbot=Voice()))
        await locks[1].acquire()
        event = types.SimpleNamespace(chat_id=1)
        first = asyncio.create_task(handlers[1](None, event))
        second = asyncio.create_task(handlers[1](None, event))
        await asyncio.sleep(0)
        locks[1].release()
        await asyncio.gather(first, second)
        advance.assert_awaited_once_with(1)
        self.assertEqual(state[1][0]['title'], 'b')
