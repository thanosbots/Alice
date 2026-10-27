from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

mongo_client = AsyncIOMotorClient(Config.MONGO_URL)
database = mongo_client["AliceMusicBot"]
chats_collection = database.chats

async def chat_exists(_cid: int) -> bool:
    _c = await chats_collection.find_one({"chat_id": _cid})
    return bool(_c)

async def save_chat(_cid: int):
    if await chat_exists(_cid):
        return
    return await chats_collection.insert_one({"chat_id": _cid})

async def get_chat_ids() -> list:
    """Returns a clean list of Group IDs for broadcasting."""
    _cl = []
    # Using $ne: 0 to catch all valid negative chat IDs
    async for _c in chats_collection.find({"chat_id": {"$ne": 0}}):
        _cl.append(_c["chat_id"])
    return _cl
