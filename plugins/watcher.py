from pyrogram import filters
from core.clients import bot
from database.chats import save_chat


@bot.on_message(filters.group, group=10)
async def _catch_existing_groups(_c, _m):
    try:

        await save_chat(_m.chat.id)
    except:
        pass
