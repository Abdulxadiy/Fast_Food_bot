from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from mini_functions import open_photo
from database import Database
from config import DATA_BASE
import logging
import globals
import main_menu

db = Database(DATA_BASE)
logger = logging.getLogger("fast_food")

def inline_handler(update, context):
    query = update.callback_query
    logger.info(f"Asosiy inline callback qabul qilindi | data={query.data}")
    data_sp = str(query.data).split("_")
    db_user = db.get_user_by_chat_id(query.message.chat_id)

    if data_sp[0] == "category":
        if data_sp[1] == "back":
            if len(data_sp) == 3:
                parent_id = int(data_sp[2])
            else:
                parent_id = None

            categories = db.get_categories_by_parent(parent_id=parent_id)
            buttons = []
            row = []

            if not categories and parent_id:
                products = db.get_products_by_category(parent_id)
                for i in range(len(products)):
                    row.append(
                        InlineKeyboardButton(
                            text=products[i][f'name_{globals.LANGUAGE_CODE[db_user["lang_id"]]}'],
                            callback_data=f"product_{products[i]['id']}"
                        )
                    )
                    if len(row) == 2 or (len(products) % 2 == 1 and i == len(products) - 1):
                        buttons.append(row)
                        row = []
            else:
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

            chat_id = query.message.chat_id
            if chat_id in globals.CART and globals.CART[chat_id]:
                buttons.append([
                    InlineKeyboardButton(
                        text=globals.BTN_BUY[db_user['lang_id']],
                        callback_data="buy"
                    )
                ])

            if parent_id:
                clicked_btn = db.get_category_parent(parent_id)

                if clicked_btn and clicked_btn['parent']:
                    buttons.append([InlineKeyboardButton(
                        text=globals.BTN_BACK[db_user['lang_id']], callback_data=f"category_back_{clicked_btn['parent']}"
                    )])
                else:
                    buttons.append([InlineKeyboardButton(
                        text=globals.BTN_BACK[db_user['lang_id']], callback_data=f"category_back"
                    )])
            else:
                buttons.append([InlineKeyboardButton(
                    text=globals.BTN_BACK[db_user['lang_id']], callback_data="menu_back"
                )])

            if query.message.photo:
                query.message.delete()
                context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=globals.TEXT_ORDER[db_user['lang_id']],
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                )
            else:
                query.message.edit_text(
                    text=globals.TEXT_ORDER[db_user['lang_id']],
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=buttons
                    )
                )

        else:
            categories = db.get_categories_by_parent(parent_id=int(data_sp[1]))
            buttons = []
            row = []

            if not categories:
                products = db.get_products_by_category(int(data_sp[1]))
                for i in range(len(products)):
                    row.append(
                        InlineKeyboardButton(
                            text=products[i][f'name_{globals.LANGUAGE_CODE[db_user["lang_id"]]}'],
                            callback_data=f"product_{products[i]['id']}"
                        )
                    )
                    if len(row) == 2 or (len(products) % 2 == 1 and i == len(products) - 1):
                        buttons.append(row)
                        row = []
            else:
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

            chat_id = query.message.chat_id
            if chat_id in globals.CART and globals.CART[chat_id]:
                buttons.append([
                    InlineKeyboardButton(
                        text=globals.BTN_BUY[db_user['lang_id']],
                        callback_data="buy"
                    )
                ])

            clicked_btn = db.get_category_parent(int(data_sp[1]))

            if clicked_btn and clicked_btn['parent']:
                buttons.append([InlineKeyboardButton(
                    text=globals.BTN_BACK[db_user['lang_id']], callback_data=f"category_back_{clicked_btn['parent']}"
                )])
            else:
                buttons.append([InlineKeyboardButton(
                    text=globals.BTN_BACK[db_user['lang_id']], callback_data=f"category_back"
                )])

            if query.message.photo:
                query.message.delete()
                context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=globals.TEXT_ORDER[db_user['lang_id']],
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                )
            else:
                query.message.edit_text(
                    text=globals.TEXT_ORDER[db_user['lang_id']],
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=buttons
                    )
                )

    elif data_sp[0] == "product":
        product_id = int(data_sp[1])
        product = db.get_product_by_id(product_id)

        lang_column_name = f"name_{globals.LANGUAGE_CODE[db_user['lang_id']]}"
        lang_column_desc = f"description_{globals.LANGUAGE_CODE[db_user['lang_id']]}"


        text = f"{globals.TEXT_PRODUCT_NAME[db_user['lang_id']]} {product[lang_column_name]}\n"
        text += f"{globals.TEXT_PRODUCT_PRICE[db_user['lang_id']]} {product['price']} {globals.TEXT_CURRENCY[db_user['lang_id']]}\n"
        text += f"{globals.TEXT_PRODUCT_DESC[db_user['lang_id']]} {product[lang_column_desc]}"

        buttons = []
        row = []

        for i in range(1, 10):
            t = globals.BTN_QUANTITY[db_user['lang_id']].format(i)
            row.append(
                InlineKeyboardButton(text=t, callback_data=f"quantity_{product_id}_{i}")
            )
            if len(row) == 3:
                buttons.append(row)
                row = []


        buttons.append([
            InlineKeyboardButton(text=globals.BTN_BACK[db_user['lang_id']], callback_data=f"category_{product['category']}")
        ])


        query.message.delete()
        if product['image']:
            context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=open_photo(product['image']),
                caption=text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
            )
        else:
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
            )

    elif data_sp[0] == "quantity":
        product_id = int(data_sp[1])
        amount = int(data_sp[2])
        chat_id = query.message.chat_id

        if chat_id not in globals.CART:
            globals.CART[chat_id] = {}

        globals.CART[chat_id][product_id] = globals.CART[chat_id].get(product_id, 0) + amount
        logger.info(
            f"Savatga mahsulot qo'shildi | user_id={chat_id} | product_id={product_id} | miqdor={amount}"
        )

        query.answer(text=globals.ALERT_ADDED_TO_CART[db_user['lang_id']], show_alert=True)


        query.data = "menu_order"

    elif data_sp[0] == "buy":
        chat_id = query.message.chat_id
        if chat_id not in globals.CART or not globals.CART[chat_id]:
            query.answer()
            return

        text = globals.TEXT_CART_SUMMARY[db_user['lang_id']]
        total_price = 0

        for p_id, amount in globals.CART[chat_id].items():
            product = db.get_product_by_id(p_id)
            lang_col = f"name_{globals.LANGUAGE_CODE[db_user['lang_id']]}"
            name = product[lang_col]
            price = product['price']
            cost = price * amount
            total_price += cost

            text += globals.TEXT_CART_ITEM[db_user['lang_id']].format(amount, name, cost, globals.TEXT_CURRENCY[db_user['lang_id']]) + "\n"

        text += globals.TEXT_CART_TOTAL[db_user['lang_id']].format(total_price, globals.TEXT_CURRENCY[db_user['lang_id']])

        buttons = [
            [InlineKeyboardButton(text=globals.BTN_CARD[db_user['lang_id']], callback_data="payment_card"),
            InlineKeyboardButton(text=globals.BTN_CASH[db_user['lang_id']], callback_data="payment_cash")],
            [InlineKeyboardButton(text=globals.BTN_CLEAR_CART[db_user['lang_id']], callback_data="clear_cart")],
            [InlineKeyboardButton(text=globals.BTN_BACK[db_user['lang_id']], callback_data="menu_order")]
        ]

        query.message.edit_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )

    elif data_sp[0] == "payment":
        payment_type = data_sp[1]
        chat_id = query.message.chat_id

        globals.USER_PAYMENT_TYPE[chat_id] = payment_type
        logger.info(f"To'lov turi tanlandi | user_id={chat_id} | payment_type={payment_type}")
        query.message.delete()


        btn = [[KeyboardButton(text=globals.BTN_SEND_LOCATION[db_user['lang_id']], request_location=True)]]

        context.bot.send_message(
            chat_id=chat_id,
            text=globals.TEXT_SEND_LOCATION[db_user['lang_id']],
            reply_markup=ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True, one_time_keyboard=True)
        )

    elif data_sp[0] == "clear":
        chat_id = query.message.chat_id
        if chat_id in globals.CART:
            if globals.CART[chat_id] == {}:
                query.answer(text=globals.ALERT_CART_ALREADY_EMPTY[db_user['lang_id']], show_alert=True)
                return
            globals.CART[chat_id] = {}
            logger.info(f"Savat tozalandi | user_id={chat_id}")
        query.answer(text=globals.ALERT_CART_CLEARED[db_user['lang_id']], show_alert=True)
        query.message.delete()
        main_menu.send_main_menu(context, chat_id, db_user['lang_id'])
