"""Bounded diagnostic snapshots with credential redaction."""
import os
from pathlib import Path
import re
from urllib.parse import quote
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
SECRET_NAME = re.compile(r'token|secret|password|passwd|api_hash|session|mongo|database_url|proxy|index_url|update_repo', re.I)


def redact(text):
    values = dict(os.environ)
    for name in ('Config.env', '.env'):
        path = ROOT / name
        if path.is_file():
            values.update(dotenv_values(path))
    secrets = [str(v) for k, v in values.items() if v and SECRET_NAME.search(k) and len(str(v)) >= 4]
    for value in sorted(secrets, key=len, reverse=True):
        text = text.replace(value, '[REDACTED]').replace(quote(value, safe=''), '[REDACTED]')
    text = re.sub(r'\b\d{5,}:[A-Za-z0-9_-]{20,}', '[BOT_TOKEN]', text)
    text = re.sub(r'(?i)\b(?:https?|mongodb(?:\+srv)?|redis|postgres(?:ql)?)://[^\s<>\"\']+', '[URL REDACTED]', text)
    text = re.sub(r'(?im)((?:token|secret|password|passwd|api_hash|string_session|authorization)\s*[=:]\s*).*', r'\1[REDACTED]', text)
    return text


def log_snapshot(lines=100):
    path = ROOT / 'alice_logs.txt'
    if not path.exists():
        return 'No log entries yet.'
    # Fixed path and bounded read: never accept a filename from chat.
    with path.open('rb') as handle:
        size = handle.seek(0, 2)
        handle.seek(max(0, size - 128 * 1024))
        if size > 128 * 1024:
            handle.readline()
        text = handle.read().decode('utf-8', errors='replace')
    return '\n'.join(redact(text).splitlines()[-lines:]) or 'No log entries yet.'
