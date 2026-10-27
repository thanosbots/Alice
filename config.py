import os
import sys
import dotenv
from helpers.version import BOT_NAME

if os.path.exists("Config.env"):
    dotenv.load_dotenv("Config.env")

class Config:
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    STRING_SESSION = os.getenv("STRING_SESSION", "")
    MONGO_URL = os.getenv("MONGO_URL", "")
    OWNER_ID = int(os.getenv("OWNER_ID", 0))
    LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", 0))
    MUSIC_QUALITY = int(os.getenv("MUSIC_QUALITY", "320"))
    MAX_DOWNLOAD_MB = max(1, int(os.getenv("MAX_DOWNLOAD_MB", "40")))
    MAX_TRACK_MINUTES = max(1, int(os.getenv("MAX_TRACK_MINUTES", "30")))
    MAX_QUEUE_SIZE = max(1, int(os.getenv("MAX_QUEUE_SIZE", "50")))
    if MUSIC_QUALITY not in (96, 160, 320):
        raise ValueError("MUSIC_QUALITY must be 96, 160, or 320")
    SUPPORT_GROUP = "https://t.me/thanosprosss"
    SUPPORT_CHANNEL = "https://t.me/THANOS_PRO"

    if not all([API_ID, API_HASH, BOT_TOKEN, STRING_SESSION, MONGO_URL]):
        print(f"\n{BOT_NAME} Configuration Error!")
        print("Check Config.env and the deployment guide at https://alicemusic.online.\n")
        sys.exit(1)
