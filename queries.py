from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import Database
from config import DATA_BASE
from inlines.about_us_inline import about_us
from inlines.main_inlines import inline_handler
from inlines.my_orders_inline import my_orders_handler, order_detail_handler
from main_menu import send_main_menu
from for_admins.owner_menu import admin_menu
from for_admins.menu_add import menu_add_handler
from for_admins.menu_edit import menu_edit_handler
from for_admins.menu_stop import menu_stop_handler
from for_admins.menu_delete import menu_delete_handler
from for_admins.menu_statistics import menu_statistics_handler
from for_admins.admin_actions import admin_action_handler
from inlines.comments_inline import start_comment_mode, suggestion_callback_handler
from inlines.setting_inline import settings_handler, setting_callback_handler
import main_menu
import logging
import globals

db = Database(DATA_BASE)
logger = logging.getLogger("xikmet_food")

def query_handler(update, context):
    q = update.callback_query
    chat_id = q.message.chat_id
    db_user = db.get_user_by_chat_id(chat_id)
    message_id = q.message.message_id
    data_sp = q.data.split("_")

    if data_sp[0] == "choice":
        if data_sp[1] == "simple":
            main_menu.send_main_menu(context, chat_id, db_user['lang_id'])
        elif data_sp[1] == "adminmenu":
            admin_menu(context, chat_id, db_user["lang_id"])
    if data_sp[0] == "admin":
        admin_action_handler(update, context)
        return
    if data_sp[0] == "sug":
        suggestion_callback_handler(update, context)
        return
    elif data_sp[0] == "adm":
        if len(data_sp) < 2:
            q.answer()
            return
        if data_sp[1] in ["add", "open", "cat", "root", "noop", "back"]:
            menu_add_handler(update, context)
            return
        elif data_sp[1] in ["edit", "ep", "en", "epr", "ed", "ei"]:
            menu_edit_handler(update, context)
            return
        elif data_sp[1] in ["stop", "sp", "sst"]:
            menu_stop_handler(update, context)
            return
        elif data_sp[1] in ["delete", "dmode", "dp", "dc", "dcf", "dccf", "ddel", "dcdel"]:
            menu_delete_handler(update, context)
            return
        elif data_sp[1] in ["stat", "st1m", "stall"]:
            menu_statistics_handler(update, context)
            return

    if not db_user:
        q.answer()
        return

    if data_sp[0] == "set":
        setting_callback_handler(update, context, db_user)
        return

    if data_sp[0] == "menu":
        if data_sp[1] in ["myorders"]:
            my_orders_handler(update, context)

        elif data_sp[1] == "comments":
            start_comment_mode(update, context, db_user)

        elif data_sp[1] == "settings":
            settings_handler(update, context, db_user)

        elif data_sp[1] == "info":
            about_us(update, context)

        elif data_sp[1] == "order":
            categories = db.get_categories_by_parent()
            buttons = []
            row = []
            for i in range(len(categories)):
                row.append(
                    InlineKeyboardButton(
                        text=categories[i][f'name_{globals.LANGUAGE_CODE[db_user["lang_id"]]}'],
                        callback_data=f"category_{categories[i]['id']}"
                    )
                )

                if len(row) == 2 or (len(categories) % 2 == 1 and i == len(categories) - 1):
                    buttons.append(row)
                    row = []

            buttons.append([
                InlineKeyboardButton(
                    text=globals.BTN_BACK[db_user["lang_id"]],
                    callback_data="menu_back"
                )
            ])

            context.bot.edit_message_text(
                text=globals.TEXT_ORDER[db_user['lang_id']],
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
                chat_id=chat_id,
                message_id=message_id
            )

        elif data_sp[1] == "back":
            send_main_menu(context, chat_id, db_user['lang_id'], message_id)

    elif data_sp[0] == "order" and len(data_sp) > 1:
        try:
            int(data_sp[1])
            order_detail_handler(update, context)
        except ValueError:
            pass

    elif data_sp[0] in ["category", "product", "quantity", "buy", "payment", "clear"]:
        inline_handler(update, context)
