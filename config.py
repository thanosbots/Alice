import os
import sys
import dotenv
from helpers._0x3c4d import _g1, _g2, _g3, _g4, _g5, _g6, _g7, _g8

if os.path.exists("Config.env"):
    dotenv.load_dotenv("Config.env")

class _C:
    _n = _g1()
    _fn = _g7()
    _u = _g5()
    _dn = _g2()
    _du = _g6()
    _v = _g8()
    _f = _g3()
    _e = _g4()
    
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    STRING_SESSION = os.getenv("STRING_SESSION", "")
    MONGO_URL = os.getenv("MONGO_URL", "")
    OWNER_ID = int(os.getenv("OWNER_ID", 0))
    LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", 0))
    START_IMAGE_URL = os.getenv("START_IMAGE_URL", "https://ibb.co/Z7CxX7b")
    CUSTOM_API_URL = "api-url" # get from thanosceo
    CUSTOM_API_KEY = "api-key" # get from thanosceo
    SUPPORT_GROUP = "https://t.me/thanosprosss"
    SUPPORT_CHANNEL = "https://t.me/THANOS_PRO"
    
    if not all([API_ID, API_HASH, BOT_TOKEN, STRING_SESSION, MONGO_URL]):
        print(f"\n{_n} Configuration Error!")
        print(f"Contact {_du} for support.\n")
        sys.exit()


HELP_DICT = {}
