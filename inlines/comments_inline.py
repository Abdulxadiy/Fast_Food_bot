from datetime import datetime
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import DATA_BASE, COMMENTS_CHANNEL
from database import Database
import globals

db = Database(DATA_BASE)
logger = logging.getLogger("xikmet_food")


def _build_admin_comment_text(db_user, message_text, suggestion_id, created_at):
    """Adminga ketadigan comment matnini bitta joyda yig'ib beradi."""
    full_name = f"{db_user.get('first_name') or ''} {db_user.get('last_name') or ''}".strip()
    phone = db_user.get("phone_number") or "-"
    return (
        f"Yangi fikr keldi\n\n"
        # f"ID: {suggestion_id}\n"
        # f"User ID: {db_user['id']}\n"
        # f"Chat ID: {db_user['chat_id']}\n"
        f"Ism: {full_name or '-'}\n"
        f"Tel: {phone}\n"
        f"Vaqt: {created_at}\n"
        f"Status: O'qilmagan (0)\n\n"
        f"Xabar:\n{message_text}"
    )


def _comment_buttons(lang_id, suggestion_id, is_read=False):
    """Comment ostidagi inline tugmalarni yasaydi: O'qilgan / Javob berish."""
    read_text = globals.BTN_SUGGESTION_READ[lang_id]
    read_callback = f"sug_read_{suggestion_id}"
    if is_read:
        read_text = f"{read_text} OK"
        read_callback = f"sug_read_done_{suggestion_id}"
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(text=read_text, callback_data=read_callback)],
            [InlineKeyboardButton(text=globals.BTN_SUGGESTION_REPLY[lang_id], callback_data=f"sug_reply_{suggestion_id}")],
        ]
    )


def start_comment_mode(update, context, db_user):
    """menu_comments bosilganda foydalanuvchini comment yozish rejimiga o'tkazadi."""
    query = update.callback_query
    chat_id = query.message.chat_id
    lang_id = db_user["lang_id"]
    globals.USER_STEPS[chat_id] = "waiting_comment"  # User ayni payt comment yozish bosqichida ekanini xotirada saqlaymiz
    query.answer()
    context.bot.send_message(  # Userga comment yozish bo'yicha yo'riqnoma yuboramiz
        chat_id=chat_id,
        text=globals.TEXT_SEND_COMMENT[lang_id]
    )


def handle_user_comment_message(update, context):
    """Foydalanuvchidan kelgan commentni qabul qiladi, DB ga yozadi va kanalga yuboradi."""
    if update.message is None:
        return False

    chat_id = update.message.chat_id
    if globals.USER_STEPS.get(chat_id) != "waiting_comment":  # User comment bosqichida bo'lmasa bu handlerdan chiqib ketamiz
        return False

    db_user = db.get_user_by_chat_id(chat_id)
    if not db_user:
        globals.USER_STEPS.pop(chat_id, None)
        return False

    message_text = update.message.text.strip()
    if not message_text:  # Bo'sh text yuborsa yana qayta so'raymiz
        update.message.reply_text(globals.TEXT_SEND_COMMENT[db_user["lang_id"]])
        return True

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    suggestion_id = db.create_suggestion(  # Commentni DB ga 0 (o'qilmagan) holatda yozamiz
        user_id=db_user["id"],
        message=message_text,
        status=0,
        created_at=created_at,
    )
    logger.info(f"Fikr saqlandi | suggestion_id={suggestion_id} | user_id={db_user['id']} | status=0")

    admin_text = _build_admin_comment_text(db_user, message_text, suggestion_id, created_at)
    sent = context.bot.send_message(  # Commentni alohida kanalga inline tugmalar bilan yuboramiz
        chat_id=COMMENTS_CHANNEL,
        text=admin_text,
        reply_markup=_comment_buttons(db_user["lang_id"], suggestion_id, is_read=False),
    )
    logger.info(
        f"Fikr kanalga yuborildi | suggestion_id={suggestion_id} | channel_id={COMMENTS_CHANNEL} | message_id={sent.message_id}"
    )

    update.message.reply_text(globals.TEXT_COMMENT_SENT[db_user["lang_id"]])  # Userga "yuborildi" degan tasdiqni yuboramiz
    logger.info(f"Fikr qabul xabari yuborildi | suggestion_id={suggestion_id} | user_chat_id={chat_id}")
    globals.USER_STEPS.pop(chat_id, None)  # User step tozalanadi (comment bosqichi tugadi)
    return True


def suggestion_callback_handler(update, context):
    """Kanaldagi comment tugmalari bosilganda ishlaydi: sug_read_<id> / sug_reply_<id>."""
    query = update.callback_query
    db_user = db.get_user_by_chat_id(query.from_user.id)
    data_sp = query.data.split("_")
    if len(data_sp) < 3:
        query.answer()
        return

    action = data_sp[1]  # read yoki reply
    if action == "read" and len(data_sp) > 3 and data_sp[2] == "done":
        query.answer(text=globals.ALREADY_READ[db_user['lang_id']], show_alert=True)
        return

    suggestion_id = int(data_sp[-1])  # callback_data oxiridan comment id ni olamiz
    suggestion = db.get_suggestion_by_id(suggestion_id)
    if not suggestion:
        query.answer(text=globals.NOT_FOUND_COMMENT[db_user['lang_id']], show_alert=True)
        logger.warning(f"Fikr topilmadi | suggestion_id={suggestion_id}")
        return

    user = db.get_user_by_id(suggestion["user"])
    if not user:
        query.answer(text=globals.NOT_FOUND_USER[db_user['lang_id']], show_alert=True)
        logger.warning(f"Fikr egasi topilmadi | suggestion_id={suggestion_id} | user_id={suggestion['user']}")
        return

    lang_id = user.get("lang_id") or 1  # Userda til bo'sh bo'lsa default 1 (uz)
    user_chat_id = user["chat_id"]
    admin_id = query.from_user.id

    if action == "read":  # Admin "O'qilgan" tugmasini bosganda
        if suggestion.get("status") == 1:
            query.answer(text=globals.ALREADY_READ[db_user['lang_id']], show_alert=True)
            return

        read_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.update_suggestion_status(
            suggestion_id=suggestion_id,
            status=1,
            read_at=read_at,
            admin_id=admin_id,
        )
        logger.info(f"Fikr o'qilgan deb belgilandi | suggestion_id={suggestion_id} | admin_id={admin_id} | status=1")

        sent = context.bot.send_message(  # Userga "xabaringiz o'qildi" deb xabar yuboramiz
            chat_id=user_chat_id,
            text=globals.TEXT_COMMENT_READ_NOTIFY[lang_id],
        )
        logger.info(
            f"O'qilganlik xabari yuborildi | suggestion_id={suggestion_id} | user_chat_id={user_chat_id} | message_id={sent.message_id}"
        )

        query.edit_message_reply_markup(  # Kanaldagi tugma holatini yangilaymiz (o'qilgan deb ko'rinadi)
            reply_markup=_comment_buttons(lang_id, suggestion_id, is_read=True)
        )
        query.answer("Belgilandi")
        return

    if action == "reply":  # Admin "Javob berish" tugmasini bosganda
        read_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if suggestion.get("status") == 0:
            db.update_suggestion_status(
                suggestion_id=suggestion_id,
                status=1,
                read_at=read_at,
                admin_id=admin_id,
            )
            logger.info(f"Fikr javob berishda avtomatik o'qildi | suggestion_id={suggestion_id} | admin_id={admin_id} | status=1")

        globals.ADMIN_REPLY_TARGET[admin_id] = {  # Admin uchun qaysi commentga reply yozayotganini xotirada saqlaymiz
            "suggestion_id": suggestion_id,
            "channel_id": query.message.chat_id,
            "channel_message_id": query.message.message_id,
        }
        context.bot.send_message(
            chat_id=admin_id,
            text=globals.TEXT_ADMIN_SEND_REPLY[lang_id],
        )
        logger.info(
            f"Fikrga javob rejimi yoqildi | suggestion_id={suggestion_id} | admin_id={admin_id} | channel_message_id={query.message.message_id}"
        )
        query.answer()
        return

    query.answer()


def handle_admin_reply_message(update, context):
    """Admin private chatda reply yuborganda uni userga yetkazadi va DB ga yozadi."""
    if update.message is None:
        return False

    admin_id = update.message.from_user.id
    target = globals.ADMIN_REPLY_TARGET.get(admin_id)
    if not target:
        return False

    suggestion_id = target["suggestion_id"]  # Admin aynan qaysi commentga javob yozayotganini olamiz
    suggestion = db.get_suggestion_by_id(suggestion_id)
    if not suggestion:
        globals.ADMIN_REPLY_TARGET.pop(admin_id, None)
        update.message.reply_text("Fikr topilmadi.")
        logger.warning(f"Javob berilayotgan fikr topilmadi | suggestion_id={suggestion_id} | admin_id={admin_id}")
        return True

    user = db.get_user_by_id(suggestion["user"])
    if not user:
        globals.ADMIN_REPLY_TARGET.pop(admin_id, None)
        update.message.reply_text("User topilmadi.")
        logger.warning(f"Javob yuboriladigan foydalanuvchi topilmadi | suggestion_id={suggestion_id} | user_id={suggestion['user']}")
        return True

    reply_text = update.message.text.strip()  # Admin yuborgan javob matni
    if not reply_text:
        update.message.reply_text("Javob matni bo'sh bo'lmasin.")
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

    sent = context.bot.send_message(  # Userga o'qildi + javob yozildi xabarini bitta xabarda yuboramiz
        chat_id=user["chat_id"],
        text=f"{globals.TEXT_COMMENT_REPLIED_NOTIFY[lang_id]}\n\n{reply_text}",
    )
    logger.info(
        f"Fikr javobi foydalanuvchiga yuborildi | suggestion_id={suggestion_id} | user_chat_id={user['chat_id']} | message_id={sent.message_id}"
    )

    try:  # Kanaldagi tugmani ham o'qilgan holatga edit qilamiz
        context.bot.edit_message_reply_markup(
            chat_id=target["channel_id"],
            message_id=target["channel_message_id"],
            reply_markup=_comment_buttons(lang_id, suggestion_id, is_read=True),
        )
    except Exception as e:
        logger.warning(f"Kanaldagi fikr tugmasi tahrirlanmadi | suggestion_id={suggestion_id} | xato={e}")

    update.message.reply_text(globals.TEXT_ADMIN_REPLY_SENT[lang_id])
    globals.ADMIN_REPLY_TARGET.pop(admin_id, None)  # Admin reply bosqichi yopiladi
    return True
