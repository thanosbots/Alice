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
    _cl = []
    async for _c in _cdb.find({"chat_id": {"$lt": 0}}):
        _cl.append(_c)
    return _cl
