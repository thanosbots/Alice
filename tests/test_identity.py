import contextlib
import io
import logging
import os
import sys
import types
import unittest
from unittest.mock import patch
from pyrogram.parser.html import HTML
from helpers.identity import is_owner, selection_name
from helpers.style import home, track_card
from helpers.terminal import banner, ConsoleFormatter

class IdentityTests(unittest.IsolatedAsyncioTestCase):
    def test_only_numeric_owner_id_gets_special_identity(self):
        with patch.dict(sys.modules, {'config': types.SimpleNamespace(Config=types.SimpleNamespace(OWNER_ID=42))}):
            owner = types.SimpleNamespace(id=42, username='changed', first_name='Changed')
            impostor = types.SimpleNamespace(id=7, username='thanosceo', first_name='Rishabh Anand')
            self.assertTrue(is_owner(owner))
            self.assertFalse(is_owner(impostor))
            self.assertFalse(is_owner(None))
            self.assertIn('Creator', selection_name(owner))
            self.assertNotIn('Creator', selection_name(impostor))

    async def test_owner_cards_fit_telegram_captions(self):
        track = dict(title='<b>Song</b>' * 40, duration='4:00', requested_by='♛ Rishabh Anand · Creator', is_owner=True)
        for text in (home('Alice', owner=True), track_card(track)):
            parsed = await HTML(None).parse(text)
            self.assertLess(len(parsed['message'].encode('utf-16-le')) // 2, 1024)
            self.assertIn('Rishabh', parsed['message'])

    def test_mobile_and_desktop_banner_width_and_no_color(self):
        for columns in (36, 80, 120):
            output = io.StringIO()
            with patch('helpers.terminal.shutil.get_terminal_size', return_value=os.terminal_size((columns, 24))), patch.dict(os.environ, {'NO_COLOR': '1'}), contextlib.redirect_stdout(output):
                banner('Alice Music Bot', '2.0', ready=True)
            text = output.getvalue()
            self.assertIn('Rishabh Anand', text)
            self.assertNotIn('\x1b', text)
            self.assertTrue(all(len(line) <= columns for line in text.splitlines()))

    def test_console_log_wraps_without_ansi_in_redirected_output(self):
        record = logging.LogRecord('Alice', logging.INFO, '', 1, 'Creator Rishabh Anand · voice engine connected and ready', (), None)
        with patch('helpers.terminal.shutil.get_terminal_size', return_value=os.terminal_size((40, 24))):
            text = ConsoleFormatter(io.StringIO()).format(record)
        self.assertNotIn('\x1b', text)
        self.assertTrue(all(len(line) <= 40 for line in text.splitlines()))
