import asyncio
from pyrogram import filters, errors
from config import _C, HELP_DICT
from core.clients import _b1
from database.chats import _cdb, _gsc
from database.users import _udb, _gsu

HELP_DICT["🗄 DB Admin"] = """**🗄 Database Management**

`/dbstats` - Check total users and groups
`/cleanusers` - Remove users who blocked the bot
`/cleanchats` - Remove groups where bot is kicked or not admin
`/top` - View top music listeners"""

@_b1.on_message(filters.command("dbstats") & filters.user(_C.OWNER_ID))
async def _db_stats_cmd(_c, _m):
    users = await _udb.count_documents({})
    chats = await _cdb.count_documents({})
    
    # Calculate total songs played
    pipeline = [{"$group": {"_id": None, "total": {"$sum": "$played"}}}]
    cursor = _udb.aggregate(pipeline)
    res = await cursor.to_list(length=1)
    total_played = res[0]["total"] if res else 0

    await _m.reply_text(
        f"**🗄 Database Stats**\n\n"
        f"👤 **Users:** `{users}`\n"
        f"👥 **Groups:** `{chats}`\n"
        f"🎵 **Total Plays:** `{total_played}`"
    )

@_b1.on_message(filters.command("cleanchats") & filters.user(_C.OWNER_ID))
async def _clean_groups_cmd(_c, _m):
    _aux = await _m.reply_text("🔎 **Cleaning Group Database...**\n*(Checking Admin status)*")
    
    all_chats = await _gsc()
    total = len(all_chats)
    deleted = 0
    checked = 0
    
    for cid in all_chats:
        checked += 1
        try:
            # Check if bot is admin
            member = await _c.get_chat_member(cid, "me")
            if member.status not in ["administrator", "creator"]:
                await _cdb.delete_one({"chat_id": cid})
                deleted += 1
        except Exception:
            # Bot was kicked, group is dead, or no access
            await _cdb.delete_one({"chat_id": cid})
            deleted += 1
            
        await asyncio.sleep(0.2)
        
        if checked % 20 == 0:
            await _aux.edit(f"**⏳ Progress:** `{checked}/{total}` groups scanned...")

    await _aux.edit(f"**✅ Group Cleanup Complete!**\n\nRemoved `{deleted}` invalid/non-admin groups.")

@_b1.on_message(filters.command("cleanusers") & filters.user(_C.OWNER_ID))
async def _clean_users_cmd(_c, _m):
    _aux = await _m.reply_text("🧹 **Cleaning User Database...**")
    
    all_users = await _gsu()
    deleted = 0
    checked = 0
    
    for uid in all_users:
        checked += 1
        try:
            await _c.get_chat(uid)
        except:
            await _udb.delete_one({"user_id": uid})
            deleted += 1
            
        await asyncio.sleep(0.1)
        if checked % 50 == 0:
            await _aux.edit(f"**⏳ Progress:** `{checked}/{len(all_users)}` users scanned...")

    await _aux.edit(f"**✅ User Cleanup Complete!**\n\nRemoved `{deleted}` blocked users.")

@_b1.on_message(filters.command("top") & filters.user(_C.OWNER_ID))
async def _top_players(_c, _m):
    top_players = ""
    async for user in _udb.find().sort("played", -1).limit(10):
        name = user.get("name", "Unknown")
        played = user.get("played", 0)
        top_players += f"👤 {name}: `{played} songs`\n"
    
    await _m.reply_text(f"**🏆 Top 10 Listeners**\n\n{top_players if top_players else 'No data.'}")