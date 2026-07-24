import inspect
import logging

from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import Call as GC, GroupCallConfig

from config import _C

_l = logging.getLogger("Alice.Clients")


class _A1:
    """
    User session (assistant account) ka wrapper.

    IMPORTANT: ye Client ko SUBCLASS nahi karta — composition use karta hai.
    Wajah: pytgcalls ka MtProtoClient library detect karta hai
    `client.__class__.__module__.split('.')[0]` se. Subclass ka module
    'core.clients' hota hai, 'pyrogram' nahi -> InvalidMTProtoClient.

    Andar wala plain `self.client` hi PyTgCalls ko diya jaata hai.
    Bahar se `_a1.join_chat(...)`, `_a1.invoke(...)` waise hi kaam karega
    __getattr__ delegation ki wajah se.
    """

    def __init__(self):
        self.client = Client(
            "AliceAssistant",
            api_id=_C.API_ID,
            api_hash=_C.API_HASH,
            session_string=_C.STRING_SESSION,
            no_updates=False,          # PyTgCalls ko raw updates chahiye
        )
        self.name = None
        self.username = None
        self.mention = None
        self.id = None

    def __getattr__(self, _item):
        # Sirf tab chalega jab attribute wrapper par na mile.
        # object.__getattribute__ use kar rahe hain warna __init__ ke dauraan
        # (jab self.client abhi set nahi hua) infinite recursion ho jayegi.
        try:
            _cl = object.__getattribute__(self, "client")
        except AttributeError:
            raise AttributeError(_item)
        return getattr(_cl, _item)

    async def load_me(self):
        """Idempotent — kitni bhi baar call kar sakte ho."""
        if self.id is not None:
            return
        _m = await self.client.get_me()
        self.name = ((_m.first_name or "") + " " + (_m.last_name or "")).strip()
        self.username = _m.username
        self.mention = _m.mention
        self.id = _m.id

    async def start(self):
        if not self.client.is_connected:
            await self.client.start()
        await self.load_me()

    async def stop(self):
        try:
            if self.client.is_connected:
                await self.client.stop()
        except Exception:
            pass


class _B1(Client):
    """
    Bot token client. Ye subclass rehne mein koi problem nahi —
    isko kabhi PyTgCalls ko pass nahi kiya jaata.
    """

    def __init__(self):
        super().__init__(
            "AliceMusicBot",
            api_id=_C.API_ID,
            api_hash=_C.API_HASH,
            bot_token=_C.BOT_TOKEN,
            plugins=dict(root="plugins"),
        )
        self.username = None
        self.mention = None
        self.id = None

    async def start(self):
        if not self.is_connected:
            await super().start()
        _m = await self.get_me()
        self.name = ((_m.first_name or "") + " " + (_m.last_name or "")).strip()
        self.username = _m.username
        self.mention = _m.mention
        self.id = _m.id

    async def stop(self):
        try:
            if self.is_connected:
                await super().stop()
        except Exception:
            pass


class _C1:
    """
    Voice-chat wrapper.

    CHANGE: pehle yahan ek naya Client("AliceVoicePlayer") banta tha usi
    STRING_SESSION se — matlab ek hi account ki do simultaneous MTProto
    sessions ek hi process mein. Ab _a1 ka andar wala client reuse hota hai.
    """

    def __init__(self, assistant: _A1):
        self.assistant = assistant
        self.userbot = assistant.client                 # plain pyrogram Client
        self.vcbot = PyTgCalls(self.userbot, cache_duration=100)
        self.call_config = GroupCallConfig(auto_start=False)
        self.is_started = False

    async def _get_calls(self):
        # py-tgcalls ke versions mein `calls` kabhi property hai kabhi awaitable
        _c = self.vcbot.calls
        if inspect.isawaitable(_c):
            _c = await _c
        return _c or {}

    async def get_call_status(self, chat_id):
        try:
            _ac = await self._get_calls()
            _a = _ac.get(chat_id)
            if not _a:
                return "nothing"

            _s = getattr(_a, "capture", None)
            if _s is None:
                _s = getattr(_a, "status", None)

            if _s == GC.Status.PLAYING:
                return "playing"
            if _s == GC.Status.PAUSED:
                return "paused"
            if _s == GC.Status.IDLE:
                return "idle"
            return "unknown"
        except Exception:
            return "nothing"

    async def join_vc(self, _cid, _st=None):
        if not _st:
            return await self.vcbot.play(_cid, config=self.call_config)
        return await self.vcbot.play(_cid, _st, config=self.call_config)

    async def leave_vc(self, _cid):
        """
        Method ka naam py-tgcalls versions ke beech badla hai:
        2.x mein `leave_call`, purani builds mein `leave_group_call`.

        PEHLE yahan seedha `self.vcbot.leave_call(_cid)` tha. Agar is build
        par wo naam na hota to AttributeError uthta — aur _cs() ka
        `except Exception: pass` usse chupchaap nigal jaata. Natija: bot VC
        mein baitha rehta, console bilkul khaali. Ab jo naam maujood hai wahi
        chalta hai, aur ek bhi na mile to saaf error uthta hai.
        """
        _names = ("leave_call", "leave_group_call")
        _found = [_n for _n in _names if callable(getattr(self.vcbot, _n, None))]

        if not _found:
            raise AttributeError(
                f"PyTgCalls par in mein se koi method nahi mila: {_names}"
            )

        _last = None
        for _n in _found:
            try:
                return await getattr(self.vcbot, _n)(_cid)
            except Exception as _e:
                _last = _e
                _l.warning(f"{_n}({_cid}) failed: {type(_e).__name__}: {_e}")
        raise _last

    async def pause_stream(self, _cid):
        try:
            return await self.vcbot.pause(_cid)
        except Exception:
            return

    async def resume_stream(self, _cid):
        try:
            return await self.vcbot.resume(_cid)
        except Exception:
            return

    async def mute_stream(self, _cid):
        try:
            return await self.vcbot.mute(_cid)
        except Exception:
            return

    async def unmute_stream(self, _cid):
        try:
            return await self.vcbot.unmute(_cid)
        except Exception:
            return

    async def start(self):
        if self.is_started or not _C.STRING_SESSION:
            return
        await self.vcbot.start()        # ye underlying client bhi start kar dega
        self.is_started = True
        await self.assistant.load_me()

    async def stop(self):
        try:
            if self.is_started:
                await self.vcbot.stop()
                self.is_started = False
        except Exception:
            pass


_a1 = _A1()
_b1 = _B1()
_c1 = _C1(_a1)          # _a1 ka andar wala client reuse hota hai

_s = filters.user()
if _C.OWNER_ID not in _s:
    _s.add(_C.OWNER_ID)