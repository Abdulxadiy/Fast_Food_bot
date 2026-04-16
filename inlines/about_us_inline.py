from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from main_menu import send_main_menu
from database import Database
from config import DATA_BASE
import logging
import globals

db = Database(DATA_BASE)
logger = logging.getLogger("xikmet_food")

def about_us(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    db_user = db.get_user_by_chat_id(query.message.chat_id)

    data_sp = query.data.split("_")

    if data_sp[1] == "back":
        send_main_menu(context, chat_id, db_user["lang_id"], message_id)
        return

    button = InlineKeyboardButton(
        text=globals.BTN_BACK[db_user["lang_id"]],
        callback_data="menu_back"
    )
    text = globals.TEXT_ABOUT_US[db_user["lang_id"]]
    query.message.edit_text(text=text, reply_markup=InlineKeyboardMarkup([[button]]))
