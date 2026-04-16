from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import Database
from config import DATA_BASE
from mini_functions import fix_phone_number
import globals
import logging

db = Database(DATA_BASE)
logger = logging.getLogger("fast_food")

def _settings_text(db_user):
    lang_id = db_user["lang_id"]
    lang_name = globals.LANGUAGE_NAMES[lang_id][lang_id]
    first_name = db_user.get("first_name") or "-"
    last_name = db_user.get("last_name") or "-"
    phone = db_user.get("phone_number") or "-"
    return (
        f"{globals.TEXT_SETTINGS_TITLE[lang_id]}\n\n"
        f"{globals.TEXT_SETTINGS_SUMMARY[lang_id].format(first_name=first_name, last_name=last_name, phone=phone, lang_name=lang_name)}"
    )

def _settings_buttons(lang_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(globals.BTN_SETTINGS_LANGUAGE[lang_id], callback_data="set_lang")],
        [InlineKeyboardButton(globals.BTN_SETTINGS_FIRST_NAME[lang_id], callback_data="set_fname")],
        [InlineKeyboardButton(globals.BTN_SETTINGS_LAST_NAME[lang_id], callback_data="set_lname")],
        [InlineKeyboardButton(globals.BTN_SETTINGS_PHONE[lang_id], callback_data="set_phone")],
        [InlineKeyboardButton(globals.BTN_BACK[lang_id], callback_data="menu_back")],
    ])

def _lang_buttons(lang_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(globals.BTN_LANG_UZ, callback_data="set_lang_uz")],
        [InlineKeyboardButton(globals.BTN_LANG_RU, callback_data="set_lang_ru")],
        [InlineKeyboardButton(globals.BTN_LANG_EN, callback_data="set_lang_en")],
        [InlineKeyboardButton(globals.BTN_BACK[lang_id], callback_data="set_back")],
    ])

def _send_settings_panel(context, chat_id, db_user):
    context.bot.send_message(
        chat_id=chat_id,
        text=_settings_text(db_user),
        reply_markup=_settings_buttons(db_user["lang_id"]),
    )

def settings_handler(update, context, db_user):
    query = update.callback_query
    query.answer()
    query.message.edit_text(
        text=_settings_text(db_user),
        reply_markup=_settings_buttons(db_user["lang_id"]),
    )

def setting_callback_handler(update, context, db_user):
    query = update.callback_query
    chat_id = query.message.chat_id
    data_sp = query.data.split("_")
    lang_id = db_user["lang_id"]

    if len(data_sp) < 2:
        query.answer()
        return

    action = data_sp[1]

    if action == "lang":
        if len(data_sp) == 2:
            query.answer()
            title = globals.TEXT_SETTINGS_CHOOSE_LANGUAGE[lang_id]
            query.message.edit_text(text=title, reply_markup=_lang_buttons(lang_id))
            return

        if len(data_sp) == 3:
            if data_sp[2] == "uz":
                db.update_user_data(chat_id, "lang_id", 1)
            elif data_sp[2] == "ru":
                db.update_user_data(chat_id, "lang_id", 2)
            elif data_sp[2] == "en":
                db.update_user_data(chat_id, "lang_id", 3)
            new_user = db.get_user_by_chat_id(chat_id)
            logger.info(f"Sozlama yangilandi | amal=til | user_id={chat_id} | yangi_lang_id={new_user['lang_id']}")
            query.answer(globals.TEXT_SETTINGS_LANGUAGE_UPDATED[new_user["lang_id"]])
            query.message.edit_text(
                text=_settings_text(new_user),
                reply_markup=_settings_buttons(new_user["lang_id"]),
            )
            return

    elif action == "fname":
        globals.USER_STEPS[chat_id] = "settings_first_name"
        query.answer()
        query.message.reply_text(globals.TEXT_SETTINGS_ENTER_FIRST_NAME[lang_id])
        return

    elif action == "lname":
        globals.USER_STEPS[chat_id] = "settings_last_name"
        query.answer()
        query.message.reply_text(globals.TEXT_SETTINGS_ENTER_LAST_NAME[lang_id])
        return

    elif action == "phone":
        globals.USER_STEPS[chat_id] = "settings_phone"
        query.answer()
        query.message.reply_text(globals.TEXT_SETTINGS_ENTER_PHONE[lang_id])
        return

    elif action == "back":
        query.answer()
        query.message.edit_text(
            text=_settings_text(db_user),
            reply_markup=_settings_buttons(lang_id),
        )
        return

    query.answer()

def handle_settings_text_message(update, context):
    if update.message is None:
        return False

    chat_id = update.message.chat_id
    step = globals.USER_STEPS.get(chat_id)
    if step not in ["settings_first_name", "settings_last_name", "settings_phone"]:
        return False

    db_user = db.get_user_by_chat_id(chat_id)
    lang_id = db_user["lang_id"]
    text = update.message.text.strip().lower()

    if step == "settings_first_name":
        db.update_user_data(chat_id, "first_name", text.lower())
        globals.USER_STEPS.pop(chat_id, None)
        update.message.reply_text(globals.TEXT_SETTINGS_FIRST_NAME_UPDATED[lang_id])
        _send_settings_panel(context, chat_id, db.get_user_by_chat_id(chat_id))
        logger.info(f"Sozlama yangilandi | amal=ism | user_id={chat_id} | yangi_qiymat={text}")
        return True

    if step == "settings_last_name":
        db.update_user_data(chat_id, "last_name", text.lower())
        globals.USER_STEPS.pop(chat_id, None)
        update.message.reply_text(globals.TEXT_SETTINGS_LAST_NAME_UPDATED[lang_id])
        _send_settings_panel(context, chat_id, db.get_user_by_chat_id(chat_id))
        logger.info(f"Sozlama yangilandi | amal=familya | user_id={chat_id} | yangi_qiymat={text}")
        return True

    if step == "settings_phone":
        phone = fix_phone_number(text, db_user=db_user, update=update, context=context)
        if phone is None:
            return True
        db.update_user_data(chat_id, "phone_number", phone)
        globals.USER_STEPS.pop(chat_id, None)
        update.message.reply_text(globals.TEXT_SETTINGS_PHONE_UPDATED[lang_id])
        _send_settings_panel(context, chat_id, db.get_user_by_chat_id(chat_id))
        logger.info(f"Sozlama yangilandi | amal=telefon | user_id={chat_id} | yangi_qiymat={phone}")
        return True

    return False
