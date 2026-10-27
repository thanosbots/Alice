import ast
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from pyrogram.enums import ChatType
from pyrogram.parser.html import HTML
from helpers.access import private_owner
from helpers.style import help_screen, PAGES, OWNER_PAGES

class OwnerHelpTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        bot = types.SimpleNamespace(on_message=lambda *a: lambda f: f, on_callback_query=lambda *a: lambda f: f)
        spec = importlib.util.spec_from_file_location('callbacks_test', Path(__file__).resolve().parents[1] / 'plugins/callbacks.py')
        self.module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'config': types.SimpleNamespace(Config=types.SimpleNamespace(OWNER_ID=42)), 'core.clients': types.SimpleNamespace(bot=bot)}):
            spec.loader.exec_module(self.module)
        self.module.edit_panel = AsyncMock()

    def query(self, user=7, chat_id=7, kind=ChatType.PRIVATE, data='guide_owner_stats'):
        return types.SimpleNamespace(from_user=types.SimpleNamespace(id=user), data=data, answer=AsyncMock(),
            message=types.SimpleNamespace(chat=types.SimpleNamespace(id=chat_id, type=kind)))

    async def test_owner_commands_absent_from_public_help(self):
        for page in [None, *PAGES, *OWNER_PAGES]:
            text, keyboard = help_screen(page)
            for command in ('/stats', '/dbstats', '/top', '/broadcast', '/cleanusers', '/cleanchats'):
                self.assertNotIn(command, text)
            self.assertFalse(any('owner_' in button.callback_data for row in keyboard.inline_keyboard for button in row))

    async def test_owner_screens_fit_caption(self):
        for page in OWNER_PAGES:
            parsed = await HTML(None).parse(help_screen(page, owner=True)[0])
            self.assertLess(len(parsed['message'].encode('utf-16-le')) // 2, 1024)

    async def test_forged_and_legacy_callbacks_denied(self):
        for data in ('guide_owner_stats', 'guide_owner_database', 'hcat_🗄 DB Admin', 'hcat_📣 Broadcast'):
            query = self.query(data=data)
            await self.module.navigation(None, query)
            self.assertTrue(query.answer.call_args.kwargs['show_alert'])
        self.module.edit_panel.assert_not_awaited()

    async def test_owner_cannot_render_private_page_in_group(self):
        await self.module.navigation(None, self.query(42, -1001, ChatType.SUPERGROUP))
        self.module.edit_panel.assert_not_awaited()

    async def test_owner_can_open_private_page(self):
        await self.module.navigation(None, self.query(42, 42))
        self.module.edit_panel.assert_awaited_once()
        self.assertIn('/stats', self.module.edit_panel.call_args.args[1])

    async def test_command_help_covers_actual_handlers(self):
        commands = set()
        for path in Path('plugins').glob('*.py'):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'command':
                    value = ast.literal_eval(node.args[0])
                    commands.update([value] if isinstance(value, str) else value)
        text = help_screen(owner=True)[0] + '\n'.join(body for _, body in [*PAGES.values(), *OWNER_PAGES.values()])
        self.assertEqual(commands - {cmd for cmd in commands if '/' + cmd in text}, set())
