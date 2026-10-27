import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from pyrogram.parser.html import HTML
from pyrogram.raw.types import MessageEntityBlockquote
from helpers.style import help_screen, home, track_card, edit_panel
from helpers.version import VERSION

class PresentationTests(unittest.IsolatedAsyncioTestCase):
    def test_welcome_displays_current_version_for_everyone(self):
        for owner in (True, False):
            self.assertIn(VERSION, home("Alice", owner=owner))

    async def test_help_fits_photo_and_supports_expandable_quotes(self):
        for page in (None, 'listen', 'controls', 'queue', 'care'):
            text, buttons = help_screen(page)
            parsed = await HTML(None).parse(text)
            self.assertLess(len(parsed['message'].encode('utf-16-le')) // 2, 1024)
            self.assertTrue(any(isinstance(e, MessageEntityBlockquote) for e in parsed['entities']))
            if page in ('listen', 'queue', 'care'):
                self.assertTrue(any(getattr(e, 'collapsed', False) for e in parsed['entities']))
            for row in buttons.inline_keyboard:
                for button in row:
                    self.assertLessEqual(len(button.callback_data.encode()), 64)

    async def test_untrusted_track_has_no_link_or_markup_injection(self):
        text = track_card({'title': '<a href="https://bad.test">Song</a>', 'duration': '1:20', 'requested_by': '<b>user</b>'})
        parsed = await HTML(None).parse(text)
        self.assertIn('<b>user</b>', parsed['message'])
        self.assertNotIn('MessageEntityTextUrl', [type(e).__name__ for e in parsed['entities']])

    async def test_photo_navigation_edits_caption(self):
        message = SimpleNamespace(chat=SimpleNamespace(id=-123), id=1, photo=True, edit_caption=AsyncMock(), edit_text=AsyncMock())
        await edit_panel(message, *help_screen())
        message.edit_caption.assert_awaited_once()
        message.edit_text.assert_not_awaited()
