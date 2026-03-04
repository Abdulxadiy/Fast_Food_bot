from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import Database
from config import DATA_BASE
from mini_functions import fix_phone_number
import globals
import logging

db = Database(DATA_BASE)
logger = logging.getLogger("xikmet_food")

def _settings_text(db_user):
    """Sozlamalar oynasining asosiy matnini chiroyli ko'rinishda qaytaradi."""
    lang_id = db_user["lang_id"]
    lang_name = "O'zbekcha" if globals.LANGUAGE_CODE.get(lang_id) == "uz" else "Русский"
    first_name = db_user.get("first_name") or "-"
    last_name = db_user.get("last_name") or "-"
    phone = db_user.get("phone_number") or "-"

    if lang_id == 1:
        text = "⚙️ Sozlamalar\n\n"
        text += "Quyida profilingiz ma'lumotlari:\n\n"
        text += f"👤 Ism: {first_name}\n"
        text += f"🧾 Familya: {last_name}\n"
        text += f"📞 Telefon: {phone}\n"
        text += f"🌐 Til: {lang_name}\n"
        return text

    text = "⚙️ Настройки\n\n"
    text += "Ваши данные профиля:\n\n"
    text += f"👤 Имя: {first_name}\n"
    text += f"🧾 Фамилия: {last_name}\n"
    text += f"📞 Телефон: {phone}\n"
    text += f"🌐 Язык: {lang_name}\n"
    return text


def _settings_buttons(lang_id):
    """Sozlamalar panelidagi 5 ta tugmani yasaydi."""
    if lang_id == 1:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Tilni o'zgartirish", callback_data="set_lang")],
            [InlineKeyboardButton("👤 Ismni o'zgartirish", callback_data="set_fname")],
            [InlineKeyboardButton("🧾 Familyani o'zgartirish", callback_data="set_lname")],
            [InlineKeyboardButton("📞 Telefonni o'zgartirish", callback_data="set_phone")],
            [InlineKeyboardButton(globals.BTN_BACK[lang_id], callback_data="menu_back")],
        ])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Изменить язык", callback_data="set_lang")],
        [InlineKeyboardButton("👤 Изменить имя", callback_data="set_fname")],
        [InlineKeyboardButton("🧾 Изменить фамилию", callback_data="set_lname")],
        [InlineKeyboardButton("📞 Изменить телефон", callback_data="set_phone")],
        [InlineKeyboardButton(globals.BTN_BACK[lang_id], callback_data="menu_back")],
    ])


def _lang_buttons(lang_id):
    """Tilni o'zgartirish uchun alohida tugmalar."""
    back_text = "⬅️ Orqaga" if lang_id == 1 else "⬅️ Назад"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇿 Uzbek", callback_data="set_lang_uz")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru")],
        [InlineKeyboardButton(back_text, callback_data="set_back")],
    ])


def _send_settings_panel(context, chat_id, db_user):
    """Text handlerdan keyin yangi xabar qilib sozlamalar panelini yuboradi."""
    context.bot.send_message(
        chat_id=chat_id,
        text=_settings_text(db_user),
        reply_markup=_settings_buttons(db_user["lang_id"]),
    )


def settings_handler(update, context, db_user):
    """menu_settings bosilganda sozlamalar panelini chiqaradi."""
    query = update.callback_query
    query.answer()
    query.message.edit_text(
        text=_settings_text(db_user),
        reply_markup=_settings_buttons(db_user["lang_id"]),
    )


def setting_callback_handler(update, context, db_user):
    """set_* callbacklarni boshqaradi."""
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
            title = "🌐 Tilni tanlang" if lang_id == 1 else "🌐 Выберите язык"
            query.message.edit_text(text=title, reply_markup=_lang_buttons(lang_id))
            return

        if len(data_sp) == 3:
            if data_sp[2] == "uz":
                db.update_user_data(chat_id, "lang_id", 1)
            elif data_sp[2] == "ru":
                db.update_user_data(chat_id, "lang_id", 2)
            new_user = db.get_user_by_chat_id(chat_id)
            logger.info(f"Sozlama yangilandi | amal=til | user_id={chat_id} | yangi_lang_id={new_user['lang_id']}")
            query.answer("Til yangilandi" if new_user["lang_id"] == 1 else "Язык обновлен")
            query.message.edit_text(
                text=_settings_text(new_user),
                reply_markup=_settings_buttons(new_user["lang_id"]),
            )
            return

    elif action == "fname":
        globals.USER_STEPS[chat_id] = "settings_first_name"
        query.answer()
        query.message.reply_text(
            "Yangi ismingizni yozing:" if lang_id == 1 else "Введите новое имя:"
        )
        return

    elif action == "lname":
        globals.USER_STEPS[chat_id] = "settings_last_name"
        query.answer()
        query.message.reply_text(
            "Yangi familyangizni yozing:" if lang_id == 1 else "Введите новую фамилию:"
        )
        return

    elif action == "phone":
        globals.USER_STEPS[chat_id] = "settings_phone"
        query.answer()
        query.message.reply_text(
            "Yangi telefon raqam yozing: +998XXXXXXXXX" if lang_id == 1 else "Введите новый номер: +998XXXXXXXXX"
        )
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
    """Sozlamada kiritilgan yangi ism/familya/telefon matnlarini qabul qiladi."""
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
        update.message.reply_text("Ism yangilandi ✅" if lang_id == 1 else "Имя обновлено ✅")
        _send_settings_panel(context, chat_id, db.get_user_by_chat_id(chat_id))
        logger.info(f"Sozlama yangilandi | amal=ism | user_id={chat_id} | yangi_qiymat={text}")
        return True

    if step == "settings_last_name":
        db.update_user_data(chat_id, "last_name", text.lower())
        globals.USER_STEPS.pop(chat_id, None)
        update.message.reply_text("Familya yangilandi ✅" if lang_id == 1 else "Фамилия обновлена ✅")
        _send_settings_panel(context, chat_id, db.get_user_by_chat_id(chat_id))
        logger.info(f"Sozlama yangilandi | amal=familya | user_id={chat_id} | yangi_qiymat={text}")
        return True

    if step == "settings_phone":
        phone = fix_phone_number(text, db_user=db_user, update=update, context=context)
        if phone is None:
            return True
        db.update_user_data(chat_id, "phone_number", phone)
        globals.USER_STEPS.pop(chat_id, None)
        update.message.reply_text("Telefon raqam yangilandi ✅" if lang_id == 1 else "Номер обновлен ✅")
        _send_settings_panel(context, chat_id, db.get_user_by_chat_id(chat_id))
        logger.info(f"Sozlama yangilandi | amal=telefon | user_id={chat_id} | yangi_qiymat={phone}")
        return True

    return False
