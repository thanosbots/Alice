from pyrogram import filters
from core.clients import _b1
from database.chats import _asc


@_b1.on_message(filters.group, group=10)
async def _catch_existing_groups(_c, _m):
    try:
   
        await _asc(_m.chat.id)
    except:
        pass