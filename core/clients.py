from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import Call as GC, GroupCallConfig
from config import _C

class _A1(Client):
    def __init__(self):
        super().__init__(
            "AliceAssistant",
            api_id=_C.API_ID,
            api_hash=_C.API_HASH,
            session_string=_C.STRING_SESSION,
            no_updates=True,
        )
        self.name = None
        self.username = None
        self.mention = None
        self.id = None

    async def start(self):
        await super().start()
        _m = await self.get_me()
        self.name = _m.first_name + " " + (_m.last_name or "")
        self.username = _m.username
        self.mention = _m.mention
        self.id = _m.id

    async def stop(self):
        try:
            await super().stop()
        except:
            pass

class _B1(Client):
    def __init__(self):
        super().__init__(
            "AliceMusicBot",
            api_id=_C.API_ID,
            api_hash=_C.API_HASH,
            bot_token=_C.BOT_TOKEN,
            plugins=dict(root="plugins") # <--- THIS IS THE MAGIC LINE
        )

    async def start(self):
        await super().start()
        _m = await self.get_me()
        self.name = _m.first_name + " " + (_m.last_name or "")
        self.username = _m.username
        self.mention = _m.mention
        self.id = _m.id
        
    async def stop(self):
        try:
            await super().stop()
        except:
            pass

class _C1:
    def __init__(self):
        self.userbot = Client(
            "AliceVoicePlayer",
            api_id=_C.API_ID,
            api_hash=_C.API_HASH,
            session_string=_C.STRING_SESSION,
            no_updates=False,
        )
        self.vcbot = PyTgCalls(self.userbot, cache_duration=100)
        self.call_config = GroupCallConfig(auto_start=False)
        self.is_started = False
        
    async def get_call_status(self, chat_id):
        try:
            _ac = await self.vcbot.calls
            _a = _ac.get(chat_id)
        
            if not _a:
                return "nothing"

            _s = _a.capture

            if _s == GC.Status.PLAYING:
                return "playing"
            elif _s == GC.Status.PAUSED:
                return "paused"
            elif _s == GC.Status.IDLE:
                return "idle"
            else:
                return "unknown"
        except:
            return "nothing"
    
    async def join_vc(self, _cid, _st=None):
        if not _st:
            return await self.vcbot.play(_cid, config=self.call_config)
        return await self.vcbot.play(_cid, _st, config=self.call_config)
        
    async def leave_vc(self, _cid):
        return await self.vcbot.leave_call(_cid)
        
    async def pause_stream(self, _cid):
        try:
            return await self.vcbot.pause(_cid)
        except:
            return

    async def resume_stream(self, _cid):
        try:
            return await self.vcbot.resume(_cid)
        except:
            return

    async def mute_stream(self, _cid):
        try:
            return await self.vcbot.mute(_cid)
        except:
            return

    async def unmute_stream(self, _cid):
        try:
            return await self.vcbot.unmute(_cid)
        except:
            return
        
    async def start(self):
        if _C.STRING_SESSION and not self.is_started:
            await self.vcbot.start()
            self.is_started = True

    async def stop(self):
        try:
            if self.is_started:
                await self.vcbot.stop()
                self.is_started = False
        except:
            pass

_a1 = _A1()
_b1 = _B1()
_c1 = _C1()

_s = filters.user()
if _C.OWNER_ID not in _s:
    _s.add(_C.OWNER_ID)
