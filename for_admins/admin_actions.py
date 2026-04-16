import logging

from telegram import Update

import globals
from config import DATA_BASE
from database import Database
from for_admins.admin_globals import (
    TEXT_ADMIN_REPLY_SENT,
    TEXT_COMMENT_REPLY_EMPTY,
    TEXT_ASK_REJECT_REASON,
    TEXT_ORDER_ACCEPTED_MARK,
    TEXT_ORDER_ACCEPTED_NOTICE,
    TEXT_ORDER_LABEL,
    TEXT_ORDER_REJECTED_MARK,
    TEXT_REASON_UNKNOWN,
    TEXT_REASON_MISSING,
    TEXT_REASON_SENT,
)
from for_admins.menu_edit import handle_admin_edit_text
from for_admins.menu_add import handle_admin_category_text
from inlines.comments_inline import handle_admin_reply_message, handle_user_comment_message
from inlines.setting_inline import handle_settings_text_message

db = Database(DATA_BASE)
logger = logging.getLogger("xikmet_food")
admin_awaiting_reason = {}

def admin_action_handler(update: Update, context):
    query = update.callback_query
    logger.info(f"Admin tugma signali qabul qilindi | data={query.data}")

    try:
        data_sp = query.data.split("_")

        action = data_sp[1]
        order_id = int(data_sp[2])
        user_chat_id = int(data_sp[3])
        lang_id = int(data_sp[4])
        admin_id = query.from_user.id
        admin_db_user = db.get_user_by_chat_id(admin_id)
        admin_lang_id = admin_db_user["lang_id"]

        try:
            query.answer()
        except Exception as e:
            logger.warning(f"Tugma signaliga javob yuborilmadi | order_id={order_id} | xato={e}")

        if action == "accept":
            db.update_order_status(order_id, 1)
            logger.info(f"Buyurtma qabul qilindi | order_id={order_id} | admin_id={admin_id} | user_chat_id={user_chat_id}")
            try:
                original_text = query.message.text or ""
                query.edit_message_text(text=original_text + f"\n\n{TEXT_ORDER_ACCEPTED_MARK[admin_lang_id]}")
            except Exception as e:
                logger.warning(f"Admin kanaldagi xabar tahrirlanmadi | order_id={order_id} | xato={e}")
                try:
                    context.bot.send_message(chat_id=admin_id, text=TEXT_ORDER_ACCEPTED_NOTICE[admin_lang_id].format(order_id))
                except Exception as notify_e:
                    logger.warning(f"Adminga tasdiq xabari yuborilmadi | order_id={order_id} | admin_id={admin_id} | xato={notify_e}")

            try:
                context.bot.send_message(
                    chat_id=user_chat_id,
                    text=globals.TEXT_ORDER_ACCEPTED_FINAL[lang_id],
                )
            except Exception as e:
                logger.warning(f"Foydalanuvchiga qabul xabari yuborilmadi | order_id={order_id} | user_chat_id={user_chat_id} | xato={e}")

        elif action == "reject":
            db.update_order_status(order_id, -1)
            logger.info(f"Buyurtma rad etildi | order_id={order_id} | admin_id={admin_id} | user_chat_id={user_chat_id}")

            try:
                original_text = query.message.text or ""
                query.edit_message_text(text=original_text + f"\n\n{TEXT_ORDER_REJECTED_MARK[admin_lang_id]}")
            except Exception as e:
                logger.warning(f"Admin kanaldagi xabar tahrirlanmadi | order_id={order_id} | xato={e}")

            admin_awaiting_reason[admin_id] = {
                "order_id": order_id,
                "user_chat_id": user_chat_id,
                "lang_id": lang_id,
            }

            try:
                context.bot.send_message(
                    chat_id=admin_id,
                    text=f"{TEXT_ASK_REJECT_REASON[admin_lang_id]}\n\n{TEXT_ORDER_LABEL[admin_lang_id]}: {order_id}",
                )
            except Exception as e:
                logger.warning(f"Admina rad etish sababi so'ralmadi | order_id={order_id} | admin_id={admin_id} | xato={e}")
                try:
                    context.bot.send_message(
                        chat_id=user_chat_id,
                        text=globals.TEXT_ORDER_REJECTED[lang_id].format(TEXT_REASON_UNKNOWN[admin_lang_id]),
                    )
                except Exception as send_e:
                    logger.error(f"Foydalanuvchiga rad etish xabari yuborilmadi | order_id={order_id} | user_chat_id={user_chat_id} | xato={send_e}")
                admin_awaiting_reason.pop(admin_id, None)

    except Exception as e:
        logger.error(f"Admin amali handlerida xato | xato={e}")

def admin_reply_handler(update: Update, context):

    if update.message is None:
        return
    if handle_settings_text_message(update, context):
        return
    if handle_admin_reply_message(update, context):
        return
    if handle_user_comment_message(update, context):
        return
    if handle_admin_edit_text(update, context):
        return
    if handle_admin_category_text(update, context):
        return

    admin_id = update.message.from_user.id
    if admin_id in admin_awaiting_reason:
        admin_db_user = db.get_user_by_chat_id(admin_id)
        admin_lang_id = admin_db_user["lang_id"]
        reason_text = (update.message.text or "").strip() or TEXT_REASON_MISSING[admin_lang_id]
        data = admin_awaiting_reason[admin_id]

        user_chat_id = data["user_chat_id"]
        lang_id = data["lang_id"]

        try:
            context.bot.send_message(
                chat_id=user_chat_id,
                text=globals.TEXT_ORDER_REJECTED[lang_id].format(reason_text),
            )
            update.message.reply_text(TEXT_REASON_SENT[admin_lang_id])
            logger.info(
                f"Rad etish sababi yuborildi | order_id={data['order_id']} | admin_id={admin_id} | user_chat_id={user_chat_id}"
            )
        except Exception as e:
            logger.warning(
                f"Rad etish sababi yuborilmadi | order_id={data['order_id']} | admin_id={admin_id} | user_chat_id={user_chat_id} | xato={e}"
            )

        del admin_awaiting_reason[admin_id]
