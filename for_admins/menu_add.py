from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import DATA_BASE, OWNER
from database import Database
from for_admins import admin_globals
from for_admins.owner_menu import admin_menu
import logging
import os
import re

db = Database(DATA_BASE)
logger = logging.getLogger("xikmet_food")
admin_cat_state = {}


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


def _build_category_markup(lang_id, parent_id=None):
    categories = db.get_categories_by_parent(parent_id=parent_id)
    buttons = []
    name_col = "name_uz" if lang_id == 1 else "name_ru"

    for category in categories:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=category[name_col],
                    callback_data=f"adm_open_{category['id']}" if parent_id is None else "adm_noop",
                )
            ]
        )

    if parent_id is None:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=admin_globals.BTN_ADD_PARENT_CATEGORY[lang_id],
                    callback_data="adm_cat_add_root",
                )
            ]
        )
        buttons.append(
            [InlineKeyboardButton(text=admin_globals.BTN_BACK[lang_id], callback_data="adm_back")]
        )
    else:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=admin_globals.BTN_ADD_CHILD_CATEGORY[lang_id],
                    callback_data=f"adm_cat_add_child_{parent_id}",
                )
            ]
        )
        buttons.append(
            [InlineKeyboardButton(text=admin_globals.BTN_BACK[lang_id], callback_data="adm_root_back")]
        )

    return InlineKeyboardMarkup(buttons)


def menu_add_handler(update, context):
    query = update.callback_query
    data_sp = query.data.split("_")
    admin_id = query.from_user.id
    db_user = db.get_user_by_chat_id(admin_id)
    lang_id = db_user["lang_id"]

    if admin_id != OWNER:
        logger.warning(f"Ruxsatsiz admin qo'shish bo'limiga kirdi | admin_id={admin_id}")
        query.answer(admin_globals.TEXT_ONLY_OWNER[lang_id], show_alert=True)
        return

    query.answer()
    if len(data_sp) < 2:
        return

    if data_sp[1] == "add":
        logger.info(f"Mahsulot qo'shish menyusi ochildi | admin_id={admin_id}")
        query.message.edit_text(
            text=admin_globals.TEXT_PICK_OR_CREATE_ROOT[lang_id],
            reply_markup=_build_category_markup(lang_id, parent_id=None),
        )
        return

    if data_sp[1] == "back":
        admin_menu(context, admin_id, lang_id, query.message.message_id)
        return

    if data_sp[1] == "root" and len(data_sp) >= 3 and data_sp[2] == "back":
        query.message.edit_text(
            text=admin_globals.TEXT_PICK_OR_CREATE_ROOT[lang_id],
            reply_markup=_build_category_markup(lang_id, parent_id=None),
        )
        return

    if data_sp[1] == "open" and len(data_sp) >= 3:
        parent_id = int(data_sp[2])
        query.message.edit_text(
            text=admin_globals.TEXT_PICK_OR_CREATE_ROOT[lang_id],
            reply_markup=_build_category_markup(lang_id, parent_id=parent_id),
        )
        return

    if data_sp[1] == "noop":
        return

    if data_sp[1] == "cat" and len(data_sp) >= 4 and data_sp[2] == "add" and data_sp[3] == "root":
        admin_cat_state[admin_id] = {"step": "cat_name_uz", "data": {"parent": None}}
        logger.info(f"Ota kategoriya yaratish boshlandi | admin_id={admin_id}")
        context.bot.send_message(chat_id=admin_id, text=admin_globals.TEXT_ENTER_ROOT_UZ[lang_id])
        return

    if data_sp[1] == "cat" and len(data_sp) >= 5 and data_sp[2] == "add" and data_sp[3] == "child":
        parent_id = int(data_sp[4])
        admin_cat_state[admin_id] = {
            "step": "child_cat_name_uz",
            "data": {"parent": parent_id},
        }
        logger.info(f"Ichki kategoriya yaratish boshlandi | admin_id={admin_id} | parent_id={parent_id}")
        context.bot.send_message(chat_id=admin_id, text=admin_globals.TEXT_ENTER_CHILD_CATEGORY_UZ[lang_id])
        return


def handle_admin_category_text(update, context):
    if update.message is None:
        return False

    admin_id = update.message.from_user.id
    db_user = db.get_user_by_chat_id(admin_id)
    lang_id = db_user["lang_id"]
    state = admin_cat_state.get(admin_id)
    if not state:
        return False

    text = (update.message.text or "").strip()
    step = state["step"]
    data = state["data"]

    if step != "product_image" and not text:
        update.message.reply_text(admin_globals.TEXT_EMPTY_TEXT[lang_id])
        return True

    if step == "cat_name_uz":
        data["name_uz"] = text
        state["step"] = "cat_name_ru"
        update.message.reply_text(admin_globals.TEXT_ENTER_ROOT_RU[lang_id])
        return True

    if step == "cat_name_ru":
        data["name_ru"] = text
        new_cat_id = db.create_category(
            name_uz=data["name_uz"],
            name_ru=data["name_ru"],
            parent=data["parent"],
        )
        update.message.reply_text(admin_globals.TEXT_CATEGORY_SAVED[lang_id].format(new_cat_id))
        admin_cat_state.pop(admin_id, None)
        logger.info(f"Ota kategoriya qo'shildi | admin_id={admin_id} | category_id={new_cat_id}")
        admin_menu(context, admin_id, lang_id)
        return True

    if step == "child_cat_name_uz":
        data["cat_name_uz"] = text
        state["step"] = "child_cat_name_ru"
        update.message.reply_text(admin_globals.TEXT_ENTER_CHILD_CATEGORY_RU[lang_id])
        return True

    if step == "child_cat_name_ru":
        data["cat_name_ru"] = text
        state["step"] = "product_price"
        update.message.reply_text(admin_globals.TEXT_ENTER_PRODUCT_PRICE[lang_id])
        return True

    if step == "product_price":
        if not text.isdigit():
            update.message.reply_text(admin_globals.TEXT_INVALID_PRICE[lang_id])
            return True
        data["product_price"] = int(text)
        state["step"] = "product_desc_uz"
        update.message.reply_text(admin_globals.TEXT_ENTER_PRODUCT_DESC_UZ[lang_id])
        return True

    if step == "product_desc_uz":
        data["product_desc_uz"] = text
        state["step"] = "product_desc_ru"
        update.message.reply_text(admin_globals.TEXT_ENTER_PRODUCT_DESC_RU[lang_id])
        return True

    if step == "product_desc_ru":
        data["product_desc_ru"] = text
        state["step"] = "product_image"
        update.message.reply_text(admin_globals.TEXT_ENTER_PRODUCT_IMAGE[lang_id])
        return True

    if step == "product_image":
        if update.message.photo:
            image_path = _save_photo_to_images(update, data["cat_name_uz"])
        elif text == "-":
            image_path = None
        else:
            update.message.reply_text(admin_globals.TEXT_ENTER_PRODUCT_IMAGE[lang_id])
            return True

        parent_id = data["parent"]
        new_cat_id = db.create_category(
            name_uz=data["cat_name_uz"],
            name_ru=data["cat_name_ru"],
            parent=parent_id,
        )

        new_product_id = db.create_product(
            name_uz=data["cat_name_uz"],
            name_ru=data["cat_name_ru"],
            category_id=new_cat_id,
            price=data["product_price"],
            description_uz=data["product_desc_uz"],
            description_ru=data["product_desc_ru"],
            image=image_path,
        )

        update.message.reply_text(
            admin_globals.TEXT_CATEGORY_AND_PRODUCT_SAVED[lang_id].format(new_cat_id, new_product_id)
        )
        admin_cat_state.pop(admin_id, None)
        logger.info(
            f"Ichki kategoriya va mahsulot qo'shildi | admin_id={admin_id} | parent_id={parent_id} "
            f"| category_id={new_cat_id} | product_id={new_product_id}"
        )
        admin_menu(context, admin_id, lang_id)
        return True

    return False
