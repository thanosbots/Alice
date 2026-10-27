"""Staged repository updates; runtime data never comes from the repository."""
import asyncio
from dataclasses import dataclass
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import uuid
from helpers.version import VERSION, read_version, version_key

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = 'https://github.com/thanosbots/Alice.git'
PROTECTED = {'.git', '.updates', '.venv', '.bootstrap', '.python', '.uv-cache',
             'Config.env', '.env', 'downloads', 'cache', 'alice_cache'}
lock = asyncio.Lock()
restart_requested = asyncio.Event()
restart_python = None


class UpdateError(Exception):
    pass


def safe_path(name):
    path = PurePosixPath(name)
    return (bool(name) and not path.is_absolute() and '..' not in path.parts
            and not any(p in PROTECTED or p == '__pycache__' for p in path.parts)
            and not any(p.endswith(('.session', '.session-journal', '.pyc', '.log'))
                        or p.startswith('alice_logs.txt') for p in path.parts))


async def run(*args, cwd=None, timeout=180):
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', PIP_DISABLE_PIP_VERSION_CHECK='1')
    process = await asyncio.create_subprocess_exec(
        *map(str, args), cwd=cwd, env=env,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    try:
        output, _ = await asyncio.wait_for(process.communicate(), timeout)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        process.kill()
        await process.communicate()
        raise
    if process.returncode:
        # Never echo subprocess output to Telegram: URLs may contain credentials.
        raise UpdateError(f'{Path(str(args[0])).name} failed (exit {process.returncode}).')
    return output.decode(errors='replace').strip()


def apply_files(root, source, names, previous, backup):
    """Copy only tracked code. Roll back all changed files on any failure."""
    names, previous = set(names), set(previous)
    touched = sorted(names | previous)
    for name in touched:
        if not safe_path(name):
            raise UpdateError(f'Repository contains a protected path: {name}')
        target = root / name
        relatives = [root / Path(*PurePosixPath(name).parts[:i])
                     for i in range(1, len(PurePosixPath(name).parts) + 1)]
        if any(p.is_symlink() for p in relatives):
            raise UpdateError('Symlink paths cannot be updated automatically.')
        if target.exists() and not target.is_file():
            raise UpdateError(f'Local path is not a regular file: {name}')
        if name in names and (not (source / name).is_file() or (source / name).is_symlink()):
            raise UpdateError('Repository contains an unsupported file type.')
    backup.mkdir(parents=True)
    existed = []
    for name in touched:
        target = root / name
        if target.exists():
            saved = backup / name
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
            existed.append(name)
    (backup / 'restore-manifest.json').write_text(json.dumps({'touched': touched, 'existed': existed}))
    try:
        for name in touched:
            target = root / name
            if name in names:
                target.parent.mkdir(parents=True, exist_ok=True)
                temp = target.with_name(target.name + '.update-tmp')
                shutil.copy2(source / name, temp)
                os.replace(temp, target)
            elif target.exists():
                target.unlink()
    except BaseException:
        for name in touched:
            target = root / name
            if name in existed:
                shutil.copy2(backup / name, target)
            elif target.is_file():
                target.unlink()
        raise


@dataclass(frozen=True)
class Release:
    root: Path
    directory: Path
    source: Path
    repo: str
    revision: str
    version: str
    files: tuple


@dataclass(frozen=True)
class UpdateCheck:
    latest_version: str
    release: Release | None = None


def discard_release(release):
    if release and release.directory.parent == release.root / '.updates':
        shutil.rmtree(release.directory, ignore_errors=True)


async def check_update(root=ROOT, repo=None, branch=None):
    """Read a remote release without installing code or dependencies."""
    root = Path(root).resolve()
    repo = repo or os.getenv('UPDATE_REPO') or DEFAULT_REPO
    branch = branch or os.getenv('UPDATE_BRANCH')
    if not shutil.which('git'):
        raise UpdateError('Git is missing. Install Git on this host first.')
    if not repo.startswith(('https://', 'ssh://', 'git@')):
        raise UpdateError('UPDATE_REPO must be an HTTPS or SSH Git repository.')
    workspace = root / '.updates'
    workspace.mkdir(exist_ok=True)
    release = workspace / uuid.uuid4().hex
    release.mkdir()
    source = release / 'source'
    args = ['git', 'clone', '--depth', '1']
    if branch:
        if branch.startswith('-'):
            raise UpdateError('Invalid UPDATE_BRANCH.')
        args += ['--branch', branch]
    try:
        await run(*args, '--', repo, source, timeout=180)
        revision = await run('git', 'rev-parse', 'HEAD', cwd=source)
        try:
            latest_version = read_version(source)
        except (OSError, ValueError) as exc:
            shutil.rmtree(release)
            raise UpdateError('Publish a valid VERSION file with the new release first.') from exc
        if version_key(latest_version) <= version_key(VERSION):
            shutil.rmtree(release)
            return UpdateCheck(latest_version)
        names = (await run('git', 'ls-files', '-z', cwd=source)).split('\x00')
        names = [name for name in names if name]
        # Runtime files in a repository are rejected rather than deployed.
        if not all(safe_path(name) for name in names):
            raise UpdateError('Remote repository tracks configuration, sessions or runtime files; update refused.')
        for required in ('VERSION', 'main.py', 'requirements.txt', 'helpers/updater.py', 'plugins/update.py', 'start.sh'):
            if required not in names:
                raise UpdateError('Publish the /update-enabled Alice code to this repository first.')
        if 'restart_requested' not in (source / 'main.py').read_text():
            raise UpdateError('Remote main.py does not support safe update restart.')
        for name in names:
            if (source / name).is_symlink():
                raise UpdateError('Remote repository contains symlinks; update refused.')
            if name.endswith('.py'):
                compile((source / name).read_bytes(), name, 'exec')
        return UpdateCheck(latest_version, Release(root, release, source, repo, revision, latest_version, tuple(names)))
    except BaseException:
        shutil.rmtree(release, ignore_errors=True)
        raise


async def install_update(candidate):
    """Install only the staged commit the owner approved; never fetch a new HEAD."""
    root, release, source = candidate.root, candidate.directory, candidate.source
    repo, revision, names = candidate.repo, candidate.revision, candidate.files
    if version_key(candidate.version) <= version_key(VERSION):
        raise UpdateError('This release is no longer newer than the running version.')
    if await run('git', 'rev-parse', 'HEAD', cwd=source) != revision:
        raise UpdateError('The checked release changed. Run /update again.')
    await run('git', 'diff', '--exit-code', 'HEAD', '--', cwd=source)
    workspace = root / '.updates'
    state_path = workspace / 'state.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    interpreter = release / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    await run(sys.executable, '-m', 'venv', interpreter.parent.parent, timeout=120)
    uv = root / '.bootstrap/bin/uv'
    if uv.is_file():
        await run(uv, 'pip', 'install', '--python', interpreter, '-r', source / 'requirements.txt', timeout=900)
    else:
        await run(interpreter, '-m', 'pip', 'install', '-r', source / 'requirements.txt', timeout=900)
    await run(interpreter, '-m', 'pip', 'check', timeout=60)
    await run(interpreter, '-c', 'import pyrogram, pytgcalls, motor, aiohttp, PIL, dotenv', timeout=60)
    # Record the old code before applying. Local configuration is never touched.
    backup = release / 'backup'
    previous = state.get('files', [])
    apply_files(root, source, names, previous, backup)
    new_state = {'repo': repo, 'revision': revision, 'version': candidate.version, 'files': names, 'backup': str(backup)}
    try:
        temporary = workspace / 'state.tmp'
        temporary.write_text(json.dumps(new_state, indent=2))
        os.replace(temporary, state_path)
        marker = workspace / 'python.tmp'
        marker.write_text(str(interpreter) + '\n')
        os.replace(marker, workspace / 'python')
    except BaseException:
        # The old process can keep running; restore code if activation fails.
        manifest = json.loads((backup / 'restore-manifest.json').read_text())
        for name in manifest['touched']:
            target = root / name
            if name in manifest['existed']:
                shutil.copy2(backup / name, target)
            elif target.is_file():
                target.unlink()
        if state:
            state_path.write_text(json.dumps(state))
        else:
            state_path.unlink(missing_ok=True)
        raise
    return candidate.version, str(interpreter), backup


def request_restart(interpreter):
    global restart_python
    restart_python = interpreter
    restart_requested.set()
