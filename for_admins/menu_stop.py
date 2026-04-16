from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging
from config import DATA_BASE, OWNER
from database import Database
from for_admins import admin_globals
from for_admins.owner_menu import admin_menu

db = Database(DATA_BASE)
logger = logging.getLogger("fast_food")

def _build_products_markup(lang_id):
    products = db.get_all_products()
    if not products:
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton(text=admin_globals.BTN_BACK[lang_id], callback_data="adm_back")]]
        )

    buttons = []
    name_col = f"name_{admin_globals.LANGUAGE_CODE[lang_id]}"
    for product in products:
        status = product.get("status_stop") or 0
        status_mark = (
            admin_globals.TEXT_STATUS_SWITCH_OFF[lang_id]
            if status == 1
            else admin_globals.TEXT_STATUS_SWITCH_ON[lang_id]
        )
        label = f"{product[name_col]} - {product['price']} ({status_mark})"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"adm_sp_{product['id']}")])

    buttons.append([InlineKeyboardButton(text=admin_globals.BTN_BACK[lang_id], callback_data="adm_back")])
    return InlineKeyboardMarkup(buttons)

def _build_stop_detail_text(product, lang_id):
    suffix = admin_globals.LANGUAGE_CODE[lang_id]
    name_col = f"name_{suffix}"
    desc_col = f"description_{suffix}"
    status = product.get("status_stop") or 0
    status_text = (
        admin_globals.TEXT_STOP_STATUS_INACTIVE[lang_id]
        if status == 1
        else admin_globals.TEXT_STOP_STATUS_ACTIVE[lang_id]
    )

    text = f"{admin_globals.TEXT_STOP_PRODUCT_DETAIL[lang_id]}\n\n"
    text += f"{admin_globals.TEXT_FIELD_ID[lang_id]}: {product['id']}\n"
    text += f"{product[name_col]}\n"
    text += f"{admin_globals.TEXT_FIELD_PRICE[lang_id]}: {product['price']}\n"
    text += f"{admin_globals.TEXT_FIELD_STATUS[lang_id]}: {status_text}\n"
    text += f"\n{product.get(desc_col) or ''}"
    return text

def _build_stop_detail_markup(product_id, status_stop, lang_id):
    action_btn = (
        InlineKeyboardButton(
            text=admin_globals.BTN_RETURN_TO_SALE[lang_id],
            callback_data=f"adm_sst_{product_id}_0",
        )
        if status_stop == 1
        else InlineKeyboardButton(
            text=admin_globals.BTN_TAKE_OFF_SALE[lang_id],
            callback_data=f"adm_sst_{product_id}_1",
        )
    )

    return InlineKeyboardMarkup(
        [
            [action_btn],
            [InlineKeyboardButton(text=admin_globals.BTN_BACK[lang_id], callback_data="adm_stop")],
        ]
    )

def menu_stop_handler(update, context):
    query = update.callback_query
    data_sp = query.data.split("_")
    admin_id = query.from_user.id
    db_user = db.get_user_by_chat_id(admin_id)
    lang_id = db_user["lang_id"]

    if admin_id != OWNER:
        logger.warning(f"Ruxsatsiz admin sotuv holati bo'limiga kirdi | admin_id={admin_id}")
        query.answer(admin_globals.TEXT_ONLY_OWNER[lang_id], show_alert=True)
        return

    query.answer()

    if len(data_sp) < 2:
        return

    if data_sp[1] == "stop":
        logger.info(f"Sotuv holatini boshqarish menyusi ochildi | admin_id={admin_id}")
        query.message.edit_text(
            text=admin_globals.TEXT_STOP_PRODUCTS[lang_id],
            reply_markup=_build_products_markup(lang_id),
        )
        return

    if data_sp[1] == "sp" and len(data_sp) >= 3:
        product_id = int(data_sp[2])
        product = db.get_product_by_id(product_id)
        if not product:
            logger.warning(f"Sotuv holati uchun mahsulot topilmadi | admin_id={admin_id} | product_id={product_id}")
            query.answer(admin_globals.TEXT_STOP_PRODUCT_NOT_FOUND[lang_id], show_alert=True)
            return

        status = product.get("status_stop") or 0
        query.message.edit_text(
            text=_build_stop_detail_text(product, lang_id),
            reply_markup=_build_stop_detail_markup(product_id, status, lang_id),
        )
        return

    if data_sp[1] == "sst" and len(data_sp) >= 4:
        product_id = int(data_sp[2])
        new_status = int(data_sp[3])

        product = db.get_product_by_id(product_id)
        if not product:
            logger.warning(f"Sotuv holati yangilashda mahsulot topilmadi | admin_id={admin_id} | product_id={product_id}")
            query.answer(admin_globals.TEXT_STOP_PRODUCT_NOT_FOUND[lang_id], show_alert=True)
            return

        db.update_product_stop_status(product_id, new_status)
        logger.info(
            f"Mahsulot sotuv holati yangilandi | admin_id={admin_id} | product_id={product_id} | status_stop={new_status}"
        )
        context.bot.send_message(
            chat_id=admin_id,
            text=(
                admin_globals.TEXT_PRODUCT_STOPPED[lang_id]
                if new_status == 1
                else admin_globals.TEXT_PRODUCT_RETURNED[lang_id]
            ),
        )
        admin_menu(context, admin_id, lang_id, query.message.message_id)
        return
