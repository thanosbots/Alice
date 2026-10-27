import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from pyrogram.enums import ChatType
from helpers import updater as u


class UpdateFilesTests(unittest.TestCase):
    def test_runtime_paths_and_traversal_are_rejected(self):
        for name in ('Config.env', '.env', '.git/config', '.updates/python',
                     '.venv/bin/python', 'downloads/song.mp3', '../outside', '/tmp/code',
                     'Alice.session', 'Alice.session-journal', 'alice_logs.txt.1'):
            self.assertFalse(u.safe_path(name), name)
        for name in ('main.py', 'Config.env.example', 'assets/image.png'):
            self.assertTrue(u.safe_path(name), name)

    def test_apply_preserves_runtime_backs_up_code_removes_previous_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'bot'; root.mkdir()
            source = Path(folder) / 'source'; source.mkdir()
            backup = Path(folder) / 'backup'
            (root / 'main.py').write_text('old')
            (root / 'obsolete.py').write_text('old')
            (root / 'Config.env').write_text('secret')
            (root / 'local-notes.txt').write_text('notes')
            (source / 'main.py').write_text('new')
            u.apply_files(root, source, ['main.py'], ['main.py', 'obsolete.py'], backup)
            self.assertEqual((root / 'main.py').read_text(), 'new')
            self.assertEqual((backup / 'main.py').read_text(), 'old')
            self.assertFalse((root / 'obsolete.py').exists())
            self.assertEqual((root / 'Config.env').read_text(), 'secret')
            self.assertTrue((root / 'local-notes.txt').exists())

    def test_copy_failure_rolls_back_files_already_replaced(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'bot'; root.mkdir()
            source = Path(folder) / 'source'; source.mkdir()
            for name in ('a.py', 'b.py'):
                (root / name).write_text('old')
                (source / name).write_text('new')
            replace = u.os.replace
            def fail_second(src, dst):
                if Path(dst).name == 'b.py':
                    raise OSError('disk failure')
                return replace(src, dst)
            with patch.object(u.os, 'replace', side_effect=fail_second):
                with self.assertRaises(OSError):
                    u.apply_files(root, source, ['a.py', 'b.py'], [], Path(folder) / 'backup')
            self.assertEqual((root / 'a.py').read_text(), 'old')
            self.assertEqual((root / 'b.py').read_text(), 'old')

    def test_symlink_cannot_write_outside_installation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'bot'; root.mkdir()
            source = Path(folder) / 'source'; source.mkdir()
            (source / 'main.py').write_text('new')
            outside = Path(folder) / 'outside'; outside.write_text('keep')
            (root / 'main.py').symlink_to(outside)
            with self.assertRaises(u.UpdateError):
                u.apply_files(root, source, ['main.py'], [], Path(folder) / 'backup')
            self.assertEqual(outside.read_text(), 'keep')


class UpdateCommandTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        spec = importlib.util.spec_from_file_location('update_test', 'plugins/update.py')
        self.module = importlib.util.module_from_spec(spec)
        bot = SimpleNamespace(on_message=lambda *a: lambda fn: fn, on_callback_query=lambda *a: lambda fn: fn)
        with patch.dict(sys.modules, {'core.clients': SimpleNamespace(bot=bot),
                         'config': SimpleNamespace(Config=SimpleNamespace(OWNER_ID=42))}):
            spec.loader.exec_module(self.module)
        u.restart_requested.clear()
        self.status = SimpleNamespace(id=10, chat=SimpleNamespace(id=42, type=ChatType.PRIVATE), edit_text=AsyncMock())
        self.release = SimpleNamespace(version='2.2.0', revision='abc123def456')

    def message(self, owner=42, kind=ChatType.PRIVATE):
        return SimpleNamespace(from_user=SimpleNamespace(id=owner),
            chat=SimpleNamespace(id=owner, type=kind), reply_text=AsyncMock(return_value=self.status))

    async def offer(self):
        with patch.object(u, 'check_update', return_value=u.UpdateCheck('2.2.0', self.release)), \
                patch.object(u, 'install_update', new_callable=AsyncMock) as install:
            await self.module.update_command(None, self.message())
        install.assert_not_awaited()
        return next(iter(self.module._pending))

    def query(self, token, action='confirm', owner=42):
        return SimpleNamespace(from_user=SimpleNamespace(id=owner), message=self.status,
            data=f'alice_update:{action}:{token}', answer=AsyncMock())

    async def test_non_owner_and_group_cannot_update(self):
        with patch.object(u, 'check_update', new_callable=AsyncMock) as check:
            await self.module.update_command(None, self.message(owner=7))
            await self.module.update_command(None, self.message(kind=ChatType.SUPERGROUP))
        check.assert_not_awaited()

    async def test_check_only_shows_versions_and_confirmation(self):
        await self.offer()
        call = self.status.edit_text.call_args
        self.assertIn('New version available', call.args[0])
        self.assertIn('2.2.0', call.args[0])
        self.assertIn(u.VERSION, call.args[0])
        self.assertEqual(len(call.kwargs['reply_markup'].inline_keyboard[0]), 2)

    async def test_confirm_installs_exact_offer_once_and_restarts(self):
        token = await self.offer()
        with patch.object(u, 'install_update', return_value=('2.2.0', '/new/python', '/backup')) as install, \
                patch.object(u, 'request_restart') as restart:
            await self.module.update_confirmation(None, self.query(token))
            await self.module.update_confirmation(None, self.query(token))
        install.assert_awaited_once_with(self.release)
        restart.assert_called_once_with('/new/python')

    async def test_cancel_never_installs(self):
        token = await self.offer()
        with patch.object(u, 'install_update', new_callable=AsyncMock) as install, \
                patch.object(u, 'discard_release') as discard:
            await self.module.update_confirmation(None, self.query(token, 'cancel'))
        install.assert_not_awaited()
        discard.assert_called_once_with(self.release)

    async def test_forged_and_expired_confirmation_never_installs(self):
        token = await self.offer()
        with patch.object(u, 'install_update', new_callable=AsyncMock) as install, patch.object(u, 'discard_release'):
            await self.module.update_confirmation(None, self.query(token, owner=7))
            await self.module.update_confirmation(None, self.query('f' * 16))
            self.module._pending[token]['expires'] = 0
            await self.module.update_confirmation(None, self.query(token))
        install.assert_not_awaited()

    async def test_failure_does_not_restart(self):
        token = await self.offer()
        with patch.object(u, 'install_update', side_effect=u.UpdateError('Dependency failed')), \
                patch.object(u, 'request_restart') as restart:
            await self.module.update_confirmation(None, self.query(token))
        restart.assert_not_called()

    async def test_existing_update_is_not_started_twice(self):
        async with u.lock:
            with patch.object(u, 'check_update', new_callable=AsyncMock) as check:
                await self.module.update_command(None, self.message())
        check.assert_not_awaited()

    async def test_no_new_version_has_no_install_button(self):
        with patch.object(u, 'check_update', return_value=u.UpdateCheck(u.VERSION)):
            await self.module.update_command(None, self.message())
        self.assertFalse(self.module._pending)
        self.assertNotIn('reply_markup', self.status.edit_text.call_args.kwargs)


class UpdateStagingTests(unittest.IsolatedAsyncioTestCase):
    async def staged_check(self, root, version='2.2.0'):
        self.commands = []
        async def fake_run(*args, **kwargs):
            self.commands.append(args)
            if args[:2] == ('git', 'clone'):
                source = Path(args[-1]); source.mkdir()
                for name, content in {'main.py': 'restart_requested = True',
                      'requirements.txt': '', 'helpers/updater.py': '', 'VERSION': version,
                      'plugins/update.py': '', 'start.sh': ''}.items():
                    path = source / name; path.parent.mkdir(exist_ok=True)
                    path.write_text(content)
            elif args[:2] == ('git', 'rev-parse'):
                return 'abc123'
            elif args[:2] == ('git', 'ls-files'):
                return 'main.py\0requirements.txt\0helpers/updater.py\0plugins/update.py\0start.sh\0VERSION\0'
            return ''
        with patch.object(u, 'run', side_effect=fake_run), patch.object(u.shutil, 'which', return_value='/git'):
            return await u.check_update(root, repo='https://example.com/alice.git')

    async def test_check_does_not_change_code_or_prepare_dependencies(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'main.py').write_text('old code')
            checked = await self.staged_check(root)
            self.assertEqual(checked.latest_version, '2.2.0')
            self.assertEqual((root / 'main.py').read_text(), 'old code')
            self.assertTrue(all(cmd[0] == 'git' for cmd in self.commands))
            self.assertFalse((root / '.updates/python').exists())

    async def test_older_or_equal_releases_are_not_offered(self):
        for version in ('1.9.9', u.VERSION):
            with tempfile.TemporaryDirectory() as folder:
                checked = await self.staged_check(Path(folder), version)
                self.assertIsNone(checked.release)
                self.assertEqual(list((Path(folder) / '.updates').iterdir()), [])

    async def test_dependency_failure_leaves_live_code_untouched(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'main.py').write_text('old code')
            candidate = (await self.staged_check(root)).release
            async def fake_install(*args, **kwargs):
                if args[:2] == ('git', 'rev-parse'): return candidate.revision
                if 'install' in args: raise u.UpdateError('Dependency failed')
                return ''
            with patch.object(u, 'run', side_effect=fake_install):
                with self.assertRaises(u.UpdateError):
                    await u.install_update(candidate)
            self.assertEqual((root / 'main.py').read_text(), 'old code')
            self.assertFalse((root / '.updates/python').exists())

    async def test_install_does_not_fetch_a_different_release(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            candidate = (await self.staged_check(root)).release
            commands = []
            async def fake_install(*args, **kwargs):
                commands.append(args)
                return candidate.revision if args[:2] == ('git', 'rev-parse') else ''
            with patch.object(u, 'run', side_effect=fake_install):
                version, interpreter, backup = await u.install_update(candidate)
            self.assertEqual(version, '2.2.0')
            self.assertEqual((root / 'VERSION').read_text(), '2.2.0')
            self.assertEqual((root / '.updates/python').read_text().strip(), interpreter)
            self.assertTrue(backup.is_dir())
            self.assertFalse(any('clone' in cmd or 'fetch' in cmd for cmd in commands))


class VersionTests(unittest.TestCase):
    def test_numeric_versions_sort_correctly_and_reject_invalid_values(self):
        from helpers.version import version_key
        self.assertGreater(version_key('2.10.0'), version_key('2.9.9'))
        for value in ('2.1', '2.1.0;echo bad', '../2.1.0', '2.1.0-beta', '02.1.0'):
            with self.assertRaises(ValueError): version_key(value)
