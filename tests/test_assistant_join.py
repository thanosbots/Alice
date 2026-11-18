import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock
from pyrogram import errors
from pyrogram.enums import ChatMemberStatus as S
from helpers.assistant_join import ensure_assistant_joined

class JoinTests(unittest.IsolatedAsyncioTestCase):
    def setup_clients(self, status=S.LEFT):
        bot = NS(get_chat_member=AsyncMock(side_effect=[NS(status=status), NS(status=S.ADMINISTRATOR, privileges=NS(can_invite_users=True))]), create_chat_invite_link=AsyncMock(return_value=NS(invite_link='https://t.me/+test')), revoke_chat_invite_link=AsyncMock(), approve_chat_join_request=AsyncMock())
        assistant = NS(id=42, join_chat=AsyncMock())
        return bot, assistant

    async def test_left_member_joins_and_temporary_link_is_revoked(self):
        bot, assistant = self.setup_clients()
        await ensure_assistant_joined(bot, assistant, NS(id=-1001))
        assistant.join_chat.assert_awaited_once_with('https://t.me/+test')
        bot.revoke_chat_invite_link.assert_awaited_once()

    async def test_unknown_member_joins(self):
        bot, assistant = self.setup_clients()
        bot.get_chat_member.side_effect = [errors.UserNotParticipant(), NS(status=S.OWNER)]
        await ensure_assistant_joined(bot, assistant, NS(id=-1001))
        assistant.join_chat.assert_awaited_once()

    async def test_existing_member_does_not_join(self):
        bot, assistant = self.setup_clients(S.MEMBER)
        await ensure_assistant_joined(bot, assistant, NS(id=-1001))
        assistant.join_chat.assert_not_awaited()

    async def test_banned_member_is_not_unbanned(self):
        from helpers.catalog import MusicError
        bot, assistant = self.setup_clients(S.BANNED)
        with self.assertRaisesRegex(MusicError, 'banned'):
            await ensure_assistant_joined(bot, assistant, NS(id=-1001))
        bot.create_chat_invite_link.assert_not_awaited()

    async def test_join_request_is_approved(self):
        bot, assistant = self.setup_clients()
        assistant.join_chat.side_effect = errors.InviteRequestSent()
        await ensure_assistant_joined(bot, assistant, NS(id=-1001))
        bot.approve_chat_join_request.assert_awaited_once_with(-1001,42)
