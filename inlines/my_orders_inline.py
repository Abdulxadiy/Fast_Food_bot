from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import DATA_BASE
from database import Database
import logging
import globals

db = Database(DATA_BASE)
logger = logging.getLogger("xikmet_food")

def _get_status_text(status, lang_id):


    return globals.ORDER_STATUS_TEXT.get(status, {}).get(lang_id, str(status))

def _get_payment_text(payment_type, lang_id):


    return globals.PAYMENT_TYPES.get(payment_type, {}).get(lang_id, payment_type)

def my_orders_handler(update, context):


    query = update.callback_query
    chat_id = query.message.chat_id

    db_user = db.get_user_by_chat_id(chat_id)
    user_id = db_user["id"]
    lang_id = db_user["lang_id"]

    orders = db.get_orders_by_user(user_id)
    if not orders:
        logger.info(f"Buyurtmalar ro'yxati bo'sh | user_id={chat_id}")
        query.answer(text=globals.ALERT_NO_ORDERS[lang_id], show_alert=True)
        return

    text = globals.TEXT_MY_ORDERS_HEADER[lang_id]

    for i, order in enumerate(orders, start=1):


        order_id = order["id"]
        created_at = order["created_at"]
        status_text = _get_status_text(order["status"], lang_id)
        payment_text = _get_payment_text(order["payment_type"], lang_id)

        text += f"┌ {i}. {globals.TEXT_ORDER_LABEL[lang_id].format(order_id)}\n"
        text += f"├ {globals.TEXT_ORDER_TIME[lang_id].format(created_at)}\n"
        text += f"├ {status_text}\n"
        text += f"└ {payment_text}\n\n"

    buttons = [[
        InlineKeyboardButton(
            text=globals.BTN_BACK[lang_id],
            callback_data="menu_back",
        )
    ]]

    query.message.edit_text(
        text=text.strip(),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    logger.info(f"Buyurtmalar ro'yxati ko'rsatildi | user_id={chat_id} | soni={len(orders)}")

def order_detail_handler(update, context):


    query = update.callback_query
    data_sp = query.data.split("_")
    order_id = int(data_sp[1])
    chat_id = query.message.chat_id

    db_user = db.get_user_by_chat_id(chat_id)
    lang_id = db_user["lang_id"]

    db.cur.execute("""SELECT * FROM "order" WHERE id = ?""", (order_id,))
    order_row = db.cur.fetchone()
    if not order_row:
        logger.warning(f"Buyurtma topilmadi | user_id={chat_id} | order_id={order_id}")
        query.answer(text=globals.ALERT_ORDER_NOT_FOUND[lang_id], show_alert=True)
        return

    db.cur.execute("""SELECT * FROM order_product WHERE "order" = ?""", (order_id,))
    order_products = db.cur.fetchall()

    payment_text = _get_payment_text(order_row[2], lang_id)
    status_text = _get_status_text(order_row[3], lang_id)
    created_at = order_row[4]

    text = f"{globals.TEXT_ORDER_LABEL[lang_id].format(order_id)}\n"
    text += f"{globals.TEXT_ORDER_TIME[lang_id].format(created_at)}\n"
    text += f"{status_text}\n"
    text += f"{payment_text}\n\n"
    text += globals.TEXT_ORDER_PRODUCTS[lang_id]

    total_price = 0
    for product_data in order_products:
        product_id = product_data[2]
        amount = product_data[3]

        product = db.get_product_by_id(product_id)
        if not product:
            text += f"  {amount}x {globals.TEXT_DELETED_PRODUCT[lang_id].format(product_id)} - ? {globals.TEXT_CURRENCY[lang_id]}\n"
            continue

        lang_col = f"name_{globals.LANGUAGE_CODE[lang_id]}"
        name = product[lang_col]
        price = product["price"]
        cost = price * amount
        total_price += cost

        text += f"  {amount}x {name} - {cost} {globals.TEXT_CURRENCY[lang_id]}\n"

    text += f"\n{'=' * 30}\n"
    text += globals.TEXT_ORDER_TOTAL[lang_id].format(total_price, globals.TEXT_CURRENCY[lang_id])

    buttons = [[
        InlineKeyboardButton(
            text=globals.BTN_BACK[lang_id],
            callback_data="menu_myorders",
        )
    ]]

    query.message.edit_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    logger.info(f"Buyurtma detali ko'rsatildi | user_id={chat_id} | order_id={order_id}")
