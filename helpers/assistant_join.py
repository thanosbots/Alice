"""Ensure the playback account can access a group before starting audio."""
from pyrogram import errors
from pyrogram.enums import ChatMemberStatus
from helpers.catalog import MusicError


async def ensure_assistant_joined(bot, assistant, chat):
    # The bot already knows this chat. A non-member assistant may not have its
    # access hash and can raise PeerIdInvalid instead of UserNotParticipant.
    try:
        member = await bot.get_chat_member(chat.id, assistant.id)
    except errors.UserNotParticipant:
        member = None
    if member and member.status == ChatMemberStatus.BANNED:
        raise MusicError('The assistant is banned from this group. Unban it, then use /play again.')
    if member and member.status not in (ChatMemberStatus.LEFT, ChatMemberStatus.RESTRICTED):
        return
    if member and member.status == ChatMemberStatus.RESTRICTED and member.is_member:
        return
    try:
        me = await bot.get_chat_member(chat.id, 'me')
        if me.status != ChatMemberStatus.OWNER and (
            me.status != ChatMemberStatus.ADMINISTRATOR
            or not me.privileges or not me.privileges.can_invite_users
        ):
            raise MusicError('Make the bot an admin with Invite Users permission so it can automatically join the assistant.')
        # A separate link avoids rotating the group's existing primary link.
        invite = await bot.create_chat_invite_link(chat.id, name='Alice assistant', creates_join_request=False)
        try:
            try:
                await assistant.join_chat(invite.invite_link)
            except errors.UserAlreadyParticipant:
                pass
            except errors.InviteRequestSent:
                await bot.approve_chat_join_request(chat.id, assistant.id)
        finally:
            try:
                await bot.revoke_chat_invite_link(chat.id, invite.invite_link)
            except errors.RPCError:
                pass
    except errors.ChatAdminRequired as exc:
        raise MusicError('Give the bot Invite Users permission, then use /play again.') from exc
    except errors.UserBannedInChannel as exc:
        raise MusicError('The assistant is banned from this group. Unban it, then use /play again.') from exc
    except errors.FloodWait as exc:
        raise MusicError(f'Telegram asks the assistant to wait {exc.value} seconds before joining. Try again after that.') from exc
