from motor.motor_asyncio import AsyncIOMotorClient
from config import _C

_mc = AsyncIOMotorClient(_C.MONGO_URL)
_db = _mc["AliceMusicBot"]
_udb = _db.users

async def _isu(_uid: int) -> bool:
    _u = await _udb.find_one({"user_id": _uid})
    return bool(_u)

async def _asu(_uid: int, name: str):
    """Adds a new user or updates the name of an existing one."""
    if await _isu(_uid):
        return await _udb.update_one({"user_id": _uid}, {"$set": {"name": name}})
    return await _udb.insert_one({"user_id": _uid, "name": name, "played": 0})

async def _inc_played(_uid: int):
    """Increments the play count for a user."""
    return await _udb.update_one({"user_id": _uid}, {"$inc": {"played": 1}})

async def _gsu() -> list:
    """Returns a clean list of user IDs for broadcasting."""
    _ul = []
    async for _u in _udb.find({"user_id": {"$gt": 0}}):
        _ul.append(_u["user_id"])
    return _ul

async def _get_user_stats(_uid: int):
    """Returns the full document for a specific user."""
    return await _udb.find_one({"user_id": _uid})