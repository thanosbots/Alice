import asyncio
from pyrogram import filters
from pyrogram.errors import FloodWait
from config import _C, HELP_DICT
from core.clients import _b1
from database.users import _gsu
from database.chats import _gsc

# Add it to the Help Menu (Optional: You can remove this if you want it hidden from normal users)
HELP_DICT["📣 Broadcast"] = """**📣 Owner Broadcast Commands**

`/broadcast users` [reply to message] - Send to all private users.
`/broadcast groups` [reply to message] - Send to all groups."""

@_b1.on_message(filters.command(["broadcast", "bcast"], ["/", "!"]) & filters.user(_C.OWNER_ID))
async def _bcast_cmd(_c, _m):
    if len(_m.command) < 2:
        return await _m.reply_text("**⚠️ Usage:** `/broadcast users` OR `/broadcast groups` (Reply to a message)")
    
    target = _m.command[1].lower()
    if target not in ["users", "groups"]:
        return await _m.reply_text("**⚠️ Target must be 'users' or 'groups'.**")

    msg_to_send = _m.reply_to_message
    
    # We use copy_message so it supports photos, videos, buttons, and formatting!
    if not msg_to_send:
        return await _m.reply_text("**⚠️ Please reply to a message (text, photo, or video) to broadcast it.**")

    _aux = await _m.reply_text(f"**⏳ Fetching {target} from database...**")

    # Fetch IDs from your database
    if target == "users":
        chats = await _gsu()
    else:
        chats = await _gsc()
        
    total_chats = len(chats)
    if total_chats == 0:
        return await _aux.edit(f"**❌ No {target} found in the database.**")

    await _aux.edit(f"**🔄 Starting broadcast to {total_chats} {target}...**\n\n*(This may take a while. You will get live updates here.)*")
    
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
                await _aux.edit(
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
    await _aux.edit(
        f"**✅ Broadcast Completed!**\n\n"
        f"**🎯 Target:** `{target.title()}`\n"
        f"**📈 Total Found:** `{total_chats}`\n"
        f"**✅ Successfully Sent:** `{successful}`\n"
        f"**❌ Failed (Blocked/Left):** `{failed}`"
    )