from helpers.identity import owner_text
import asyncio
from pyrogram import filters
from pyrogram.errors import FloodWait
from config import Config
from core.clients import bot
from database.users import get_user_ids
from database.chats import get_chat_ids

@bot.on_message(filters.command(["broadcast", "bcast"], ["/", "!"]) & filters.user(Config.OWNER_ID) & filters.private)
async def _bcast_cmd(_c, _m):
    if len(_m.command) < 2:
        return await owner_reply(_m, "**⚠️ Usage:** `/broadcast users` OR `/broadcast groups` (Reply to a message)")

    target = _m.command[1].lower()
    if target not in ["users", "groups"]:
        return await owner_reply(_m, "**⚠️ Target must be 'users' or 'groups'.**")

    msg_to_send = _m.reply_to_message

    # We use copy_message so it supports photos, videos, buttons, and formatting!
    if not msg_to_send:
        return await owner_reply(_m, "**⚠️ Please reply to a message (text, photo, or video) to broadcast it.**")

    _aux = await owner_reply(_m, f"**⏳ Fetching {target} from database...**")

    # Fetch IDs from your database
    if target == "users":
        chats = await get_user_ids()
    else:
        chats = await get_chat_ids()

    total_chats = len(chats)
    if total_chats == 0:
        return await owner_edit(_aux, f"**❌ No {target} found in the database.**")

    await owner_edit(_aux, f"**🔄 Starting broadcast to {total_chats} {target}...**\n\n*(This may take a while. You will get live updates here.)*")

    successful = 0
    failed = 0

    # The broadcast loop
    for i, chat_id in enumerate(chats):
        try:
            # copy_message perfectly mirrors your replied message to the target
            await msg_to_send.copy(chat_id)
            successful += 1

            # 🌟 CRITICAL: 0.1s delay keeps you under Telegram's global broadcast limits
            await asyncio.sleep(0.1)

        except FloodWait as e:
            # 🌟 CRITICAL: If Telegram says "slow down", the bot pauses automatically, then continues!
            await asyncio.sleep(e.value + 1)
            try:
                await msg_to_send.copy(chat_id)
                successful += 1
            except:
                failed += 1
        except Exception:
            # User blocked the bot, group was deleted, etc.
            failed += 1

        # Update the owner every 500 messages so we don't spam edit requests
        if (i + 1) % 500 == 0:
            try:
                await owner_edit(_aux,
                    f"**📣 Broadcast in Progress...**\n\n"
                    f"**🎯 Target:** `{target.title()}`\n"
                    f"**📈 Total:** `{total_chats}`\n"
                    f"**✅ Sent:** `{successful}`\n"
                    f"**❌ Failed:** `{failed}`\n"
                    f"**⏳ Remaining:** `{total_chats - (successful + failed)}`"
                )
            except:
                pass

    # Final Summary
    await owner_edit(_aux,
        f"**✅ Broadcast Completed!**\n\n"
        f"**🎯 Target:** `{target.title()}`\n"
        f"**📈 Total Found:** `{total_chats}`\n"
        f"**✅ Successfully Sent:** `{successful}`\n"
        f"**❌ Failed (Blocked/Left):** `{failed}`"
    )

async def owner_reply(message, text):
    return await message.reply_text(owner_text(text))

async def owner_edit(message, text):
    return await message.edit(owner_text(text))
