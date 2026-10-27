import atexit
from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types import Call as GC, GroupCallConfig
from config import Config

class AssistantClient(Client):
    def __init__(self):
        super().__init__(
            "AliceAssistant",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            session_string=Config.STRING_SESSION,
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

class BotClient(Client):
    def __init__(self):
        super().__init__(
            "AliceMusicBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="plugins")
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

class VoiceClient:
    def __init__(self):
        self.userbot = Client(
            "AliceVoicePlayer",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            session_string=Config.STRING_SESSION,
            no_updates=False,
        )
        self.vcbot = PyTgCalls(self.userbot, cache_duration=100)
        self.call_config = GroupCallConfig(auto_start=False)
        self.is_started = False
        atexit.register(self.release_native)

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
        return await self.vcbot.pause(_cid)

    async def resume_stream(self, _cid):
        return await self.vcbot.resume(_cid)

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
        if Config.STRING_SESSION and not self.is_started:
            await self.vcbot.start()
            self.is_started = True

    def release_native(self):
        # Release native worker threads before Python tears down its runtime.
        self.vcbot.executor.shutdown(wait=False)
        self.vcbot._binding = None

    async def stop(self):
        if self.is_started:
            try:
                for chat_id in list(await self.vcbot.calls):
                    try:
                        await self.leave_vc(chat_id)
                    except Exception:
                        pass
            finally:
                if self.userbot.is_connected:
                    await self.userbot.stop()
                self.is_started = False
        self.release_native()


assistant = AssistantClient()
bot = BotClient()
voice = VoiceClient()
