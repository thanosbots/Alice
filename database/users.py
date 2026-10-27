from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

mongo_client = AsyncIOMotorClient(Config.MONGO_URL)
database = mongo_client["AliceMusicBot"]
users_collection = database.users

async def user_exists(_uid: int) -> bool:
    _u = await users_collection.find_one({"user_id": _uid})
    return bool(_u)

async def save_user(_uid: int, name: str):
    """Adds a new user or updates the name of an existing one."""
    if await user_exists(_uid):
        return await users_collection.update_one({"user_id": _uid}, {"$set": {"name": name}})
    return await users_collection.insert_one({"user_id": _uid, "name": name, "played": 0})

async def increment_play_count(_uid: int):
    """Increments the play count for a user."""
    return await users_collection.update_one({"user_id": _uid}, {"$inc": {"played": 1}})

async def get_user_ids() -> list:
    """Returns a clean list of user IDs for broadcasting."""
    _ul = []
    async for _u in users_collection.find({"user_id": {"$gt": 0}}):
        _ul.append(_u["user_id"])
    return _ul
