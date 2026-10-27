"""Width-aware console styling; log files remain plain and searchable."""
import logging
import os
import re
import shutil
import sys
import textwrap
from logging.handlers import RotatingFileHandler

ANSI = re.compile(r'\x1b\[[0-9;]*m')

def width():
    return max(20, min(shutil.get_terminal_size((80, 24)).columns - 4, 72))

def banner(name, version, ready=False):
    use_color = sys.stdout.isatty() and 'NO_COLOR' not in os.environ
    lavender = '\033[38;2;198;182;240m' if use_color else ''
    lime = '\033[38;2;229;239;172m' if use_color else ''
    reset = '\033[0m' if use_color else ''
    size = width()
    inner = size - 4
    status = 'LISTENING ROOM OPEN' if ready else 'PREPARING THE ROOM'
    rows = [('A L I C E  /  THANOS PRO', lavender),
            ('Good music. Better together.', ''),
            ('', ''), (f'{name} · {version}', ''),
            ('Creator · Rishabh Anand', ''),
            ('', ''), (status, lime if ready else lavender),
            ('Telegram voice · 48 kHz stereo', '')]
    output = [lavender + '╭' + '─' * (size - 2) + '╮' + reset]
    for text, color in rows:
        for line in textwrap.wrap(text, inner) or ['']:
            output.append(lavender + '│ ' + reset + color + line.ljust(inner)
                          + reset + lavender + ' │' + reset)
    output.append(lavender + '╰' + '─' * (size - 2) + '╯' + reset)
    print('\n' + '\n'.join('  ' + line for line in output) + '\n', flush=True)

class ConsoleFormatter(logging.Formatter):
    def __init__(self, stream=None):
        super().__init__()
        self.stream = stream or sys.stderr

    def format(self, record):
        level = {'INFO': 'READY', 'WARNING': 'NOTICE', 'ERROR': 'ERROR', 'CRITICAL': 'ERROR', 'DEBUG': 'TRACE'}.get(record.levelname, record.levelname)
        if record.levelname == 'INFO':
            level = 'INFO'
        prefix = f'{self.formatTime(record, "%H:%M:%S")}  {level:<6}  '
        message = ANSI.sub('', record.getMessage())
        chunks = []
        for line in message.splitlines() or ['']:
            chunks.extend(textwrap.wrap(line, max(10, width() - len(prefix))) or [''])
        rendered = prefix + ('\n' + ' ' * len(prefix)).join(chunks)
        if record.exc_info:
            rendered += '\n' + self.formatException(record.exc_info)
        if self.stream.isatty() and 'NO_COLOR' not in os.environ:
            color = {logging.DEBUG: '198;182;240', logging.INFO: '229;239;172', logging.WARNING: '240;209;150'}.get(record.levelno, '240;160;170')
            return f'\033[38;2;{color}m{rendered}\033[0m'
        return rendered

def configure_logging():
    console = logging.StreamHandler()
    console.setFormatter(ConsoleFormatter(console.stream))
    file = RotatingFileHandler('alice_logs.txt', maxBytes=5_000_000, backupCount=10, encoding='utf-8')
    file.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logging.basicConfig(level=logging.INFO, handlers=[file, console], force=True)
    for name in ('asyncio', 'httpx', 'pyrogram', 'pytgcalls'):
        logging.getLogger(name).setLevel(logging.ERROR)
