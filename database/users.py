from motor.motor_asyncio import AsyncIOMotorClient
from config import _C

_mc = AsyncIOMotorClient(_C.MONGO_URL)
_db = _mc["AliceMusicBot"]
_udb = _db.users

async def _isu(_uid: int) -> bool:
    _u = await _udb.find_one({"user_id": _uid})
    return bool(_u)

async def _asu(_uid: int):
    if await _isu(_uid):
        return
    return await _udb.insert_one({"user_id": _uid})

async def _gsu() -> list:
    _ul = []
    async for _u in _udb.find({"user_id": {"$gt": 0}}):
        _ul.append(_u)
    return _ul
