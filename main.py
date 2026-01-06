"""
Alice Music Bot v2.0
Open Source Music Streaming Bot
Credits: Rishabh Anand (@rishabhops)
"""

import asyncio
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pyrogram import idle
from config import _C
from core.clients import _b1, _a1, _c1
from core.decorators import _sh
from helpers.api import _cls
from helpers._0x3c4d import _0x7f3a

if not _0x7f3a._0xcc():
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format=f"[%(asctime)s - %(levelname)s] - {_C._n} - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("alice_logs.txt", maxBytes=5000000, backupCount=10),
        logging.StreamHandler(),
    ],
)

logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("pytgcalls").setLevel(logging.ERROR)

_l = logging.getLogger("Alice")

async def _ast():
    _l.info("╔═══════════════════════════════════════╗")
    _l.info(f"║   {_C._fn} v{_C._v} - Starting...   ║")
    _l.info("╚═══════════════════════════════════════╝")
    
    for _d in ["cache", "downloads", "alice_cache"]:
        if not os.path.exists(_d):
            os.mkdir(_d)
    
    for _f in os.listdir():
        if _f.endswith((".session", ".session-journal")):
            try:
                os.remove(_f)
            except:
                pass
    
    try:
        await _b1.start()
        _l.info(f"✅ {_C._n} Started!")
        try:
            await _b1.send_message(_C.LOG_GROUP_ID, f"**✨ {_C._fn} Started ✨**\n\n**🎵 Ready!**\n\n{_C._f}")
        except:
            pass
    except Exception as _e:
        _l.error(f"❌ {_C._n} Failed: {_e}")
        sys.exit()

    await asyncio.sleep(3)
    
    try:
        await _a1.start()
        _l.info(f"✅ {_C._n} Assistant Started!")
        try:
            await _a1.send_message(_C.LOG_GROUP_ID, f"**✨ {_C._n} Assistant Connected ✨**")
        except:
            pass
    except Exception as _e:
        _l.error(f"❌ {_C._n} Assistant Failed: {_e}")
        sys.exit()
    
    await asyncio.sleep(3)
    
    try:
        await _c1.start()
        _l.info(f"✅ {_C._n} Voice Started!")
    except Exception as _e:
        _l.error(f"❌ {_C._n} Voice Failed: {_e}")
        sys.exit()
    
    await _sh(_c1)
    
    _l.info("╔═══════════════════════════════════════╗")
    _l.info(f"║  🎵 {_C._n} is now live!           ║")
    _l.info("╚═══════════════════════════════════════╝")
    
    await idle()
    
    _l.info(f"{_C._n} shutting down...")
    await _cls()
    await _a1.stop()
    await _c1.stop()
    await _b1.stop()
    _l.info(f"✅ {_C._n} stopped.")

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"  {_C._fn} v{_C._v}")
    print(f"  Credits: {_C._dn} ({_C._du})")
    print(f"{'='*60}\n")
    
    _loop = asyncio.get_event_loop()
    _loop.run_until_complete(_ast())
