import sqlite3

class Database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cur = self.conn.cursor()

        self.cur.execute("PRAGMA foreign_keys = ON")
        self.conn.commit()
        self._ensure_suggestions_columns()
        self._ensure_multilang_columns()

    def _ensure_suggestions_columns(self):

        self.cur.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='suggestions'
            """
        )
        if not self.cur.fetchone():
            return

        self.cur.execute("""PRAGMA table_info(suggestions)""")
        columns = {row[1] for row in self.cur.fetchall()}

        if "read_at" not in columns:
            self.cur.execute("""ALTER TABLE suggestions ADD COLUMN read_at TEXT""")
        if "admin_reply" not in columns:
            self.cur.execute("""ALTER TABLE suggestions ADD COLUMN admin_reply TEXT""")
        if "replied_at" not in columns:
            self.cur.execute("""ALTER TABLE suggestions ADD COLUMN replied_at TEXT""")
        if "admin_id" not in columns:
            self.cur.execute("""ALTER TABLE suggestions ADD COLUMN admin_id INTEGER""")
        self.conn.commit()

    def _ensure_multilang_columns(self):
        self._ensure_table_columns(
            "category",
            {
                "name_en": "TEXT",
            },
        )
        self._ensure_table_columns(
            "product",
            {
                "name_en": "TEXT",
                "description_en": "TEXT",
            },
        )

    def _ensure_table_columns(self, table_name, columns_to_add):
        self.cur.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
            """,
            (table_name,),
        )
        if not self.cur.fetchone():
            return

        self.cur.execute(f"""PRAGMA table_info({table_name})""")
        existing_columns = {row[1] for row in self.cur.fetchall()}

        for column_name, column_type in columns_to_add.items():
            if column_name not in existing_columns:
                self.cur.execute(
                    f"""ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"""
                )

        if table_name == "category" and "name_en" in columns_to_add:
            self.cur.execute(
                """
                UPDATE category
                SET name_en = COALESCE(NULLIF(name_en, ''), name_ru, name_uz)
                WHERE name_en IS NULL OR name_en = ''
                """
            )

        if table_name == "product":
            if "name_en" in columns_to_add:
                self.cur.execute(
                    """
                    UPDATE product
                    SET name_en = COALESCE(NULLIF(name_en, ''), name_ru, name_uz)
                    WHERE name_en IS NULL OR name_en = ''
                    """
                )
            if "description_en" in columns_to_add:
                self.cur.execute(
                    """
                    UPDATE product
                    SET description_en = COALESCE(NULLIF(description_en, ''), description_ru, description_uz)
                    WHERE description_en IS NULL OR description_en = ''
                    """
                )

        self.conn.commit()

    def create_user(self, chat_id):
        self.cur.execute("""insert into users(chat_id) values (?)""", (chat_id,))
        self.conn.commit()

    def update_user_data(self, chat_id, key, value):
        self.cur.execute(f"""update users set {key} = ? where chat_id = ?""", (value, chat_id))
        self.conn.commit()

    def get_user_by_chat_id(self, chat_id):
        self.cur.execute("""select * from users where chat_id = ?""", (chat_id, ))
        user = dict_fetchone(self.cur)
        return user

    def get_categories_by_parent(self, parent_id=None):
        if parent_id:
            self.cur.execute("""select * from category where parent = ?""", (parent_id, ))
        else:
            self.cur.execute("""select * from category where parent is NULL""")

        categories = dict_fetchall(self.cur)
        return categories

    def get_category_parent(self, category_id):
        self.cur.execute("""select parent from category where id = ?""", (category_id, ))
        category = dict_fetchone(self.cur)
        return category

    def get_category_by_id(self, category_id):
        self.cur.execute("""SELECT * FROM category WHERE id = ?""", (category_id,))
        return dict_fetchone(self.cur)

    def get_products_by_category(self, category_id):
        self.cur.execute(
            """SELECT * FROM product WHERE category = ? AND COALESCE(status_stop, 0) = 0""",
            (category_id,),
        )
        products = dict_fetchall(self.cur)
        return products

    def get_product_by_id(self, product_id):
        self.cur.execute("""select * from product where id = ?""", (product_id, ))
        product = dict_fetchone(self.cur)
        return product

    def create_order(self, user_id, payment_type, address, created_at):
        self.cur.execute("""INSERT INTO "order" (user, payment_type, address, created_at) VALUES (?, ?, ?, ?)""", (user_id, payment_type, address, created_at))
        self.conn.commit()
        return self.cur.lastrowid

    def add_order_product(self, order_id, product_id, amount, created_at):
        self.cur.execute("""INSERT INTO order_product ("order", product, amount, created_at) VALUES (?, ?, ?, ?)""", (order_id, product_id, amount, created_at))
        self.conn.commit()

    def update_order_status(self, order_id, status):

        self.cur.execute("""UPDATE "order" SET status = ? WHERE id = ?""", (status, order_id))
        self.conn.commit()

    def get_orders_by_user(self, user_id):
        self.cur.execute("""SELECT * FROM "order" WHERE user = ?""", (user_id, ))
        orders = dict_fetchall(self.cur)
        return orders

    def get_product_sales_statistics(self, days=None):
        date_filter = ""
        params = []
        if days is not None:
            date_filter = " AND datetime(o.created_at) >= datetime('now', ?)"
            params.append(f"-{int(days)} day")

        self.cur.execute(
            f"""
            SELECT
                op.product AS product_id,
                p.name_uz,
                p.name_ru,
                p.name_en,
                SUM(op.amount) AS sold_count
            FROM order_product op
            JOIN "order" o ON o.id = op."order"
            LEFT JOIN product p ON p.id = op.product
            WHERE o.status = 1 {date_filter}
            GROUP BY op.product, p.name_uz, p.name_ru, p.name_en
            ORDER BY sold_count DESC, op.product ASC
            """,
            tuple(params),
        )
        return dict_fetchall(self.cur)

    def create_suggestion(self, user_id, message, status=0, created_at=None):

        self.cur.execute(
            """
            INSERT INTO suggestions (user, message, status, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, message, status, created_at),
        )
        self.conn.commit()
        return self.cur.lastrowid

    def get_suggestion_by_id(self, suggestion_id):

        self.cur.execute("""SELECT * FROM suggestions WHERE id = ?""", (suggestion_id,))
        return dict_fetchone(self.cur)

    def get_user_by_id(self, user_id):

        self.cur.execute("""SELECT * FROM users WHERE id = ?""", (user_id,))
        return dict_fetchone(self.cur)

    def update_suggestion_status(self, suggestion_id, status, read_at=None, admin_id=None):

        self.cur.execute(
            """
            UPDATE suggestions
            SET status = ?, read_at = COALESCE(?, read_at), admin_id = COALESCE(?, admin_id)
            WHERE id = ?
            """,
            (status, read_at, admin_id, suggestion_id),
        )
        self.conn.commit()

    def save_suggestion_reply(self, suggestion_id, admin_id, reply_text, replied_at, status=1, read_at=None):

        self.cur.execute(
            """
            UPDATE suggestions
            SET admin_reply = ?, replied_at = ?, admin_id = ?, status = ?, read_at = COALESCE(?, read_at)
            WHERE id = ?
            """,
            (reply_text, replied_at, admin_id, status, read_at, suggestion_id),
        )
        self.conn.commit()

    def get_all_categories(self):
        self.cur.execute("""SELECT id, name_uz, name_ru, name_en, parent FROM category ORDER BY id""")
        return dict_fetchall(self.cur)

    def create_product(
        self,
        name_uz,
        name_ru,
        name_en,
        category_id,
        price,
        description_uz,
        description_ru,
        description_en,
        image=None,
    ):
        self.cur.execute(
            """
            INSERT INTO product (
                name_uz,
                name_ru,
                name_en,
                category,
                price,
                status_stop,
                description_uz,
                description_ru,
                description_en,
                image
            )
            VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
            """,
            (
                name_uz,
                name_ru,
                name_en,
                category_id,
                price,
                description_uz,
                description_ru,
                description_en,
                image,
            ),
        )
        self.conn.commit()
        return self.cur.lastrowid

    def get_all_products(self):
        self.cur.execute("""SELECT * FROM product ORDER BY id DESC""")
        return dict_fetchall(self.cur)

    def update_product_names(self, product_id, name_uz, name_ru, name_en):
        self.cur.execute(
            """UPDATE product SET name_uz = ?, name_ru = ?, name_en = ? WHERE id = ?""",
            (name_uz, name_ru, name_en, product_id),
        )
        self.conn.commit()

    def update_product_price(self, product_id, price):
        self.cur.execute(
            """UPDATE product SET price = ? WHERE id = ?""",
            (price, product_id),
        )
        self.conn.commit()

    def update_product_descriptions(self, product_id, description_uz, description_ru, description_en):
        self.cur.execute(
            """UPDATE product SET description_uz = ?, description_ru = ?, description_en = ? WHERE id = ?""",
            (description_uz, description_ru, description_en, product_id),
        )
        self.conn.commit()

    def update_product_image(self, product_id, image_path):
        self.cur.execute(
            """UPDATE product SET image = ? WHERE id = ?""",
            (image_path, product_id),
        )
        self.conn.commit()

    def update_product_stop_status(self, product_id, status_stop):
        self.cur.execute(
            """UPDATE product SET status_stop = ? WHERE id = ?""",
            (status_stop, product_id),
        )
        self.conn.commit()

    def get_product_order_usage_count(self, product_id):
        self.cur.execute(
            """SELECT COUNT(*) AS cnt FROM order_product WHERE product = ?""",
            (product_id,),
        )
        row = self.cur.fetchone()
        return row[0] if row else 0

    def delete_product(self, product_id):


        self.conn.commit()
        self.cur.execute("PRAGMA foreign_keys = OFF")
        try:
            self.cur.execute("""DELETE FROM product WHERE id = ?""", (product_id,))
            self.conn.commit()
        finally:
            self.cur.execute("PRAGMA foreign_keys = ON")
            self.conn.commit()

    def get_category_descendant_ids(self, category_id):
        self.cur.execute(
            """
            WITH RECURSIVE cat_tree(id) AS (
                SELECT id FROM category WHERE id = ?
                UNION ALL
                SELECT c.id
                FROM category c
                JOIN cat_tree ct ON c.parent = ct.id
            )
            SELECT id FROM cat_tree
            """,
            (category_id,),
        )
        return [row[0] for row in self.cur.fetchall()]

    def delete_category_cascade(self, category_id):
        category_ids = self.get_category_descendant_ids(category_id)
        if not category_ids:
            return 0, 0

        ph = ",".join(["?"] * len(category_ids))

        self.cur.execute(
            f"""SELECT id FROM product WHERE category IN ({ph})""",
            tuple(category_ids),
        )
        product_ids = [row[0] for row in self.cur.fetchall()]

        self.conn.commit()
        self.cur.execute("PRAGMA foreign_keys = OFF")
        try:
            if product_ids:
                pp = ",".join(["?"] * len(product_ids))
                self.cur.execute(
                    f"""DELETE FROM product WHERE id IN ({pp})""",
                    tuple(product_ids),
                )


            for cid in sorted(category_ids, reverse=True):
                self.cur.execute("""DELETE FROM category WHERE id = ?""", (cid,))

            self.conn.commit()
        finally:
            self.cur.execute("PRAGMA foreign_keys = ON")
            self.conn.commit()

        return len(category_ids), len(product_ids)

    def get_root_categories(self):
        self.cur.execute("""SELECT * FROM category WHERE parent IS NULL ORDER BY id""")
        return dict_fetchall(self.cur)

    def create_category(self, name_uz, name_ru, name_en, parent=None):
        self.cur.execute(
            """INSERT INTO category (name_uz, name_ru, name_en, parent) VALUES (?, ?, ?, ?)""",
            (name_uz, name_ru, name_en, parent)
        )
        self.conn.commit()
        return self.cur.lastrowid

def dict_fetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def dict_fetchone(cursor):
    row = cursor.fetchone()
    if row is None:
        return False
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))
