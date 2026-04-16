import os
import re
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import DATA_BASE, OWNER
from database import Database
from for_admins import admin_globals
from for_admins.owner_menu import admin_menu

db = Database(DATA_BASE)
admin_edit_state = {}
logger = logging.getLogger("xikmet_food")

def _slugify_filename(text):
    s = (text or "").strip().lower()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^a-z0-9_-]", "", s)
    return s or "product"

def _build_unique_image_path(base_name):
    os.makedirs("images", exist_ok=True)
    i = 0
    while True:
        filename = f"{base_name}.jpg" if i == 0 else f"{base_name}-{i}.jpg"
        path = os.path.join("images", filename)
        if not os.path.exists(path):
            return path
        i += 1

def _save_photo_to_images(update, product_name_uz):
    if not update.message.photo:
        return None
    tg_file = update.message.photo[-1].get_file()
    base_name = _slugify_filename(product_name_uz)
    image_path = _build_unique_image_path(base_name)
    tg_file.download(custom_path=image_path)
    return image_path

def _build_products_markup(lang_id):
    products = db.get_all_products()
    if not products:
        buttons = [[InlineKeyboardButton(text=admin_globals.BTN_BACK[lang_id], callback_data="adm_back")]]
        return InlineKeyboardMarkup(buttons)

    buttons = []
    name_col = f"name_{admin_globals.LANGUAGE_CODE[lang_id]}"
    for product in products:
        label = f"{product[name_col]} - {product['price']}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"adm_ep_{product['id']}")])

    buttons.append([InlineKeyboardButton(text=admin_globals.BTN_BACK[lang_id], callback_data="adm_back")])
    return InlineKeyboardMarkup(buttons)

def _build_product_edit_menu(lang_id, product_id):
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(text=admin_globals.BTN_EDIT_NAME[lang_id], callback_data=f"adm_en_{product_id}")],
            [InlineKeyboardButton(text=admin_globals.BTN_EDIT_PRICE[lang_id], callback_data=f"adm_epr_{product_id}")],
            [InlineKeyboardButton(text=admin_globals.BTN_EDIT_DESC[lang_id], callback_data=f"adm_ed_{product_id}")],
            [InlineKeyboardButton(text=admin_globals.BTN_EDIT_IMAGE[lang_id], callback_data=f"adm_ei_{product_id}")],
            [InlineKeyboardButton(text=admin_globals.BTN_BACK[lang_id], callback_data="adm_edit")],
        ]
    )

def menu_edit_handler(update, context):
    query = update.callback_query
    data_sp = query.data.split("_")
    admin_id = query.from_user.id
    db_user = db.get_user_by_chat_id(admin_id)
    lang_id = db_user["lang_id"]

    if admin_id != OWNER:
        logger.warning(f"Ruxsatsiz admin tahrirlash bo'limiga kirdi | admin_id={admin_id}")
        query.answer(admin_globals.TEXT_ONLY_OWNER[lang_id], show_alert=True)
        return

    query.answer()
    if len(data_sp) < 2:
        return

    if data_sp[1] == "edit":
        logger.info(f"Mahsulot tahrirlash menyusi ochildi | admin_id={admin_id}")
        products = db.get_all_products()
        text = admin_globals.TEXT_EDIT_PRODUCTS[lang_id] if products else admin_globals.TEXT_NO_PRODUCTS[lang_id]
        query.message.edit_text(text=text, reply_markup=_build_products_markup(lang_id))
        return

    if data_sp[1] == "ep" and len(data_sp) >= 3:
        product_id = int(data_sp[2])
        query.message.edit_text(
            text=admin_globals.TEXT_EDIT_MENU[lang_id],
            reply_markup=_build_product_edit_menu(lang_id, product_id),
        )
        return

    if data_sp[1] == "en" and len(data_sp) >= 3:
        product_id = int(data_sp[2])
        admin_edit_state[admin_id] = {"step": "edit_name_uz", "data": {"product_id": product_id}}
        logger.info(f"Mahsulot nomini tahrirlash boshlandi | admin_id={admin_id} | product_id={product_id}")
        context.bot.send_message(chat_id=admin_id, text=admin_globals.TEXT_ENTER_NEW_NAME_UZ[lang_id])
        return

    if data_sp[1] == "epr" and len(data_sp) >= 3:
        product_id = int(data_sp[2])
        admin_edit_state[admin_id] = {"step": "edit_price", "data": {"product_id": product_id}}
        logger.info(f"Mahsulot narxini tahrirlash boshlandi | admin_id={admin_id} | product_id={product_id}")
        context.bot.send_message(chat_id=admin_id, text=admin_globals.TEXT_ENTER_NEW_PRICE[lang_id])
        return

    if data_sp[1] == "ed" and len(data_sp) >= 3:
        product_id = int(data_sp[2])
        admin_edit_state[admin_id] = {"step": "edit_desc_uz", "data": {"product_id": product_id}}
        logger.info(f"Mahsulot tavsifini tahrirlash boshlandi | admin_id={admin_id} | product_id={product_id}")
        context.bot.send_message(chat_id=admin_id, text=admin_globals.TEXT_ENTER_NEW_DESC_UZ[lang_id])
        return

    if data_sp[1] == "ei" and len(data_sp) >= 3:
        product_id = int(data_sp[2])
        admin_edit_state[admin_id] = {"step": "edit_image", "data": {"product_id": product_id}}
        logger.info(f"Mahsulot rasmini tahrirlash boshlandi | admin_id={admin_id} | product_id={product_id}")
        context.bot.send_message(chat_id=admin_id, text=admin_globals.TEXT_ENTER_NEW_IMAGE[lang_id])
        return

    if data_sp[1] == "back":
        admin_menu(context, admin_id, lang_id, query.message.message_id)
        return

def handle_admin_edit_text(update, context):
    if update.message is None:
        return False

    admin_id = update.message.from_user.id
    state = admin_edit_state.get(admin_id)
    if not state:
        return False

    db_user = db.get_user_by_chat_id(admin_id)
    lang_id = db_user["lang_id"]
    step = state["step"]
    data = state["data"]
    text = (update.message.text or "").strip()

    if step != "edit_image" and not text:
        update.message.reply_text(admin_globals.TEXT_EMPTY_TEXT[lang_id])
        return True

    if step == "edit_name_uz":
        data["name_uz"] = text
        state["step"] = "edit_name_ru"
        update.message.reply_text(admin_globals.TEXT_ENTER_NEW_NAME_RU[lang_id])
        return True

    if step == "edit_name_ru":
        data["name_ru"] = text
        state["step"] = "edit_name_en"
        update.message.reply_text(admin_globals.TEXT_ENTER_NEW_NAME_EN[lang_id])
        return True

    if step == "edit_name_en":
        data["name_en"] = text
        product_id = data["product_id"]
        db.update_product_names(product_id, data["name_uz"], data["name_ru"], data["name_en"])
        logger.info(f"Mahsulot nomi yangilandi | admin_id={admin_id} | product_id={product_id}")
        update.message.reply_text(admin_globals.TEXT_EDIT_SUCCESS[lang_id])
        admin_edit_state.pop(admin_id, None)
        context.bot.send_message(
            chat_id=admin_id,
            text=admin_globals.TEXT_EDIT_MENU[lang_id],
            reply_markup=_build_product_edit_menu(lang_id, product_id),
        )
        return True

    if step == "edit_price":
        if not text.isdigit():
            update.message.reply_text(admin_globals.TEXT_INVALID_PRICE[lang_id])
            return True
        product_id = data["product_id"]
        db.update_product_price(product_id, int(text))
        logger.info(f"Mahsulot narxi yangilandi | admin_id={admin_id} | product_id={product_id} | yangi_narx={int(text)}")
        update.message.reply_text(admin_globals.TEXT_EDIT_SUCCESS[lang_id])
        admin_edit_state.pop(admin_id, None)
        context.bot.send_message(
            chat_id=admin_id,
            text=admin_globals.TEXT_EDIT_MENU[lang_id],
            reply_markup=_build_product_edit_menu(lang_id, product_id),
        )
        return True

    if step == "edit_desc_uz":
        data["desc_uz"] = text
        state["step"] = "edit_desc_ru"
        update.message.reply_text(admin_globals.TEXT_ENTER_NEW_DESC_RU[lang_id])
        return True

    if step == "edit_desc_ru":
        data["desc_ru"] = text
        state["step"] = "edit_desc_en"
        update.message.reply_text(admin_globals.TEXT_ENTER_NEW_DESC_EN[lang_id])
        return True

    if step == "edit_desc_en":
        data["desc_en"] = text
        product_id = data["product_id"]
        db.update_product_descriptions(product_id, data["desc_uz"], data["desc_ru"], data["desc_en"])
        logger.info(f"Mahsulot tavsifi yangilandi | admin_id={admin_id} | product_id={product_id}")
        update.message.reply_text(admin_globals.TEXT_EDIT_SUCCESS[lang_id])
        admin_edit_state.pop(admin_id, None)
        context.bot.send_message(
            chat_id=admin_id,
            text=admin_globals.TEXT_EDIT_MENU[lang_id],
            reply_markup=_build_product_edit_menu(lang_id, product_id),
        )
        return True

    if step == "edit_image":
        product_id = data["product_id"]
        product = db.get_product_by_id(product_id)
        base_name = (product or {}).get("name_uz") or "product"

        if update.message.photo:
            image_path = _save_photo_to_images(update, base_name)
        elif text == "-":
            image_path = None
        else:
            update.message.reply_text(admin_globals.TEXT_ENTER_NEW_IMAGE[lang_id])
            return True

        db.update_product_image(product_id, image_path)
        logger.info(f"Mahsulot rasmi yangilandi | admin_id={admin_id} | product_id={product_id} | image={image_path or '-'}")
        update.message.reply_text(admin_globals.TEXT_EDIT_SUCCESS[lang_id])
        admin_edit_state.pop(admin_id, None)
        context.bot.send_message(
            chat_id=admin_id,
            text=admin_globals.TEXT_EDIT_MENU[lang_id],
            reply_markup=_build_product_edit_menu(lang_id, product_id),
        )
        return True
    return False
