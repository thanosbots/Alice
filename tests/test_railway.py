import os
import unittest
from unittest.mock import AsyncMock, patch
from helpers import updater


class ManagedDeploymentTests(unittest.IsolatedAsyncioTestCase):
    async def test_managed_update_cannot_clone_or_install(self):
        for environment in ({'RAILWAY_PROJECT_ID': 'project'}, {'ALICE_MANAGED_DEPLOYMENT': '1'}):
            with self.subTest(environment=environment), patch.dict(os.environ, environment, clear=True), patch.object(updater, 'run', new_callable=AsyncMock) as run:
                with self.assertRaisesRegex(updater.UpdateError, 'redeploy'):
                    await updater.check_update()
                with self.assertRaisesRegex(updater.UpdateError, 'redeploy'):
                    await updater.install_update(None)
                run.assert_not_awaited()

    def test_vps_keeps_existing_updater(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(updater.managed_deployment())
