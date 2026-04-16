from datetime import datetime
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import DATA_BASE, COMMENTS_CHANNEL
from database import Database
import globals
from for_admins import admin_globals

db = Database(DATA_BASE)
logger = logging.getLogger("xikmet_food")
ADMIN_REPLY_TARGET = {}

def _build_admin_comment_text(db_user, message_text, suggestion_id, created_at):
    lang_id = db_user.get("lang_id") or 1
    full_name = f"{db_user.get('first_name') or ''} {db_user.get('last_name') or ''}".strip()
    phone = db_user.get("phone_number") or "-"
    return (
        f"{admin_globals.TEXT_ADMIN_COMMENT_HEADER[lang_id]}\n\n"
        f"{admin_globals.TEXT_ADMIN_COMMENT_NAME[lang_id]}: {full_name or '-'}\n"
        f"{admin_globals.TEXT_ADMIN_COMMENT_PHONE[lang_id]}: {phone}\n"
        f"{admin_globals.TEXT_ADMIN_COMMENT_TIME[lang_id]}: {created_at}\n"
        f"{admin_globals.TEXT_ADMIN_COMMENT_STATUS[lang_id]}: {admin_globals.TEXT_ADMIN_COMMENT_UNREAD[lang_id]}\n\n"
        f"{admin_globals.TEXT_ADMIN_COMMENT_MESSAGE[lang_id]}:\n{message_text}"
    )

def _comment_buttons(lang_id, suggestion_id, is_read=False):
    read_text = admin_globals.BTN_SUGGESTION_READ[lang_id]
    read_callback = f"sug_read_{suggestion_id}"
    if is_read:
        read_text = f"{read_text} {admin_globals.TEXT_COMMENT_MARK_OK[lang_id]}"
        read_callback = f"sug_read_done_{suggestion_id}"
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(text=read_text, callback_data=read_callback)],
            [InlineKeyboardButton(text=admin_globals.BTN_SUGGESTION_REPLY[lang_id], callback_data=f"sug_reply_{suggestion_id}")],
        ]
    )

def start_comment_mode(update, context, db_user):

    query = update.callback_query
    chat_id = query.message.chat_id
    lang_id = db_user["lang_id"]
    globals.USER_STEPS[chat_id] = "waiting_comment"
    query.answer()
    context.bot.send_message(
        chat_id=chat_id,
        text=globals.TEXT_SEND_COMMENT[lang_id]
    )

def handle_user_comment_message(update, context):

    if update.message is None:
        return False

    chat_id = update.message.chat_id
    if globals.USER_STEPS.get(chat_id) != "waiting_comment":
        return False

    db_user = db.get_user_by_chat_id(chat_id)
    if not db_user:
        globals.USER_STEPS.pop(chat_id, None)
        return False

    message_text = update.message.text.strip()
    if not message_text:
        update.message.reply_text(globals.TEXT_SEND_COMMENT[db_user["lang_id"]])
        return True

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    suggestion_id = db.create_suggestion(
        user_id=db_user["id"],
        message=message_text,
        status=0,
        created_at=created_at,
    )
    logger.info(f"Fikr saqlandi | suggestion_id={suggestion_id} | user_id={db_user['id']} | status=0")

    admin_text = _build_admin_comment_text(db_user, message_text, suggestion_id, created_at)
    sent = context.bot.send_message(
        chat_id=COMMENTS_CHANNEL,
        text=admin_text,
        reply_markup=_comment_buttons(db_user["lang_id"], suggestion_id, is_read=False),
    )
    logger.info(
        f"Fikr kanalga yuborildi | suggestion_id={suggestion_id} | channel_id={COMMENTS_CHANNEL} | message_id={sent.message_id}"
    )

    update.message.reply_text(globals.TEXT_COMMENT_SENT[db_user["lang_id"]])
    logger.info(f"Fikr qabul xabari yuborildi | suggestion_id={suggestion_id} | user_chat_id={chat_id}")
    globals.USER_STEPS.pop(chat_id, None)
    return True

def suggestion_callback_handler(update, context):

    query = update.callback_query
    db_user = db.get_user_by_chat_id(query.from_user.id)
    data_sp = query.data.split("_")
    if len(data_sp) < 3:
        query.answer()
        return

    action = data_sp[1]
    if action == "read" and len(data_sp) > 3 and data_sp[2] == "done":
        query.answer(text=admin_globals.TEXT_COMMENT_ALREADY_READ[db_user['lang_id']], show_alert=True)
        return

    suggestion_id = int(data_sp[-1])
    suggestion = db.get_suggestion_by_id(suggestion_id)
    if not suggestion:
        query.answer(text=admin_globals.TEXT_COMMENT_NOT_FOUND[db_user['lang_id']], show_alert=True)
        logger.warning(f"Fikr topilmadi | suggestion_id={suggestion_id}")
        return

    user = db.get_user_by_id(suggestion["user"])
    if not user:
        query.answer(text=admin_globals.TEXT_COMMENT_USER_NOT_FOUND[db_user['lang_id']], show_alert=True)
        logger.warning(f"Fikr egasi topilmadi | suggestion_id={suggestion_id} | user_id={suggestion['user']}")
        return

    lang_id = user.get("lang_id") or 1
    user_chat_id = user["chat_id"]
    admin_id = query.from_user.id

    if action == "read":
        if suggestion.get("status") == 1:
            query.answer(text=admin_globals.TEXT_COMMENT_ALREADY_READ[db_user['lang_id']], show_alert=True)
            return

        read_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.update_suggestion_status(
            suggestion_id=suggestion_id,
            status=1,
            read_at=read_at,
            admin_id=admin_id,
        )
        logger.info(f"Fikr o'qilgan deb belgilandi | suggestion_id={suggestion_id} | admin_id={admin_id} | status=1")

        sent = context.bot.send_message(
            chat_id=user_chat_id,
            text=globals.TEXT_COMMENT_READ_NOTIFY[lang_id],
        )
        logger.info(
            f"O'qilganlik xabari yuborildi | suggestion_id={suggestion_id} | user_chat_id={user_chat_id} | message_id={sent.message_id}"
        )

        query.edit_message_reply_markup(
            reply_markup=_comment_buttons(lang_id, suggestion_id, is_read=True)
        )
        query.answer(admin_globals.TEXT_COMMENT_MARKED[db_user["lang_id"]])
        return

    if action == "reply":
        read_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if suggestion.get("status") == 0:
            db.update_suggestion_status(
                suggestion_id=suggestion_id,
                status=1,
                read_at=read_at,
                admin_id=admin_id,
            )
            logger.info(f"Fikr javob berishda avtomatik o'qildi | suggestion_id={suggestion_id} | admin_id={admin_id} | status=1")

        ADMIN_REPLY_TARGET[admin_id] = {
            "suggestion_id": suggestion_id,
            "channel_id": query.message.chat_id,
            "channel_message_id": query.message.message_id,
        }
        context.bot.send_message(
            chat_id=admin_id,
            text=admin_globals.TEXT_ADMIN_SEND_REPLY[db_user["lang_id"]],
        )
        logger.info(
            f"Fikrga javob rejimi yoqildi | suggestion_id={suggestion_id} | admin_id={admin_id} | channel_message_id={query.message.message_id}"
        )
        query.answer()
        return

    query.answer()

def handle_admin_reply_message(update, context):

    if update.message is None:
        return False

    admin_id = update.message.from_user.id
    target = ADMIN_REPLY_TARGET.get(admin_id)
    if not target:
        return False

    suggestion_id = target["suggestion_id"]
    suggestion = db.get_suggestion_by_id(suggestion_id)
    if not suggestion:
        ADMIN_REPLY_TARGET.pop(admin_id, None)
        admin_user = db.get_user_by_chat_id(admin_id)
        admin_lang_id = admin_user["lang_id"] if admin_user and admin_user.get("lang_id") else 1
        update.message.reply_text(admin_globals.TEXT_COMMENT_REPLY_TARGET_NOT_FOUND[admin_lang_id])
        logger.warning(f"Javob berilayotgan fikr topilmadi | suggestion_id={suggestion_id} | admin_id={admin_id}")
        return True

    user = db.get_user_by_id(suggestion["user"])
    if not user:
        ADMIN_REPLY_TARGET.pop(admin_id, None)
        admin_user = db.get_user_by_chat_id(admin_id)
        admin_lang_id = admin_user["lang_id"] if admin_user and admin_user.get("lang_id") else 1
        update.message.reply_text(admin_globals.TEXT_COMMENT_REPLY_USER_NOT_FOUND[admin_lang_id])
        logger.warning(f"Javob yuboriladigan foydalanuvchi topilmadi | suggestion_id={suggestion_id} | user_id={suggestion['user']}")
        return True

    reply_text = update.message.text.strip()
    if not reply_text:
        admin_user = db.get_user_by_chat_id(admin_id)
        admin_lang_id = admin_user["lang_id"] if admin_user and admin_user.get("lang_id") else 1
        update.message.reply_text(admin_globals.TEXT_COMMENT_REPLY_EMPTY[admin_lang_id])
        return True

    lang_id = user.get("lang_id") or 1
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.save_suggestion_reply(
        suggestion_id=suggestion_id,
        admin_id=admin_id,
        reply_text=reply_text,
        replied_at=now,
        status=1,
        read_at=now,
    )
    logger.info(f"Fikrga javob saqlandi | suggestion_id={suggestion_id} | admin_id={admin_id} | status=1")

    sent = context.bot.send_message(
        chat_id=user["chat_id"],
        text=f"{globals.TEXT_COMMENT_REPLIED_NOTIFY[lang_id]}\n\n{reply_text}",
    )
    logger.info(
        f"Fikr javobi foydalanuvchiga yuborildi | suggestion_id={suggestion_id} | user_chat_id={user['chat_id']} | message_id={sent.message_id}"
    )

    try:
        context.bot.edit_message_reply_markup(
            chat_id=target["channel_id"],
            message_id=target["channel_message_id"],
            reply_markup=_comment_buttons(lang_id, suggestion_id, is_read=True),
        )
    except Exception as e:
        logger.warning(f"Kanaldagi fikr tugmasi tahrirlanmadi | suggestion_id={suggestion_id} | xato={e}")

    admin_user = db.get_user_by_chat_id(admin_id)
    admin_lang_id = admin_user["lang_id"] if admin_user and admin_user.get("lang_id") else 1
    update.message.reply_text(admin_globals.TEXT_ADMIN_REPLY_SENT[admin_lang_id])
    ADMIN_REPLY_TARGET.pop(admin_id, None)
    return True
