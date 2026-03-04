from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from mini_functions import open_photo
from database import Database
from config import DATA_BASE
import logging
import globals
import main_menu

db = Database(DATA_BASE)
logger = logging.getLogger("xikmet_food")

def inline_handler(update, context):
    query = update.callback_query
    logger.info(f"Asosiy inline callback qabul qilindi | data={query.data}")
    data_sp = str(query.data).split("_")
    db_user = db.get_user_by_chat_id(query.message.chat_id)

    if data_sp[0] == "category":
        if data_sp[1] == "back":
            if len(data_sp) == 3:
                parent_id = int(data_sp[2]) # Agar parent_id berilsa, uni int ga o'tkazib olamiz va parent_id ga tenglaymiz.
            else:
                parent_id = None # Agar parent_id berilmagan bolsa, demak eng bosh kategoriyalarni qaytarish kerak, shuning uchun None deb belgilaymiz.

            categories = db.get_categories_by_parent(parent_id=parent_id) # Kategoriyalarni bazadan olamiz.
            buttons = [] # Tugmalar ro'yxati.
            row = [] # Qator tugmalari.
            
            if not categories and parent_id: # Agar maxsulotlar bo'lsa (ya'ni ichki kategoriya bo'lmasa)
                products = db.get_products_by_category(parent_id) # Maxsulotlarni olamiz
                for i in range(len(products)): # Har bir mahsulot aylanadi
                    row.append( # Qatorga tugma qo'shiladi
                        InlineKeyboardButton(
                            text=products[i][f'name_{globals.LANGUAGE_CODE[db_user["lang_id"]]}'], # Mahsulot nomi
                            callback_data=f"product_{products[i]['id']}" # Mahsulot bosilganda yuboriladigan signal
                        )
                    )
                    if len(row) == 2 or (len(products) % 2 == 1 and i == len(products) - 1): # 2 tadan qilib taxlaymiz
                        buttons.append(row)
                        row = []
            else: # Agar kategoriyalar bo'lsa
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

            chat_id = query.message.chat_id # Xozirgi chat ID sini aniqlaymiz.
            if chat_id in globals.CART and globals.CART[chat_id]: # Agar savatda mahsulot bo'lsa
                buttons.append([ # Sotib olish tugmasini ro'yxatga kiritamiz
                    InlineKeyboardButton(
                        text=globals.BTN_BUY[db_user['lang_id']], # Sotib olish yozuvi
                        callback_data="buy" # Sotib olish callback belgisi
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


            if query.message.photo: # Rasm bo'lsa (mahsulotdan qaytilgan)
                query.message.delete() # Avval rasmli xabarni remove(o'chirish) qilamiz
                context.bot.send_message( # Keyin bitta avvalgi knopkalar bilan matn jo'natamiz
                    chat_id=query.message.chat_id,
                    text=globals.TEXT_ORDER[db_user['lang_id']],
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                )
            else: # Agar avval qandaydir rasm bo'lmasa edit qilamiz
                query.message.edit_text(
                    text=globals.TEXT_ORDER[db_user['lang_id']],
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=buttons
                    )
                )

        else:
            categories = db.get_categories_by_parent(parent_id=int(data_sp[1])) # Kategoriyalarni bazadan tekshirish.
            buttons = [] # Buttonlar massivi.
            row = [] # Qatordagi tugmalar massivi.
            
            if not categories: # Agar ichki kategoriyalar bo'lmasa, maxsulotlar chiqishi kerak.
                products = db.get_products_by_category(int(data_sp[1])) # Maxsulotlarni bazadan olamiz.
                for i in range(len(products)): # Tsikl maxsulotlarni aylantiradi.
                    row.append( # Tugmani qatorga joylaymiz.
                        InlineKeyboardButton(
                            text=products[i][f'name_{globals.LANGUAGE_CODE[db_user["lang_id"]]}'], # Maxsulot matni
                            callback_data=f"product_{products[i]['id']}" # Maxsulot callback datasi
                        )
                    )
                    if len(row) == 2 or (len(products) % 2 == 1 and i == len(products) - 1): # Har qatorda 2 ta.
                        buttons.append(row)
                        row = []
            else: # Aks holda kategoriyalarni chiqarish.
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

            chat_id = query.message.chat_id # Chat id olish.
            if chat_id in globals.CART and globals.CART[chat_id]: # Savat bo'shmasligini tekshirish.
                buttons.append([ # Tugma ro'yxatiga Savatga kirish tugmasini qo'shish.
                    InlineKeyboardButton(
                        text=globals.BTN_BUY[db_user['lang_id']], # Sotib olish yozuvi
                        callback_data="buy" # Sotib olish hodisasi signali
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


            if query.message.photo: # Rasm bo'lsa (mahsulotdan qaytilgan)
                query.message.delete() # Avval rasmli xabarni remove(o'chirish) qilamiz
                context.bot.send_message( # Keyin bitta avvalgi knopkalar bilan matn jo'natamiz
                    chat_id=query.message.chat_id,
                    text=globals.TEXT_ORDER[db_user['lang_id']],
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                )
            else: # Agar avval qandaydir rasm bo'lmasa edit qilamiz
                query.message.edit_text(
                    text=globals.TEXT_ORDER[db_user['lang_id']],
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=buttons
                    )
                )

    elif data_sp[0] == "product": # Agar foydalanuvchi ma'lumotni ustiga (mahsulotga) bopsa.
        product_id = int(data_sp[1]) # Mahsulot id raqamini ajratib olamiz.
        product = db.get_product_by_id(product_id) # Bazadan mahsulot haqida malumotni yuklaymiz.
        
        lang_column_name = f"name_{globals.LANGUAGE_CODE[db_user['lang_id']]}" # Tilga mos narx ustuni nomi tugrilanadi
        lang_column_desc = f"description_{globals.LANGUAGE_CODE[db_user['lang_id']]}" # Tilga mos malumot ustun nomi
        
        # Maxsulot haqida matn shakllantiramiz
        text = f"{globals.TEXT_PRODUCT_NAME[db_user['lang_id']]} {product[lang_column_name]}\n" # Nomi
        text += f"{globals.TEXT_PRODUCT_PRICE[db_user['lang_id']]} {product['price']} so'm\n" # Narxi
        text += f"{globals.TEXT_PRODUCT_DESC[db_user['lang_id']]} {product[lang_column_desc]}" # Tarkibi
        
        buttons = [] # 1 dan 9 gacha tugmalarni saqlash ro'yxati.
        row = [] # bitta qator elementlari.
        
        for i in range(1, 10): # 1 dan 9 gacha tsikl
            t = str(i) + "ta"
            row.append( # sonni tugma ko'rinishida qo'shamiz
                InlineKeyboardButton(text=t, callback_data=f"quantity_{product_id}_{i}") # son va callback_data
            )
            if len(row) == 3: # Har bir qatorda 3 ta son bo'lsin.
                buttons.append(row)
                row = []
                
        # Orqaga qaytish tugmasi
        buttons.append([ # mahsulot joylashgan kategoriya sahifasiga qaytaruvchi tugma
            InlineKeyboardButton(text=globals.BTN_BACK[db_user['lang_id']], callback_data=f"category_{product['category']}") 
        ])
        
        # Rasm bilan yoki rasmsiz xabar jo'natish
        query.message.delete() # Eskisini o'chiramiz chunki rasm yuborish kerak bo'lishi mumkin.
        if product['image']: # Rasm mavjud bo'lsa
            context.bot.send_photo( # rasmli jo'natamiz
                chat_id=query.message.chat_id,
                photo=open_photo(product['image']), # fileni ochib jonatamiz
                caption=text, # tegiga matn qoshamiz
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons) # va tugmalar
            )
        else: # Rasm yo'q bo'lsa
            context.bot.send_message( # oddiy matn
                chat_id=query.message.chat_id,
                text=text, # yuqoridagi matn
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons) # knopkalar
            )

    elif data_sp[0] == "quantity": # Foydalanuvchi miqdorni (raqamni) tanlaganda ishga tushadi.
        product_id = int(data_sp[1]) # Mahsulot id
        amount = int(data_sp[2]) # Tanlangan miqdor (1-9)
        chat_id = query.message.chat_id # Chat identifikatori
        
        if chat_id not in globals.CART: # Agar foydalanuvchi avval narsa qoshmagan bolsa
            globals.CART[chat_id] = {} # Bo'sh lug'at ochiq deymiz
            
        globals.CART[chat_id][product_id] = globals.CART[chat_id].get(product_id, 0) + amount # Tanlangan miqdorni avvalgisiga qo'shamiz yoki noldan boplaymiz
        logger.info(
            f"Savatga mahsulot qo'shildi | user_id={chat_id} | product_id={product_id} | miqdor={amount}"
        )
        
        query.answer(text=globals.ALERT_ADDED_TO_CART[db_user['lang_id']], show_alert=True) # Ekranga ogohlantirish chiqaramiz (Savatchaga qoshildi!)
        # show_alert=True      bu ekranga qalqib chiqadigan ogohlantirish oynasini faollashtiradi, agar false bo'lsa pastda kichik bildirishnoma ko'rinishida chiqadi.
        

        query.data = "menu_order" # Eng bosh kategoriyalar ro'yxatini chaqiruvchi maxsus call_back data
        
    elif data_sp[0] == "buy": # Menyudan "Sotib olish" tugmasi bosilganda
        chat_id = query.message.chat_id # Chat id aniqlash
        if chat_id not in globals.CART or not globals.CART[chat_id]: # Savat bush bosla
            query.answer() # Indamasdan qaytib ketamiz (Xato xolati xolos)
            return
            
        text = globals.TEXT_CART_SUMMARY[db_user['lang_id']] # Eng yuqoriga Savatcha: degan yozuv.
        total_price = 0 # Umumiy narx xisoblagich noldan boshlanadi
        
        for p_id, amount in globals.CART[chat_id].items(): # Savatdagi barcha maxsulotarni sanab otamiz
            product = db.get_product_by_id(p_id) # ID orqali bazadan kerakli ma'lumot obkelamiz
            lang_col = f"name_{globals.LANGUAGE_CODE[db_user['lang_id']]}" # O'zgaruvchida ism
            name = product[lang_col] # Maxsulot tilga mos ismi
            price = product['price'] # maxsulot bir doasi narxi
            cost = price * amount # shu maxsulot tiplari umumiy narxi
            total_price += cost # uni butun xarid summasiga qoshib qyamz
            
            text += f"{amount}x {name} - {cost} so'm\n" # Maxsulot soni, nomi va summasi yoziladi (Masalan 2x Lavash - 56000 so'm)
            
        text += globals.TEXT_CART_TOTAL[db_user['lang_id']].format(total_price) # Tagidan Umumiy narxi degan yozuvga sonni formatlaymiz
        
        buttons = [ # Tolov turlari tugmalari
            [InlineKeyboardButton(text=globals.BTN_CARD[db_user['lang_id']], callback_data="payment_card"),
            InlineKeyboardButton(text=globals.BTN_CASH[db_user['lang_id']], callback_data="payment_cash")],
            [InlineKeyboardButton(text=globals.BTN_CLEAR_CART[db_user['lang_id']], callback_data="clear_cart")],
            [InlineKeyboardButton(text=globals.BTN_BACK[db_user['lang_id']], callback_data="menu_order")]
        ]
        
        query.message.edit_text( # Oynani ozgartiramiz yoki rasmni uchirib yangitdan jonatamz
            text=text, # Ruyxat tekst
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons) # Tahrirlangan tugmalar panelı
        )

    elif data_sp[0] == "payment": # To'lov turi tanlanganda
        payment_type = data_sp[1] # "cash" yoki "card"
        chat_id = query.message.chat_id
        
        globals.USER_PAYMENT_TYPE[chat_id] = payment_type # Tanlovni saqlab qo'yamiz
        logger.info(f"To'lov turi tanlandi | user_id={chat_id} | payment_type={payment_type}")
        query.message.delete() # Savat xabarini o'chiramiz

        # Lokatsiya so'rash tugmasi
        btn = [[KeyboardButton(text=globals.BTN_SEND_LOCATION[db_user['lang_id']], request_location=True)]]
        
        context.bot.send_message(
            chat_id=chat_id,
            text=globals.TEXT_SEND_LOCATION[db_user['lang_id']],
            reply_markup=ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True, one_time_keyboard=True)
        )

    elif data_sp[0] == "clear": # Savatni tozalash
        chat_id = query.message.chat_id
        if chat_id in globals.CART:
            if globals.CART[chat_id] == {}:
                query.answer(text=globals.ALERT_CART_ALREADY_EMPTY[db_user['lang_id']], show_alert=True) # Ekranga ogohlantirish chiqaramiz (Savat allaqachon bo'sh!)
                return
            globals.CART[chat_id] = {} # Savatni bo'shatamiz
            logger.info(f"Savat tozalandi | user_id={chat_id}")
        query.answer(text=globals.ALERT_CART_CLEARED[db_user['lang_id']], show_alert=True) # Ekranga ogohlantirish chiqaramiz (Savat tozalandi!)
        query.message.delete() # Xabarni o'chirish
        main_menu.send_main_menu(context, chat_id, db_user['lang_id']) # Eng bosh menyuga qaytamiz
