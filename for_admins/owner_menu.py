from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from for_admins import admin_globals
import logging

logger = logging.getLogger("xikmet_food")

def admin_menu(context, chat_id, lang_id, message_id=None):
    buttons = [
        [
            InlineKeyboardButton(text=admin_globals.BTN_ADD_PRODUCT[lang_id], callback_data="adm_add"),
            InlineKeyboardButton(text=admin_globals.BTN_DELETE_PRODUCT[lang_id], callback_data="adm_delete")],
        [
            InlineKeyboardButton(text=admin_globals.BTN_EDIT_PRODUCT[lang_id], callback_data="adm_edit"),
            InlineKeyboardButton(text=admin_globals.BTN_HIDE_PRODUCT[lang_id], callback_data="adm_stop"),
        ],
        [
            InlineKeyboardButton(text=admin_globals.BTN_STATISTICS[lang_id], callback_data="adm_stat")
        ],
    ]

    if message_id:
        logger.info(f"Admin menyu tahrirlandi | chat_id={chat_id} | message_id={message_id}")
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=admin_globals.ADMIN_PANEL_TEXT[lang_id],
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        return

    logger.info(f"Admin menyu yuborildi | chat_id={chat_id}")
    context.bot.send_message(
        chat_id=chat_id,
        text=admin_globals.ADMIN_PANEL_TEXT[lang_id],
        reply_markup=InlineKeyboardMarkup(buttons),
    )
