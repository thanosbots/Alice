import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from helpers import notifications as n

class NotificationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.uploader = patch.object(n, 'upload_photo', new_callable=AsyncMock, return_value='telegram-photo-id')
        self.uploader.start()

    async def asyncTearDown(self):
        await n.close_notifications()
        n._photo_ids.clear()
        self.uploader.stop()

    async def test_text_delivered_before_slow_photo(self):
        release = asyncio.Event()
        async def upload(*args, **kwargs):
            await release.wait()
        message = SimpleNamespace(_client=object(), chat=SimpleNamespace(id=-123), id=1, edit_media=AsyncMock(side_effect=upload))
        client = SimpleNamespace(send_message=AsyncMock(return_value=message))
        result = await asyncio.wait_for(n.send_panel(client, -123, 'Ready'), 0.2)
        self.assertIs(result, message)
        client.send_message.assert_awaited_once()
        release.set()

    async def test_timeout_does_not_wait_for_stalled_cancellation_cleanup(self):
        release = asyncio.Event()
        async def stalled():
            try:
                await asyncio.Event().wait()
            finally:
                await release.wait()
        with self.assertRaises(asyncio.TimeoutError):
            await asyncio.wait_for(n.bounded(stalled(), .01), .2)
        release.set()
        await asyncio.sleep(0)

    async def test_failed_image_preserves_text_without_duplicate_send(self):
        message = SimpleNamespace(_client=object(), chat=SimpleNamespace(id=-123), id=1, edit_media=AsyncMock(side_effect=RuntimeError('upload')))
        client = SimpleNamespace(send_message=AsyncMock(return_value=message))
        await n.send_panel(client, -123, 'Ready')
        await asyncio.sleep(.02)
        client.send_message.assert_awaited_once()
        message.edit_media.assert_awaited_once()

    async def test_navigation_cancels_old_artwork(self):
        message = SimpleNamespace(_client=object(), chat=SimpleNamespace(id=-123), id=1, edit_media=AsyncMock())
        started = asyncio.Event()
        async def slow(*args):
            started.set()
            await asyncio.Event().wait()
        with patch.object(n, 'decorate', side_effect=slow):
            first = n.schedule_decoration(message, 'Home', None, 'start.png')
            await started.wait()
            second = n.schedule_decoration(message, 'Help', None, 'help.png')
            await asyncio.sleep(0)
            self.assertTrue(first.cancelled())
            self.assertIs(n._decorations[(-123, 1)], second)
            n.cancel_decoration(message)
            await asyncio.sleep(0)
            self.assertTrue(second.cancelled())
