import logging
from geopy import Nominatim
import globals
from database import Database
from config import DATA_BASE

db = Database(DATA_BASE)
logger = logging.getLogger("xikmet_food")

def fix_phone_number(number, db_user=None, update=None, context=None):
    if not number:
        return None
    n = number.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if n.startswith("998"):
        n = "+" + n
    if not n.startswith("+998") or len(n) != 13 or not n[1:].isdigit():
        if db_user and update:
            update.message.reply_text(globals.FIX_PHONE_NUMBER[db_user['lang_id']])
        elif update:
            update.message.reply_text(globals.FIX_PHONE_NUMBER[db_user['lang_id']])
        return None
    return n


def get_location_name(latitude, longitude):
    try:
        geolocator = Nominatim(user_agent="my_app")
        location = geolocator.reverse(f"{latitude}, {longitude}")
        return location.address
    except Exception as e:
        logger.warning(f"Lokatsiya manzili aniqlanmadi | latitude={latitude} | longitude={longitude} | xato={e}")
        return None


def read(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Matn fayli topilmadi | path={path}")
        return "Fayl topilmadi ❌"


def open_photo(path):
    try:
        with open(path, "rb") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"Rasm fayli topilmadi | path={path}")
        return None
