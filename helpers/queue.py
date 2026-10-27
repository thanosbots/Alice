import asyncio
from collections import defaultdict
from core.clients import voice

queues = {}
active_audio_chats = set()
active_video_chats = set()

async def enqueue(_cid: int, _ms, _t, _d, _l, _th, _st, _cn, _cl, _rb):
    if _cid not in queues:
        queues[_cid] = []

    _i = {
        "media_stream": _ms,
        "title": _t,
        "duration": _d,
        "link": _l,
        "thumbnail": _th,
        "stream_type": _st,
        "chat_name": _cn,
        "chat_link": _cl,
        "requested_by": _rb
    }

    queues[_cid].append(_i)
    return len(queues[_cid]) - 1

async def stop_playback(_cid: int):
    request_versions[_cid] += 1
    queues.pop(_cid, None)
    repeat_modes.pop(_cid, None)
    try:
        await voice.leave_vc(_cid)
    except:
        pass
    try:
        await mark_inactive(_cid)
    except:
        pass

async def mark_active(_cid: int, _st: str):
    _sx = _st.lower()
    if _sx == "audio":
        active_audio_chats.add(_cid)
        active_video_chats.discard(_cid)
    elif _sx == "video":
        active_video_chats.add(_cid)
        active_audio_chats.discard(_cid)

async def mark_inactive(_cid: int):
    active_audio_chats.discard(_cid)
    active_video_chats.discard(_cid)

# One lock per chat serializes play, skip, stop and automatic transitions.
chat_locks = defaultdict(asyncio.Lock)
repeat_modes = {}


def advance_queue(chat_id, manual=False):
    queue = queues.get(chat_id, [])
    if not queue:
        return None
    mode = repeat_modes.get(chat_id, "off")
    if manual or mode != "one":
        current = queue.pop(0)
        if mode == "all":
            queue.append(current)
    if queue:
        queue[0] = dict(queue[0])  # New playback identity, including repeat-one.
        return queue[0]
    return None

# Preparation never holds the playback lock. Stop invalidates pending requests.
request_locks = defaultdict(asyncio.Lock)
request_versions = defaultdict(int)
