"""
core/decorators.py — voice-chat handler REGISTRATION.

Asli logic events.py mein rehti hai; yahan sirf wiring hai.

Registration ek hi jagah honi chahiye. Pehle events.py bhi khud
`@_c1.vcbot.on_update()` se register karti thi aur yahan bhi `fl.stream_end`
tha — dono ek hi PyTgCalls instance par. Natija: har stream end par queue do
baar pop hoti thi (gaane skip) aur join_vc() do baar chalta tha (stutter).

Registration yahan rakha hai, events.py mein nahi, kyunki _sh() ko main.py
seedha call karta hai — Pyrogram ke plugin loader par depend nahi karta.
"""

import logging

from pytgcalls import filters as fl
from pytgcalls.types import ChatUpdate, Update

# ⚠️  Ye path tumhari events.py ki jagah ke hisaab se badalna pad sakta hai.
#     plugins/events.py  -> from plugins.events import advance, cleanup
#     core/events.py     -> from core.events import advance, cleanup
from plugins.events import advance, cleanup

_l = logging.getLogger("Alice.Events")


async def _sh(_cl):
    @_cl.vcbot.on_update(
        fl.chat_update(
            ChatUpdate.Status.LEFT_CALL
            | ChatUpdate.Status.KICKED
            | ChatUpdate.Status.CLOSED_VOICE_CHAT
        )
    )
    async def _lh(_, _u: Update):
        await cleanup(_u.chat_id)

    # ⚠️  BRACKET ZAROORI HAI: fl.stream_end ek CLASS hai, filter object nahi.
    #     Bina () ke class khud pass hoti hai; dispatcher use filter(client,
    #     update) karke bulaata hai, jo __call__ nahi balki __init__ chala kar
    #     naya object bana deta hai — isinstance(update, StreamEnded) check
    #     kabhi hota hi nahi. Handler chalta hi nahi tha.
    @_cl.vcbot.on_update(fl.stream_end())
    async def _seh(_, _u: Update):
        await advance(_u.chat_id, _cl.join_vc)

    _l.info("vc handlers registered (stream_end + call_dead)")