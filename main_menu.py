from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import logging
import globals

logger = logging.getLogger("xikmet_food")

def send_main_menu(context, chat_id, lang_id, message_id=None):
    buttons = [
        [
            InlineKeyboardButton(text=globals.BTN_ORDER[lang_id], callback_data="menu_order")
        ],
        [
            InlineKeyboardButton(text=globals.BTN_MY_ORDERS[lang_id], callback_data="menu_myorders"),
            InlineKeyboardButton(text=globals.BTN_INFO[lang_id], callback_data="menu_info")
        ],
        [
            InlineKeyboardButton(text=globals.BTN_COMMENTS[lang_id], callback_data="menu_comments"),
            InlineKeyboardButton(text=globals.BTN_SETTINGS[lang_id], callback_data="menu_settings")
        ]
    ]
    if message_id:
        logger.info(f"Asosiy menyu tahrirlandi | chat_id={chat_id} | message_id={message_id} | lang_id={lang_id}")
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=globals.TEXT_MAIN_MENU[lang_id],
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        logger.info(f"Asosiy menyu yuborildi | chat_id={chat_id} | lang_id={lang_id}")
        context.bot.send_message(
            chat_id=chat_id,
            text=globals.TEXT_MAIN_MENU[lang_id],
            reply_markup=InlineKeyboardMarkup(buttons)
        )
