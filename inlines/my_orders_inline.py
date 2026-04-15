from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import DATA_BASE
from database import Database
import logging
import globals

db = Database(DATA_BASE)
logger = logging.getLogger("xikmet_food")


def _get_status_text(status, lang_id): 
    """
    Bu funksiya buyurtmaning status kodini o'qiydi va foydalanuvchining tiliga mos ravishda matn ko'rsatadi.
    Funksiya nomidan avval qo'yilgan "_" belgi bu funksiyani faqat shu modul ichida ishlatish uchun mo'ljallanganligini bildiradi.
    Yani bu huddi shu funksiyani boshqa moduldan (.py faylidan) import qilib ishlatish mumkin emas, faqat shu fayl ichida chaqirilishi mumkin deganga o'xshaydi.
    """
    return globals.ORDER_STATUS_TEXT.get(status, {}).get(lang_id, str(status)) # bu joydagi get metodi, agar ORDER_STATUS_TEXT lug'atida status uchun matn topilmasa, default qiymat sifatida status kodini stringga aylantirib qaytaradi.


def _get_payment_text(payment_type, lang_id):
    """
    Bu funksiya to'lov turini o'qiydi va foydalanuvchining tiliga mos ravishda matn ko'rsatadi.
    """
    return globals.PAYMENT_TYPES.get(payment_type, {}).get(lang_id, payment_type)


def my_orders_handler(update, context):
    """
    Bu funksiya foydalanuvchining buyurtmalarini ko'rsatish uchun ishlatiladi. 
    U callback query orqali chaqiriladi va foydalanuvchining chat_id sini olish orqali uning buyurtmalarini 
    bazadan olib, ularni formatlab, foydalanuvchiga ko'rsatadi.
    """
    query = update.callback_query
    chat_id = query.message.chat_id

    db_user = db.get_user_by_chat_id(chat_id) # bazadan foydalanuvchini chat_id orqali olish, bu orqali foydalanuvchining id sini va tilini aniqlash mumkin bo'ladi.
    user_id = db_user["id"]
    lang_id = db_user["lang_id"]

    orders = db.get_orders_by_user(user_id)
    if not orders:
        logger.info(f"Buyurtmalar ro'yxati bo'sh | user_id={chat_id}")
        query.answer(text=globals.ALERT_NO_ORDERS[lang_id], show_alert=True)
        return

    text = globals.TEXT_MY_ORDERS_HEADER[lang_id]

    for i, order in enumerate(orders, start=1):
        """
        bu yerda orders ro'yxatidagi har bir buyurtma uchun, ularni tartib raqami bilan ko'rsatish uchun 
        enumerate funksiyasi ishlatilmoqda. start=1 parametri esa tartib raqamining 1 dan boshlanishini ta'minlaydi.
        """
        order_id = order["id"]
        created_at = order["created_at"]
        status_text = _get_status_text(order["status"], lang_id)
        payment_text = _get_payment_text(order["payment_type"], lang_id)

        text += f"┌ {i}. {globals.TEXT_ORDER_LABEL[lang_id].format(order_id)}\n" # bu yerdagi .format 
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
    """
    Bu funksiya foydalanuvchining buyurtmasi haqida batafsil ma'lumot ko'rsatish uchun ishlatiladi.
    U callback query orqali chaqiriladi va buyurtmaning id sini callback data dan olish orqali, bazadan 
    buyurtma haqida ma'lumot olib, ularni formatlab, foydalanuvchiga ko'rsatadi.
     Bu yerda buyurtmaning id sini callback data dan olish uchun, data_sp o'zgaruvchisi yaratilib, 
     callback data ni "_" belgisiga bo'lib, ro'yxatga aylantiriladi.
    """
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
            text += f"  {amount}x [deleted product #{product_id}] - ? so'm\n"
            continue

        lang_col = f"name_{globals.LANGUAGE_CODE[lang_id]}"
        name = product[lang_col]
        price = product["price"]
        cost = price * amount
        total_price += cost

        text += f"  {amount}x {name} - {cost} so'm\n"

    text += f"\n{'=' * 30}\n"
    text += globals.TEXT_ORDER_TOTAL[lang_id].format(total_price)

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
