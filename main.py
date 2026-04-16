from telegram.ext import Updater, CallbackQueryHandler, MessageHandler, Filters, CommandHandler
from logging.handlers import RotatingFileHandler
from database import Database
from register import conversation
from config import DATA_BASE, TOKEN
from queries import query_handler
from location_handler import location_handler
from for_admins.admin_actions import admin_reply_handler
import logging
import globals

db = Database(DATA_BASE)

logger = logging.getLogger("xikmet_food")


logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)


file_handler = RotatingFileHandler(
    "texts/logging_info.log",
    maxBytes=5_000_000,
    backupCount=10
)
file_handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(file_handler)

logger.info("Bot ishga tushdi | holat=boshlanish")

def bot_info(update, context):
    db_user = db.get_user_by_chat_id(update.message.chat_id)
    lang_id = db_user["lang_id"] if db_user and db_user.get("lang_id") else 1
    update.message.reply_text(globals.TEXT_BOT_INFO[lang_id])

def main():
    logger.info("Bot ishga tushirilmoqda | rejim=polling")
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("info", bot_info))
    dp.add_handler(conversation)
    dp.add_handler(CallbackQueryHandler(query_handler))
    dp.add_handler(MessageHandler(Filters.location, location_handler))
    dp.add_handler(
        MessageHandler(
            (Filters.text | Filters.photo) & ~Filters.command,
            admin_reply_handler
        )
    )

    updater.start_polling()
    logger.info("Bot ishga tushdi | holat: polling_boshlandi")
    updater.idle()

if __name__ == '__main__':
    main()
