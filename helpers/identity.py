"""Presentation identity is based exclusively on the configured numeric owner ID."""
from html import escape

OWNER_NAME = 'Rishabh Anand'
OWNER_LABEL = '♛ Rishabh Anand · Creator'

def is_owner(user):
    from config import Config
    owner_id = getattr(Config, 'OWNER_ID', 0)
    return bool(owner_id and user and user.id == owner_id)

def selection_name(user):
    if is_owner(user):
        return OWNER_LABEL
    return f'@{user.username}' if user.username else user.first_name

def owner_note(user):
    return '<i>♛ Rishabh Anand · Your private edition</i>' if is_owner(user) else ''

def owner_text(text):
    # Owner-only command plugins use Markdown; no dynamic user input here.
    return '**♛ Rishabh Anand · Owner desk**\n\n' + text

def owner_mention(user):
    return f'<a href="tg://user?id={user.id}">{escape(OWNER_NAME)}</a>'
