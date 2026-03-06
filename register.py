from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ConversationHandler, MessageHandler, Filters, CommandHandler, CallbackQueryHandler
from mini_functions import fix_phone_number
from database import Database
from config import DATA_BASE
from config import OWNER
import globals
import main_menu
import logging

db = Database(DATA_BASE)
logger = logging.getLogger("xikmet_food")
FIRST_NAME, LAST_NAME, PHONE = range(3)

def registration(reply, chat_id, context):
    db_user = db.get_user_by_chat_id(chat_id)

    if not db_user:
        db.create_user(chat_id)
        buttons = [
            [InlineKeyboardButton(text=globals.BTN_LANG_UZ, callback_data="lang_uz")],
            [InlineKeyboardButton(text=globals.BTN_LANG_RU, callback_data="lang_ru")]
        ]
        reply(text=globals.WELCOME_TEXT)
        reply(
            text=globals.CHOOSE_LANG,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return ConversationHandler.END

    elif not db_user["lang_id"]:
        buttons = [
            [InlineKeyboardButton(text=globals.BTN_LANG_UZ, callback_data="lang_uz")],
            [InlineKeyboardButton(text=globals.BTN_LANG_RU, callback_data="lang_ru")]
        ]
        reply(
            text=globals.CHOOSE_LANG,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return ConversationHandler.END

    elif not db_user['first_name']:
        reply(
            text=globals.TEXT_ENTER_FIRST_NAME[db_user['lang_id']],
            reply_markup=ReplyKeyboardRemove()
        )
        return FIRST_NAME

    elif not db_user['last_name']:
        reply(
            text=globals.TEXT_ENTER_LAST_NAME[db_user['lang_id']],
            reply_markup=ReplyKeyboardRemove()
        )
        return LAST_NAME

    elif not db_user['phone_number']:
        buttons = [
            [KeyboardButton(text=globals.BTN_SEND_CONTACT[db_user['lang_id']], request_contact=True)]
        ]
        reply(text=globals.BTN_SEND_CONTACT[db_user['lang_id']])
        reply(
            text=globals.TEXT_ENTER_CONTACT[db_user['lang_id']],
            reply_markup=ReplyKeyboardMarkup(
                keyboard=buttons,
                resize_keyboard=True
            )
        )
        return PHONE

    else:
        reply(globals.REPLAY_END[db_user['lang_id']], reply_markup=ReplyKeyboardRemove())
        main_menu.send_main_menu(context, chat_id, db_user['lang_id'])
        return ConversationHandler.END

def start(update, context):
    user = update.message.from_user
    chat_id = user.id
    reply = update.message.reply_text
    db_user = db.get_user_by_chat_id(chat_id)

    username = user.username or "username yo'q"
    logger.info(
        f"Start buyrug'i bosildi | user_id={chat_id} | username=@{username}"
    )
    if user.id == OWNER:
        ad_buttons = [
            [InlineKeyboardButton(text=globals.SIMPLE_MENU[db_user['lang_id']], callback_data="choice_simple")],
            [InlineKeyboardButton(text=globals.ADMIN_MENU[db_user['lang_id']], callback_data="choice_adminmenu")]
        ]
        update.message.reply_text(globals.WELCOME_TEXT_ADMIN[db_user['lang_id']], reply_markup=ReplyKeyboardRemove())
        update.message.reply_text(globals.CHOICE_FOR_ADMIN[db_user['lang_id']], reply_markup=InlineKeyboardMarkup(ad_buttons))
        logger.info(
            f"Admin paneliga kirdi | user_id={chat_id} | username=@{username}"
        )
        return ConversationHandler.END
    return registration(reply, chat_id, context)


def cancel(update, context):
    update.message.reply_text("Barchasi bekor qlindi ⚠️")
    username = update.message.from_user.username or "username yo'q"
    logger.info(
        f"Ro'yxatdan o'tish bekor qilindi | user_id={update.message.from_user.id} | username=@{username}"
    )
    return ConversationHandler.END

def first_name_handler(update, context):
    user = update.message.from_user
    db_user = db.get_user_by_chat_id(user.id)
    first_name = update.message.text.strip().lower()
    db.update_user_data(user.id, "first_name", first_name)
    update.message.reply_text(text=globals.TEXT_ENTER_LAST_NAME[db_user['lang_id']])
    return LAST_NAME


def last_name_handler(update, context):
    user = update.message.from_user
    db_user = db.get_user_by_chat_id(user.id)
    last_name = update.message.text.strip().lower()
    db.update_user_data(user.id, "last_name", last_name)

    buttons = [
        [KeyboardButton(text=globals.BTN_SEND_CONTACT[db_user['lang_id']], request_contact=True)]
    ]
    update.message.reply_text(text=globals.BTN_SEND_CONTACT[db_user['lang_id']])
    update.message.reply_text(
        text=globals.TEXT_ENTER_CONTACT[db_user['lang_id']],
        reply_markup=ReplyKeyboardMarkup(
            keyboard=buttons,
            resize_keyboard=True
        )
    )
    return PHONE


def contact_handler(update, context):
    user = update.message.from_user
    db_user = db.get_user_by_chat_id(user.id)

    if update.message.contact:
        phone_number = update.message.contact.phone_number
        number = fix_phone_number(phone_number, db_user, update, context)
        if number is None:
            update.message.reply_text(text=globals.TEXT_ENTER_CONTACT[db_user['lang_id']])
            return PHONE
        db.update_user_data(user.id, "phone_number", number)
        main_menu.send_main_menu(context, user.id, db_user['lang_id'])
        username = update.message.from_user.username or "username yo'q"
        logger.info(
            f"Ro'yxatdan o'tish yakunlandi | user_id={user.id} | username=@{username}"
        )
        return ConversationHandler.END

    else:
        phone_number = update.message.text
        phone = fix_phone_number(phone_number, db_user, update, context)
        if phone is None:
            update.message.reply_text(text=globals.TEXT_ENTER_CONTACT[db_user['lang_id']])
            return PHONE
        db.update_user_data(user.id, "phone_number", phone)

        update.message.reply_text(globals.REPLAY_END[db_user['lang_id']])
        main_menu.send_main_menu(context, user.id, db_user['lang_id'])

        username = update.message.from_user.username or "username yo'q"
        logger.info(
            f"Ro'yxatdan o'tish yakunlandi | user_id={update.message.from_user.id} | username=@{username}"
        )
        return ConversationHandler.END


def lang_callback(update, context):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    data = query.data

    if data == "lang_uz":
        db.update_user_data(chat_id, "lang_id", 1)
        logger.info(f"Til tanlandi | user_id={chat_id} | lang_id=1")
    elif data == "lang_ru":
        db.update_user_data(chat_id, "lang_id", 2)
        logger.info(f"Til tanlandi | user_id={chat_id} | lang_id=2")

    db_user = db.get_user_by_chat_id(chat_id)
    query.message.delete()
    
    context.bot.send_message(
        chat_id=chat_id,
        text=globals.TEXT_ENTER_FIRST_NAME[db_user['lang_id']],
        reply_markup=ReplyKeyboardRemove()
    )
    return FIRST_NAME


conversation = ConversationHandler(
    entry_points=[
        CommandHandler('start', start),
        CallbackQueryHandler(lang_callback, pattern='^lang_')
    ],
    states={
        FIRST_NAME: [MessageHandler(Filters.text & ~Filters.command, first_name_handler)],
        LAST_NAME: [MessageHandler(Filters.text & ~Filters.command, last_name_handler)],
        PHONE: [MessageHandler((Filters.contact | Filters.regex(r'^\+998\d{9}$')) & ~Filters.command, contact_handler)],
    }, fallbacks=[CommandHandler('cancel', cancel)]
)
