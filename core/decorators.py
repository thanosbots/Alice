from pytgcalls import filters as fl
from pytgcalls.types import ChatUpdate, StreamEnded
from helpers.queue import queues, mark_inactive, chat_locks, repeat_modes
from helpers.player import advance

async def register_voice_handlers(client):
    @client.vcbot.on_update(fl.chat_update(ChatUpdate.Status.LEFT_CALL))
    async def left(_, update):
        # Do not leave again from a leave notification.
        async with chat_locks[update.chat_id]:
            queues.pop(update.chat_id, None)
            repeat_modes.pop(update.chat_id, None)
            await mark_inactive(update.chat_id)

    @client.vcbot.on_update(fl.stream_end(StreamEnded.Type.AUDIO))
    async def ended(_, update):
        # Capture identity before waiting: queued duplicate events cannot pop twice.
        queue = queues.get(update.chat_id)
        current = queue[0] if queue else None
        async with chat_locks[update.chat_id]:
            queue = queues.get(update.chat_id)
            if current and queue and queue[0] is current:
                await advance(update.chat_id)
