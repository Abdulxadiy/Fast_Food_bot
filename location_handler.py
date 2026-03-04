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
    logger.info(f"Lokatsiya xabari qabul qilindi | user_id={chat_id}")
    db_user = db.get_user_by_chat_id(chat_id)

    
    if chat_id not in globals.CART or not globals.CART[chat_id]:
        logger.info(f"Lokatsiya rad etildi | sabab=savat_bosh | user_id={chat_id}")
        return # Savat bo'sh bo'lsa
        
    location = update.message.location
    if not location:
        logger.warning(f"Lokatsiya topilmadi | user_id={chat_id}")
        return
        
    latitude = location.latitude
    longitude = location.longitude
    address = get_location_name(latitude, longitude)
    
    # --- (Buyurtmani yig'ish va adminga jo'natish) ---
    payment_type_raw = globals.USER_PAYMENT_TYPE.get(chat_id, "cash")
    payment_type = globals.PAYMENT_TYPES[payment_type_raw][db_user['lang_id']]
    
    order_text = f"🆕 Yangi buyurtma!\n\n"
    order_text += f"👤 Mijoz: {db_user['first_name']} {db_user.get('last_name', '')}\n"
    order_text += f"📞 Tel: {db_user['phone_number']}\n"
    order_text += f"💳 To'lov turi: {payment_type}\n\n"
    order_text += f"🛒 Buyurtmalar:\n"
    
    total_price = 0
    for p_id, amount in globals.CART[chat_id].items():
        product = db.get_product_by_id(p_id)
        name = product[f"name_{globals.LANGUAGE_CODE[db_user['lang_id']]}"]
        price = product['price']
        cost = price * amount
        total_price += cost
        order_text += f"🔸 {amount}x {name} - {cost} so'm\n"
        
    order_text += f"\n💰 Umumiy summa: {total_price} so'm\n"
    order_text += f"\n📍 Manzil: {address if address else 'Nomalum'}"
    
    # Avval bazaga yozib ID ni olamizki, uni inline button callbackiga qo'shaylik
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    order_id = db.create_order(user_id=db_user['id'], payment_type=payment_type_raw, address=address, created_at=created_at)
    logger.info(
        f"Buyurtma yaratildi | order_id={order_id} | user_id={chat_id} | payment_type={payment_type_raw} | manzil={address or 'nomalum'}"
    )
    
    for p_id, amount in globals.CART[chat_id].items():
        db.add_order_product(order_id=order_id, product_id=p_id, amount=amount, created_at=created_at)
        
    admin_buttons = [
        [
            InlineKeyboardButton(text=globals.BTN_ACCEPT_ORDER[1], callback_data=f"admin_accept_{order_id}_{chat_id}_{db_user['lang_id']}"),
            InlineKeyboardButton(text=globals.BTN_REJECT_ORDER[1], callback_data=f"admin_reject_{order_id}_{chat_id}_{db_user['lang_id']}")
        ]
    ]

    # Admin kanaliga buyurtma matni va joylashuvni jo'natish tasdiqlash tugmalari bilan
    try:
        context.bot.send_message(
            chat_id=ADMIN_CHANNEL, 
            text=order_text,
            reply_markup=InlineKeyboardMarkup(admin_buttons)
        )
        context.bot.send_location(chat_id=ADMIN_CHANNEL, latitude=latitude, longitude=longitude)
    except Exception as e:
        logger.error(f"Adminga buyurtma yuborilmadi | order_id={order_id} | xato={e}")

         
    # Savatni tozalash va to'lov turini o'chirish
    globals.CART[chat_id] = {}
    if chat_id in globals.USER_PAYMENT_TYPE:
        del globals.USER_PAYMENT_TYPE[chat_id]
        
    # Foydalanuvchiga xabar berish
    update.message.reply_text(
        text=globals.TEXT_ORDER_CHECKING[db_user['lang_id']],
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Asosiy menyuga o'tkazish
    send_main_menu(context, chat_id, db_user['lang_id'])
    logger.info(f"Buyurtma yakunlandi va menyu yuborildi | order_id={order_id} | user_id={chat_id}")
