from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging

from config import DATA_BASE, OWNER
from database import Database
from for_admins import admin_globals
from for_admins.owner_menu import admin_menu

db = Database(DATA_BASE)
logger = logging.getLogger("xikmet_food")

def _build_stat_menu(lang_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=admin_globals.BTN_STAT_MONTHLY[lang_id],
                    callback_data="adm_st1m",
                )
            ],
            [
                InlineKeyboardButton(
                    text=admin_globals.BTN_STAT_ALL[lang_id],
                    callback_data="adm_stall",
                )
            ],
            [InlineKeyboardButton(text=admin_globals.BTN_BACK[lang_id], callback_data="adm_back")],
        ]
    )

def _format_stats_text(items, lang_id, monthly=False):
    header = (
        admin_globals.TEXT_STAT_MONTH_HEADER[lang_id]
        if monthly
        else admin_globals.TEXT_STAT_ALL_HEADER[lang_id]
    )

    if not items:
        return f"{header}\n* {admin_globals.TEXT_STAT_EMPTY[lang_id]}"

    lines = [header, "+--------------------------------+"]
    for idx, row in enumerate(items, start=1):
        name_col = f"name_{admin_globals.LANGUAGE_CODE[lang_id]}"
        name = row.get(name_col) or admin_globals.TEXT_FALLBACK_DELETED_PRODUCT[lang_id].format(row["product_id"])
        sold_count = row.get("sold_count", 0)
        lines.append(f"| {idx}. {name}")
        lines.append(f"|    {admin_globals.TEXT_STAT_SOLD[lang_id].format(sold_count)}")
        lines.append("+--------------------------------+")

    return "\n".join(lines)

def menu_statistics_handler(update, context):
    query = update.callback_query
    data_sp = query.data.split("_")
    admin_id = query.from_user.id
    db_user = db.get_user_by_chat_id(admin_id)
    lang_id = db_user["lang_id"]

    if admin_id != OWNER:
        logger.warning(f"Ruxsatsiz admin statistika bo'limiga kirdi | admin_id={admin_id}")
        query.answer(admin_globals.TEXT_ONLY_OWNER[lang_id], show_alert=True)
        return

    query.answer()

    if len(data_sp) < 2:
        return

    if data_sp[1] == "stat":
        logger.info(f"Statistika menyusi ochildi | admin_id={admin_id}")
        query.message.edit_text(
            text=admin_globals.TEXT_STAT_MENU[lang_id],
            reply_markup=_build_stat_menu(lang_id),
        )
        return

    if data_sp[1] == "st1m":
        items = db.get_product_sales_statistics(days=30)
        logger.info(f"1 oylik statistika so'raldi | admin_id={admin_id} | qatorlar={len(items)}")
        context.bot.send_message(
            chat_id=admin_id,
            text=_format_stats_text(items, lang_id, monthly=True),
        )
        admin_menu(context, admin_id, lang_id)
        return

    if data_sp[1] == "stall":
        items = db.get_product_sales_statistics(days=None)
        logger.info(f"Umumiy statistika so'raldi | admin_id={admin_id} | qatorlar={len(items)}")
        context.bot.send_message(
            chat_id=admin_id,
            text=_format_stats_text(items, lang_id, monthly=False),
        )
        admin_menu(context, admin_id, lang_id)
        return
