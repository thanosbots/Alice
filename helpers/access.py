"""Owner screens must never be rendered into a shared group message."""
from pyrogram.enums import ChatType

def private_owner(user, chat, owner_id):
    return bool(user and chat and user.id == owner_id and chat.type == ChatType.PRIVATE and chat.id == owner_id)
