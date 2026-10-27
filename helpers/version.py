"""Release metadata shared by startup, Telegram panels and the updater."""
from pathlib import Path
import re


def version_key(value):
    value = value.strip()
    if not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', value):
        raise ValueError('VERSION must use major.minor.patch, for example 2.1.0')
    return tuple(map(int, value.split('.')))


def read_version(root):
    value = (Path(root) / 'VERSION').read_text(encoding='utf-8').strip()
    version_key(value)
    return value


VERSION = read_version(Path(__file__).resolve().parents[1])
BOT_NAME = 'Alice Music Bot'
