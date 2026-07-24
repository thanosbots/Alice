"""
Alice Music Bot v2.0
Open Source Music Streaming Bot
Credits: Rishabh Anand (@rishabhops)

⚠️  TEMP DIAGNOSTIC blocks abhi maujood hain — bug confirm hone ke baad hata dena.
"""

import asyncio
import logging
import os
import pathlib
import platform
import sys
import time
from logging.handlers import RotatingFileHandler

from pyrogram import filters as _flt
from pyrogram import idle

from config import _C
from core import console as _cn
from core.clients import _b1, _a1, _c1
from core.decorators import _sh
from helpers._0x3c4d import _0x7f3a
from helpers.api import _cls

if not _0x7f3a._0xcc():
    sys.exit(1)


# ── logging ───────────────────────────────────────────────────────────
# File handler plain text likhta hai (grep karne layak), console rangeen.

_fileh = RotatingFileHandler("alice_logs.txt", maxBytes=5_000_000, backupCount=10)
_fileh.setFormatter(
    logging.Formatter(
        f"[%(asctime)s - %(levelname)s] - {_C._n} - %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
    )
)

_conh = logging.StreamHandler(sys.stdout)
_conh.setFormatter(_cn.ColourFormatter(_C._n)())

logging.basicConfig(level=logging.INFO, handlers=[_fileh, _conh])

for _noisy in ("asyncio", "httpx", "ntgcalls", "pyrogram.session", "pyrogram.connection"):
    logging.getLogger(_noisy).setLevel(logging.ERROR)

# ─── TEMP DIAGNOSTIC 1 ─────────────────────────────────────────────────
# Plugin loading ki lines dekhne ke liye. Bug fix hone par ise
# logging.ERROR kar dena.
logging.getLogger("pyrogram").setLevel(logging.INFO)
logging.getLogger("pytgcalls").setLevel(logging.WARNING)
# ───────────────────────────────────────────────────────────────────────

_l = logging.getLogger("Alice")

_T0 = time.monotonic()


# ─── TEMP DIAGNOSTIC 2 ─────────────────────────────────────────────────
async def _diagnose():
    """
    NOTE: ye async hai aur pehle sleep karta hai — jaan-bujh ke.

    Pyrogram ka Dispatcher.add_handler() andar se
    `self.loop.create_task(fn())` karta hai, yaani registration event loop
    par DEFER hoti hai. start() ke turant baad ginne se hamesha 0-1 milega,
    chahe sab theek ho. Loop ko ek baar ghoom lene do, phir gino.
    """
    await asyncio.sleep(1)

    _g = getattr(getattr(_b1, "dispatcher", None), "groups", {}) or {}
    _total = sum(len(_v) for _v in _g.values())

    _pd = pathlib.Path("plugins")
    _files = (
        sorted(str(_p.relative_to(_pd)) for _p in _pd.rglob("*.py"))
        if _pd.is_dir()
        else []
    )

    _cn.rule("diagnostics")
    _cn.info(f"cwd             {os.getcwd()}")
    _cn.info(f"plugin files    {len(_files)}  {', '.join(_files) or '—'}")

    # Modules sys.modules mein aaye ya nahi -> import hua ya nahi
    _missing = [
        _f for _f in _files
        if f"plugins.{_f[:-3].replace('/', '.')}" not in sys.modules
    ]
    if _missing:
        _cn.fail(f"import NAHI hue    {', '.join(_missing)}")
    else:
        _cn.ok(f"sab {len(_files)} plugin module import ho gaye")

    if _total:
        _cn.ok(f"handlers registered  {_total}  across {len(_g)} group(s)")
        for _grp, _hs in sorted(_g.items()):
            _cn.info(f"   group {_grp:>4}   {len(_hs)} handler(s)")
    else:
        _cn.fail("handlers registered  0  ← dispatcher par kuch nahi lagaa")

    # Loop identity check — asli shak yahi tha
    _dl = getattr(getattr(_b1, "dispatcher", None), "loop", None)
    _rl = asyncio.get_running_loop()
    if _dl is None:
        _cn.warn("dispatcher.loop mila hi nahi")
    elif _dl is _rl:
        _cn.ok("dispatcher loop == running loop")
    else:
        _cn.fail("dispatcher loop != running loop  ← handlers kabhi register nahi honge")

    @_b1.on_message(_flt.all, group=-99)
    async def _canary(_, _m):
        _cn.info(
            f"UPDATE  chat={_m.chat.id}  type={_m.chat.type}  "
            f"text={(_m.text or _m.caption or '')[:40]!r}"
        )

    _cn.info("canary lagaya — ab bot ko message bhejo")
    _cn.rule()
    print()
# ───────────────────────────────────────────────────────────────────────


async def _ast():
    _cn.banner(_C._fn, _C._v, _C._dn, _C._du)

    _cn.box(
        "environment",
        [
            ("python", platform.python_version()),
            ("platform", f"{platform.system()} {platform.machine()}"),
            ("pid", os.getpid()),
            ("workdir", os.getcwd()),
        ],
    )
    print()

    _cn.rule("boot")

    for _d in ("cache", "downloads", "alice_cache"):
        os.makedirs(_d, exist_ok=True)

    _stale = 0
    for _f in os.listdir():
        if _f.endswith((".session", ".session-journal")):
            try:
                os.remove(_f)
                _stale += 1
            except OSError:
                pass
    if _stale:
        _cn.info(f"cleared {_stale} stale session file(s)")

    # ---- bot client ----
    _cn.step("bot", "connecting bot client")
    try:
        await _b1.start()
        _cn.ok(f"bot online  {_cn.DIM}@{_b1.username}{_cn.RESET}", "bot")
    except Exception as _e:
        _cn.fail(f"bot failed — {_e}", "bot")
        sys.exit(1)

    await _diagnose()                              # TEMP DIAGNOSTIC 3

    try:
        await _b1.send_message(
            _C.LOG_GROUP_ID, f"**✨ {_C._fn} Started ✨**\n\n**🎵 Ready!**"
        )
    except Exception as _e:
        _cn.warn(f"log group post failed — {_e}")

    await asyncio.sleep(3)

    # ---- assistant ----
    _cn.step("asst", "connecting assistant")
    try:
        await _a1.start()
        _cn.ok(f"assistant online  {_cn.DIM}id {_a1.id}{_cn.RESET}", "asst")
    except Exception as _e:
        _cn.fail(f"assistant failed — {_e}", "asst")
        sys.exit(1)

    try:
        await _a1.send_message(_C.LOG_GROUP_ID, f"**✨ {_C._n} Assistant Connected ✨**")
    except Exception:
        pass

    await asyncio.sleep(3)

    # ---- voice ----
    _cn.step("vc", "starting voice engine")
    try:
        await _c1.start()
        _cn.ok("voice engine ready", "vc")
    except Exception as _e:
        _cn.fail(f"voice engine failed — {_e}", "vc")
        sys.exit(1)

    await _sh(_c1)

    print()
    _cn.box(
        f"{_C._fn} is live",
        [
            ("bot", f"@{_b1.username}"),
            ("assistant", str(_a1.id)),
            ("version", _C._v),
            ("boot time", f"{time.monotonic() - _T0:.2f}s"),
        ],
        _cn.GREEN,
    )
    print(f"  {_cn.DIM}ctrl-c to stop{_cn.RESET}\n")

    await idle()

    # ---- shutdown ----
    print()
    _cn.rule("shutdown")
    for _label, _coro in (
        ("http sessions", _cls()),
        ("assistant", _a1.stop()),
        ("voice engine", _c1.stop()),
        ("bot client", _b1.stop()),
    ):
        try:
            await _coro
            _cn.ok(f"{_label} closed")
        except Exception as _e:
            _cn.fail(f"{_label} — {_e}")

    print(f"\n  {_cn.GREY}{_C._fn} stopped.{_cn.RESET}\n")


if __name__ == "__main__":
    # ⚠️  asyncio.run() YAHAN MAT LAGANA.
    #
    # _b1 / _a1 / _c1 module import ke waqt bante hain, yaani loop banne se
    # PEHLE. Pyrogram ka Dispatcher apne __init__ mein
    # `self.loop = asyncio.get_event_loop()` karke usi waqt ka loop pakad
    # leta hai. asyncio.run() ek NAYA loop banata hai, to dispatcher purane
    # loop par create_task() karta rehta hai — jo kabhi chalta nahi.
    # Natija: handlers register hote hi nahi, bot online dikhta hai,
    # aur ek bhi command kaam nahi karti. Bina kisi error ke.
    _loop = asyncio.get_event_loop()
    try:
        _loop.run_until_complete(_ast())
    except KeyboardInterrupt:
        print(f"\n  {_cn.GREY}interrupted.{_cn.RESET}\n")