from telegram.ext import Updater, CallbackQueryHandler, MessageHandler, Filters, CommandHandler
from logging.handlers import RotatingFileHandler
from database import Database
from register import conversation
from config import DATA_BASE, TOKEN
from mini_functions import read
from queries import query_handler
from location_handler import location_handler
from for_admins.admin_actions import admin_reply_handler
import logging

db = Database(DATA_BASE)

logger = logging.getLogger("xikmet_food")
"""
bu vaziyatda "xikmet_food" asosiy logger nomi bo'ladi, bu orqali loglarni boshqarish osonlashadi va 
duplikatsiyani oldini olish mumkin. Agar boshqa modullarda ham log yozish kerak bo'lsa, ular ham "xikmet_food" loggeridan 
foydalanishi mumkin, bu esa loglarni markazlashtirishga yordam beradi.
"""
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

# 🔁 Rotating file handler
file_handler = RotatingFileHandler(
    "texts/logging_info.log",
    maxBytes=5_000_000,   # 5MB dan oshganda yangi faylga o'tadi
    backupCount=10 # eski log fayllarini saqlash soni (faqat 10 ta eski fayl saqlanadi)
)
file_handler.setFormatter(formatter) # log formatini o'rnatish

if not logger.handlers:
    logger.addHandler(file_handler) # loglarni faylga yozish uchun handlerni loggerga qo'shish

logger.info("Bot ishga tushdi | holat=boshlanish")

def bot_info(update, context):
    path = "texts/bot_info.txt"
    text = read(path)
    update.message.reply_text(text)

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