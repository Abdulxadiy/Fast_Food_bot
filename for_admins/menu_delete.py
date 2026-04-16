from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging

from config import DATA_BASE, OWNER
from database import Database
from for_admins import admin_globals
from for_admins.owner_menu import admin_menu

db = Database(DATA_BASE)
logger = logging.getLogger("fast_food")

def _build_delete_mode_markup(lang_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=admin_globals.BTN_DELETE_PRODUCT_MODE[lang_id],
                    callback_data="adm_dmode_product",
                )
            ],
            [
                InlineKeyboardButton(
                    text=admin_globals.BTN_DELETE_CATEGORY_MODE[lang_id],
                    callback_data="adm_dmode_category",
                )
            ],
            [InlineKeyboardButton(text=admin_globals.BTN_BACK[lang_id], callback_data="adm_back")],
        ]
    )

def _build_products_markup(lang_id):
    products = db.get_all_products()
    if not products:
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton(text=admin_globals.BTN_BACK[lang_id], callback_data="adm_delete")]]
        )

    buttons = []
    name_col = f"name_{admin_globals.LANGUAGE_CODE[lang_id]}"
    for product in products:
        label = f"{product[name_col]} - {product['price']}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"adm_dp_{product['id']}")])

    buttons.append([InlineKeyboardButton(text=admin_globals.BTN_BACK[lang_id], callback_data="adm_delete")])
    return InlineKeyboardMarkup(buttons)

def _build_categories_markup(lang_id):
    categories = db.get_all_categories()
    if not categories:
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton(text=admin_globals.BTN_BACK[lang_id], callback_data="adm_delete")]]
        )

    name_col = f"name_{admin_globals.LANGUAGE_CODE[lang_id]}"
    by_id = {c["id"]: c for c in categories}
    buttons = []

    for cat in categories:
        parent = by_id.get(cat.get("parent"))
        parent_name = parent[name_col] if parent else admin_globals.TEXT_CATEGORY_ROOT[lang_id]
        label = f"{cat[name_col]} ({parent_name})"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"adm_dc_{cat['id']}")])

    buttons.append([InlineKeyboardButton(text=admin_globals.BTN_BACK[lang_id], callback_data="adm_delete")])
    return InlineKeyboardMarkup(buttons)

def _build_product_text(product, lang_id):
    suffix = admin_globals.LANGUAGE_CODE[lang_id]
    name_col = f"name_{suffix}"
    desc_col = f"description_{suffix}"

    text = f"{admin_globals.TEXT_DELETE_PRODUCT_DETAIL[lang_id]}\n\n"
    text += f"{admin_globals.TEXT_FIELD_ID[lang_id]}: {product['id']}\n"
    text += f"{product[name_col]}\n"
    text += f"{admin_globals.TEXT_FIELD_PRICE[lang_id]}: {product['price']}\n"
    text += f"\n{product.get(desc_col) or ''}"
    return text

def _build_category_text(category, lang_id):
    name_col = f"name_{admin_globals.LANGUAGE_CODE[lang_id]}"
    return (
        f"{admin_globals.TEXT_DELETE_CATEGORY_DETAIL[lang_id]}\n\n"
        f"{admin_globals.TEXT_FIELD_ID[lang_id]}: {category['id']}\n"
        f"{admin_globals.TEXT_FIELD_NAME[lang_id]}: {category[name_col]}\n"
    )

def _build_product_menu(product_id, lang_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=admin_globals.BTN_DELETE_THIS_PRODUCT[lang_id],
                    callback_data=f"adm_dcf_{product_id}",
                )
            ],
            [InlineKeyboardButton(text=admin_globals.BTN_BACK[lang_id], callback_data="adm_dmode_product")],
        ]
    )

def _build_category_menu(category_id, lang_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=admin_globals.BTN_DELETE_THIS_CATEGORY[lang_id],
                    callback_data=f"adm_dccf_{category_id}",
                )
            ],
            [InlineKeyboardButton(text=admin_globals.BTN_BACK[lang_id], callback_data="adm_dmode_category")],
        ]
    )

def _build_confirm_product_menu(product_id, lang_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=admin_globals.BTN_CONFIRM_DELETE[lang_id],
                    callback_data=f"adm_ddel_{product_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=admin_globals.BTN_CANCEL_DELETE[lang_id],
                    callback_data=f"adm_dp_{product_id}",
                )
            ],
        ]
    )

def _build_confirm_category_menu(category_id, lang_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=admin_globals.BTN_CONFIRM_DELETE[lang_id],
                    callback_data=f"adm_dcdel_{category_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=admin_globals.BTN_CANCEL_DELETE[lang_id],
                    callback_data=f"adm_dc_{category_id}",
                )
            ],
        ]
    )

def menu_delete_handler(update, context):
    query = update.callback_query
    data_sp = query.data.split("_")
    admin_id = query.from_user.id
    db_user = db.get_user_by_chat_id(admin_id)
    lang_id = db_user["lang_id"]

    if admin_id != OWNER:
        logger.warning(f"Ruxsatsiz admin o'chirish bo'limiga kirdi | admin_id={admin_id}")
        query.answer(admin_globals.TEXT_ONLY_OWNER[lang_id], show_alert=True)
        return

    query.answer()

    if len(data_sp) < 2:
        return

    if data_sp[1] == "delete":
        logger.info(f"O'chirish menyusi ochildi | admin_id={admin_id}")
        query.message.edit_text(
            text=admin_globals.TEXT_DELETE_MENU[lang_id],
            reply_markup=_build_delete_mode_markup(lang_id),
        )
        return

    if data_sp[1] == "dmode" and len(data_sp) >= 3:
        if data_sp[2] == "product":
            query.message.edit_text(
                text=admin_globals.TEXT_DELETE_PRODUCTS[lang_id],
                reply_markup=_build_products_markup(lang_id),
            )
            return

        if data_sp[2] == "category":
            query.message.edit_text(
                text=admin_globals.TEXT_DELETE_CATEGORIES[lang_id],
                reply_markup=_build_categories_markup(lang_id),
            )
            return

    if data_sp[1] == "dp" and len(data_sp) >= 3:
        product_id = int(data_sp[2])
        product = db.get_product_by_id(product_id)
        if not product:
            logger.warning(f"O'chirish uchun mahsulot topilmadi | admin_id={admin_id} | product_id={product_id}")
            query.answer(admin_globals.TEXT_DELETE_PRODUCT_NOT_FOUND[lang_id], show_alert=True)
            return

        query.message.edit_text(
            text=_build_product_text(product, lang_id),
            reply_markup=_build_product_menu(product_id, lang_id),
        )
        return

    if data_sp[1] == "dc" and len(data_sp) >= 3:
        category_id = int(data_sp[2])
        category = db.get_category_by_id(category_id)
        if not category:
            logger.warning(f"O'chirish uchun kategoriya topilmadi | admin_id={admin_id} | category_id={category_id}")
            query.answer(admin_globals.TEXT_DELETE_CATEGORY_NOT_FOUND[lang_id], show_alert=True)
            return

        query.message.edit_text(
            text=_build_category_text(category, lang_id),
            reply_markup=_build_category_menu(category_id, lang_id),
        )
        return

    if data_sp[1] == "dcf" and len(data_sp) >= 3:
        product_id = int(data_sp[2])
        product = db.get_product_by_id(product_id)
        if not product:
            logger.warning(f"O'chirishni tasdiqlashda mahsulot topilmadi | admin_id={admin_id} | product_id={product_id}")
            query.answer(admin_globals.TEXT_DELETE_PRODUCT_NOT_FOUND[lang_id], show_alert=True)
            return

        text = _build_product_text(product, lang_id)
        text += f"\n\n{admin_globals.TEXT_DELETE_CONFIRM[lang_id]}"
        query.message.edit_text(text=text, reply_markup=_build_confirm_product_menu(product_id, lang_id))
        return

    if data_sp[1] == "dccf" and len(data_sp) >= 3:
        category_id = int(data_sp[2])
        category = db.get_category_by_id(category_id)
        if not category:
            logger.warning(f"O'chirishni tasdiqlashda kategoriya topilmadi | admin_id={admin_id} | category_id={category_id}")
            query.answer(admin_globals.TEXT_DELETE_CATEGORY_NOT_FOUND[lang_id], show_alert=True)
            return

        text = _build_category_text(category, lang_id)
        text += f"\n\n{admin_globals.TEXT_DELETE_CATEGORY_CONFIRM[lang_id]}"
        query.message.edit_text(text=text, reply_markup=_build_confirm_category_menu(category_id, lang_id))
        return

    if data_sp[1] == "ddel" and len(data_sp) >= 3:
        product_id = int(data_sp[2])
        product = db.get_product_by_id(product_id)
        if not product:
            logger.warning(f"Mahsulotni yakuniy o'chirishda topilmadi | admin_id={admin_id} | product_id={product_id}")
            query.answer(admin_globals.TEXT_DELETE_PRODUCT_NOT_FOUND[lang_id], show_alert=True)
            return

        db.delete_product(product_id)
        logger.info(f"Mahsulot o'chirildi | admin_id={admin_id} | product_id={product_id}")
        context.bot.send_message(chat_id=admin_id, text=admin_globals.TEXT_PRODUCT_DELETED[lang_id])
        admin_menu(context, admin_id, lang_id, query.message.message_id)
        return

    if data_sp[1] == "dcdel" and len(data_sp) >= 3:
        category_id = int(data_sp[2])
        category = db.get_category_by_id(category_id)
        if not category:
            logger.warning(f"Kategoriyani yakuniy o'chirishda topilmadi | admin_id={admin_id} | category_id={category_id}")
            query.answer(admin_globals.TEXT_DELETE_CATEGORY_NOT_FOUND[lang_id], show_alert=True)
            return

        cat_count, product_count = db.delete_category_cascade(category_id)
        logger.info(
            f"Kategoriya kaskad o'chirildi | admin_id={admin_id} | category_id={category_id} | categories={cat_count} | products={product_count}"
        )
        msg = (
            f"{admin_globals.TEXT_CATEGORY_DELETED[lang_id]}\n"
            f"{admin_globals.TEXT_DELETE_RESULT[lang_id].format(categories=cat_count, products=product_count)}"
        )
        context.bot.send_message(chat_id=admin_id, text=msg)
        admin_menu(context, admin_id, lang_id, query.message.message_id)
        return
