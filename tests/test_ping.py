import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch


class PingTests(unittest.IsolatedAsyncioTestCase):
    async def test_ping_reports_measured_response_before_artwork(self):
        bot = SimpleNamespace(on_message=lambda *args: lambda fn: fn)
        spec = importlib.util.spec_from_file_location('ping_test', Path('plugins/ping.py'))
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'core.clients': SimpleNamespace(bot=bot)}):
            spec.loader.exec_module(module)
        reply = object()
        client = SimpleNamespace(send_message=AsyncMock(return_value=reply))
        message = SimpleNamespace(chat=SimpleNamespace(id=-123))
        with patch.object(module, 'perf_counter', side_effect=[10, 10.125]), \
                patch.object(module, 'edit_panel', new_callable=AsyncMock) as edit:
            await module.ping_command(client, message)
        self.assertEqual(client.send_message.call_args.args[0], -123)
        self.assertIs(edit.call_args.args[0], reply)
        self.assertIn('PONG!', edit.call_args.args[1])
        self.assertIn(module.VERSION, edit.call_args.args[1])
        self.assertIn('125 ms', edit.call_args.args[1])
        self.assertEqual(edit.call_args.kwargs['image'], 'assets/alice-ping-v2.png')
