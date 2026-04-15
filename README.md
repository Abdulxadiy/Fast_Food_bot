# Xikmet Food Telegram Bot

<p align="center">
  A bilingual Telegram bot for fast-food ordering, delivery coordination, customer feedback, and owner-side product management.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Telegram-Bot%20API-26A5E4?style=for-the-badge&logo=telegram" alt="Telegram Bot API">
  <img src="https://img.shields.io/badge/Database-SQLite-07405E?style=for-the-badge&logo=sqlite" alt="SQLite">
  <img src="https://img.shields.io/badge/Languages-Uzbek%20%7C%20Russian-success?style=for-the-badge" alt="Languages">
</p>

## Overview

**Xikmet Food** is a Telegram-based food ordering system built for a fast-food business. It allows customers to browse categories, select products, place orders, share delivery locations, track previous orders, and send feedback directly from Telegram.

The project also includes an **owner-only admin workflow** for managing the catalog, moderating incoming orders, reviewing customer comments, and viewing sales statistics.

## What This Bot Can Do

### Customer features

- Register users with first name, last name, phone number, and preferred language.
- Support **Uzbek** and **Russian** interfaces.
- Browse a hierarchical product catalog through inline keyboards.
- View product details, price, description, and optional product image.
- Add products to a cart with quantity selection.
- Choose a payment method: **cash** or **card**.
- Send live location for delivery.
- Store orders in SQLite and show order history to the customer.
- Let users update profile settings: language, first name, last name, and phone number.
- Let users send comments or suggestions to the business.
- Notify users when their comment is read or replied to by an admin.

### Admin / owner features

- Receive new orders in a dedicated Telegram channel.
- Accept or reject orders directly from inline action buttons.
- Send a rejection reason back to the customer.
- Manage the catalog from Telegram without touching the database manually.
- Add parent categories and child categories.
- Add products with bilingual names, descriptions, prices, and optional images.
- Edit product names, prices, descriptions, and images.
- Temporarily remove products from sale and return them later.
- Delete products.
- Delete categories with recursive child-category and product cleanup.
- Receive customer feedback in a separate comments channel.
- Mark comments as read and reply to users from Telegram.
- View product sales statistics for the last 30 days or for all time.

## Tech Stack

| Area | Technology |
|---|---|
| Main language | Python |
| Bot framework | `python-telegram-bot` |
| Database | SQLite |
| Geolocation reverse lookup | `geopy` with Nominatim |
| Logging | Python `logging` + `RotatingFileHandler` |
| Interaction style | Telegram polling |

## Supported Languages

This project works in two user-facing languages:

- Uzbek
- Russian

Programming language used in the codebase:

- Python

## Project Structure

```text
Xikmet_Food/
├── main.py                    # Bot entry point
├── register.py                # Registration flow
├── queries.py                 # Callback router
├── location_handler.py        # Delivery location and order creation
├── database.py                # SQLite access layer
├── globals.py                 # Shared texts and runtime state
├── main_menu.py               # Main menu builder
├── mini_functions.py          # Helpers
├── inlines/                   # Customer-side inline handlers
├── for_admins/                # Admin/owner handlers
├── texts/                     # Static text content and logs
├── db_design/                 # Database design reference
├── xikmet_food.db             # SQLite database
└── config.py                  # Local configuration
```

## Order Flow

1. User starts the bot and selects a language.
2. User completes registration.
3. User browses menu categories and products.
4. User adds items to the cart.
5. User selects a payment type.
6. User sends location for delivery.
7. Order is saved to SQLite.
8. Order is forwarded to the admin channel.
9. Admin accepts or rejects the order.
10. User receives the final status in Telegram.

## Database Design

The current SQLite database includes these main tables:

- `users`
- `category`
- `product`
- `order`
- `order_product`
- `suggestions`

These tables cover:

- user registration data
- multilingual catalog structure
- products and pricing
- customer orders and ordered items
- customer suggestions/comments and admin replies

## Configuration

The bot expects a local `config.py` file with values similar to this:

```python
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
DATA_BASE = "xikmet_food.db"
OWNER = 123456789
ADMIN_CHANNEL = -1001234567890
COMMENTS_CHANNEL = -1001234567890
```

### Config fields

- `TOKEN`: Telegram bot token from BotFather.
- `DATA_BASE`: SQLite database file path.
- `OWNER`: Telegram user ID of the project owner/admin.
- `ADMIN_CHANNEL`: channel or group where incoming orders are sent.
- `COMMENTS_CHANNEL`: channel or group where customer comments are sent.

Important:

- Do not commit real tokens or private IDs to GitHub.
- Replace all placeholder values before running the bot.

## Installation

```bash
git clone <your-repository-url>
cd Xikmet_Food
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If your environment has issues reading `requirements.txt`, recreate it in standard UTF-8 format before installation.

## Run

```bash
python main.py
```

The bot starts in **polling mode**.

## Main Functional Modules

| File | Responsibility |
|---|---|
| `main.py` | Starts the bot, registers handlers, enables logging |
| `register.py` | Registration and language selection |
| `queries.py` | Routes all callback queries |
| `inlines/main_inlines.py` | Menu browsing, product viewing, cart flow, payment choice |
| `location_handler.py` | Finalizes order after location is sent |
| `inlines/my_orders_inline.py` | Displays previous orders |
| `inlines/setting_inline.py` | User settings management |
| `inlines/comments_inline.py` | Customer feedback and admin replies |
| `for_admins/menu_add.py` | Adding categories and products |
| `for_admins/menu_edit.py` | Editing products |
| `for_admins/menu_stop.py` | Hiding and restoring products |
| `for_admins/menu_delete.py` | Deleting products and categories |
| `for_admins/menu_statistics.py` | Sales statistics |
| `database.py` | SQLite queries and update methods |

## Logging

The project writes logs to:

```text
texts/logging_info.log
```

Logs are rotated automatically using `RotatingFileHandler`, which helps keep long-running bot logs manageable.

## Why This Project Is Useful

This bot is a practical example of how Telegram can be used as a complete food-ordering interface for a local business. It combines:

- customer onboarding
- multilingual UX
- cart and order handling
- admin moderation
- feedback management
- lightweight analytics

without requiring a separate web dashboard.

## Notes

- The project stores some runtime state in memory, such as carts and temporary user/admin steps.
- Product availability is controlled through a `status_stop` flag.
- Reverse geocoding depends on external Nominatim lookup through `geopy`.
- The admin tools are designed for the configured `OWNER` account.

## Future Improvements

- Move secrets from `config.py` to environment variables.
- Add Docker support.
- Add automated tests.
- Add richer order-status tracking.
- Add payment gateway integration.
- Add multiple admin roles instead of a single owner account.
- Add webhook deployment support.

## License

This repository currently does not include a license file. Add one if you plan to publish the project publicly on GitHub.
