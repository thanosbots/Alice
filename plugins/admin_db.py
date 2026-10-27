from helpers.identity import owner_text
import asyncio
from pyrogram import filters, errors
from pyrogram.enums import ChatMemberStatus
from config import Config
from core.clients import bot
from database.chats import chats_collection, get_chat_ids
from database.users import users_collection, get_user_ids

@bot.on_message(filters.command("dbstats") & filters.user(Config.OWNER_ID) & filters.private)
async def _db_stats_cmd(_c, _m):
    users = await users_collection.count_documents({})
    chats = await chats_collection.count_documents({})

    # Calculate total songs played
    pipeline = [{"$group": {"_id": None, "total": {"$sum": "$played"}}}]
    cursor = users_collection.aggregate(pipeline)
    res = await cursor.to_list(length=1)
    total_played = res[0]["total"] if res else 0

    await owner_reply(_m,
        f"**🗄 Database Stats**\n\n"
        f"👤 **Users:** `{users}`\n"
        f"👥 **Groups:** `{chats}`\n"
        f"🎵 **Total Plays:** `{total_played}`"
    )

@bot.on_message(filters.command("cleanchats") & filters.user(Config.OWNER_ID) & filters.private)
async def _clean_groups_cmd(_c, _m):
    _aux = await owner_reply(_m, "🔎 **Cleaning Group Database...**\n*(Checking Admin status)*")

    all_chats = await get_chat_ids()
    total = len(all_chats)
    deleted = 0
    checked = 0

    for cid in all_chats:
        checked += 1
        try:
            # Check if bot is admin
            member = await _c.get_chat_member(cid, "me")
            if member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
                await chats_collection.delete_one({"chat_id": cid})
                deleted += 1
        except (errors.ChannelPrivate, errors.UserNotParticipant):
            await chats_collection.delete_one({"chat_id": cid})
            deleted += 1
        except errors.FloodWait as exc:
            await asyncio.sleep(exc.value + 1)
        except Exception:
            # Unknown peers and network failures are not evidence of removal.
            pass

        await asyncio.sleep(0.2)

        if checked % 20 == 0:
            await owner_edit(_aux, f"**⏳ Progress:** `{checked}/{total}` groups scanned...")

    await owner_edit(_aux, f"**✅ Group Cleanup Complete!**\n\nRemoved `{deleted}` invalid/non-admin groups.")

@bot.on_message(filters.command("cleanusers") & filters.user(Config.OWNER_ID) & filters.private)
async def _clean_users_cmd(_c, _m):
    _aux = await owner_reply(_m, "🧹 **Cleaning User Database...**")

    all_users = await get_user_ids()
    deleted = 0
    checked = 0

    for uid in all_users:
        checked += 1
        try:
            user = await _c.get_users(uid)
            if user.is_deleted:
                await users_collection.delete_one({"user_id": uid})
                deleted += 1
        except (errors.UserDeactivated, errors.InputUserDeactivated):
            await users_collection.delete_one({"user_id": uid})
            deleted += 1
        except errors.FloodWait as exc:
            await asyncio.sleep(exc.value + 1)
        except Exception:
            pass

        await asyncio.sleep(0.1)
        if checked % 50 == 0:
            await owner_edit(_aux, f"**⏳ Progress:** `{checked}/{len(all_users)}` users scanned...")

    await owner_edit(_aux, f"**✅ User Cleanup Complete!**\n\nRemoved `{deleted}` deleted user records.")

@bot.on_message(filters.command("top") & filters.user(Config.OWNER_ID) & filters.private)
async def _top_players(_c, _m):
    top_players = ""
    async for user in users_collection.find().sort("played", -1).limit(10):
        name = user.get("name", "Unknown")
        played = user.get("played", 0)
        top_players += f"👤 {name}: `{played} songs`\n"

    await owner_reply(_m, f"**🏆 Top 10 Listeners**\n\n{top_players if top_players else 'No data.'}")

async def owner_reply(message, text):
    return await message.reply_text(owner_text(text))

async def owner_edit(message, text):
    return await message.edit(owner_text(text))
