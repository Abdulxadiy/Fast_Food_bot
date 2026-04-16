from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from mini_functions import get_location_name
from database import Database
from config import DATA_BASE, ADMIN_CHANNEL
from datetime import datetime
from main_menu import send_main_menu
import logging
import globals

db = Database(DATA_BASE)
logger = logging.getLogger("xikmet_food")

def location_handler(update: Update, context):
    user = update.message.from_user
    chat_id = user.id
    db_user = db.get_user_by_chat_id(chat_id)


    if chat_id not in globals.CART or not globals.CART[chat_id]:
        return

    location = update.message.location
    if not location:
        logger.warning(f"Lokatsiya topilmadi | user_id={chat_id}")
        return

    latitude = location.latitude
    longitude = location.longitude
    address = get_location_name(latitude, longitude)


    payment_type_raw = globals.USER_PAYMENT_TYPE.get(chat_id, "cash")
    payment_type = globals.PAYMENT_TYPES[payment_type_raw][db_user['lang_id']]

    order_text = f"{globals.TEXT_ADMIN_ORDER_NEW[db_user['lang_id']]}\n\n"
    order_text += f"{globals.TEXT_ADMIN_ORDER_CUSTOMER[db_user['lang_id']]}: {db_user['first_name']} {db_user.get('last_name', '')}\n"
    order_text += f"{globals.TEXT_ADMIN_ORDER_PHONE[db_user['lang_id']]}: {db_user['phone_number']}\n"
    order_text += f"{globals.TEXT_ADMIN_ORDER_PAYMENT[db_user['lang_id']]}: {payment_type}\n\n"
    order_text += f"{globals.TEXT_ADMIN_ORDER_ITEMS[db_user['lang_id']]}\n"

    total_price = 0
    for p_id, amount in globals.CART[chat_id].items():
        product = db.get_product_by_id(p_id)
        name = product[f"name_{globals.LANGUAGE_CODE[db_user['lang_id']]}"]
        price = product['price']
        cost = price * amount
        total_price += cost
        order_text += f"🔸 {amount}x {name} - {cost} {globals.TEXT_CURRENCY[db_user['lang_id']]}\n"

    order_text += f"\n{globals.TEXT_ADMIN_ORDER_TOTAL[db_user['lang_id']].format(total_price, globals.TEXT_CURRENCY[db_user['lang_id']])}\n"
    order_text += (
        f"\n{globals.TEXT_ADMIN_ORDER_ADDRESS[db_user['lang_id']]}: "
        f"{address if address else globals.TEXT_ADMIN_ORDER_UNKNOWN_ADDRESS[db_user['lang_id']]}"
    )


    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    order_id = db.create_order(user_id=db_user['id'], payment_type=payment_type_raw, address=address, created_at=created_at)
    logger.info(
        f"Buyurtma yaratildi | order_id={order_id} | user_id={chat_id} | payment_type={payment_type_raw} | manzil={address or 'nomalum'}"
    )

    for p_id, amount in globals.CART[chat_id].items():
        db.add_order_product(order_id=order_id, product_id=p_id, amount=amount, created_at=created_at)

    admin_buttons = [
        [
            InlineKeyboardButton(text=globals.BTN_ACCEPT_ORDER[db_user['lang_id']], callback_data=f"admin_accept_{order_id}_{chat_id}_{db_user['lang_id']}"),
            InlineKeyboardButton(text=globals.BTN_REJECT_ORDER[db_user['lang_id']], callback_data=f"admin_reject_{order_id}_{chat_id}_{db_user['lang_id']}")
        ]
    ]


    try:
        context.bot.send_message(
            chat_id=ADMIN_CHANNEL,
            text=order_text,
            reply_markup=InlineKeyboardMarkup(admin_buttons)
        )
        context.bot.send_location(chat_id=ADMIN_CHANNEL, latitude=latitude, longitude=longitude)
    except Exception as e:
        logger.error(f"Adminga buyurtma yuborilmadi | order_id={order_id} | xato={e}")


    globals.CART[chat_id] = {}
    if chat_id in globals.USER_PAYMENT_TYPE:
        del globals.USER_PAYMENT_TYPE[chat_id]


    update.message.reply_text(
        text=globals.TEXT_ORDER_CHECKING[db_user['lang_id']],
        reply_markup=ReplyKeyboardRemove()
    )


    send_main_menu(context, chat_id, db_user['lang_id'])
