from motor.motor_asyncio import AsyncIOMotorClient
from config import _C

_mc = AsyncIOMotorClient(_C.MONGO_URL)
_db = _mc["AliceMusicBot"]
_cdb = _db.chats

async def _isc(_cid: int) -> bool:
    _c = await _cdb.find_one({"chat_id": _cid})
    return bool(_c)

async def _asc(_cid: int):
    if await _isc(_cid):
        return
    return await _cdb.insert_one({"chat_id": _cid})

async def _gsc() -> list:
    """Returns a clean list of Group IDs for broadcasting."""
    _cl = []
    # Using $ne: 0 to catch all valid negative chat IDs
    async for _c in _cdb.find({"chat_id": {"$ne": 0}}):
        _cl.append(_c["chat_id"])
    return _cl