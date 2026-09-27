"""
Bot Telegram — boutique intégrée (comptes streaming, jeux, VPN, avantages).
Librairie : python-telegram-bot v21+

Installation (depuis un service comme Railway, Render, PythonAnywhere ou un VPS —
tout ce qui tourne du Python en continu, accessible depuis un navigateur mobile) :
    pip install python-telegram-bot==21.*

Configuration :
    1. Crée un bot avec @BotFather sur Telegram, récupère le token.
    2. Remplace BOT_TOKEN ci-dessous (ou définis la variable d'environnement BOT_TOKEN).
    3. Lance : python bot.py
"""

import os
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "COLLE_TON_TOKEN_ICI")

# --- Catalogue -------------------------------------------------------------

CATEGORIES = ["Streaming", "Jeux", "VPN", "Avantages", "Autre"]

PRODUCTS = {
    "p1": {"name": "Netflix Premium — 1 mois", "cat": "Streaming", "price": 6},
    "p2": {"name": "Spotify Premium — 1 mois", "cat": "Streaming", "price": 4},
    "p3": {"name": "Valorant — 5000 VP", "cat": "Jeux", "price": 35},
    "p4": {"name": "Xbox Game Pass Ultimate — 3 mois", "cat": "Jeux", "price": 29},
    "p5": {"name": "NordVPN — 1 an", "cat": "VPN", "price": 39},
    "p6": {"name": "ExpressVPN — 6 mois", "cat": "VPN", "price": 45},
    "p7": {"name": "Carte cadeau Amazon — 25€", "cat": "Avantages", "price": 25},
    "p8": {"name": "Discord Nitro — 1 mois", "cat": "Avantages", "price": 8},
    "p9": {"name": "Support prioritaire", "cat": "Autre", "price": 5},
}

# panier en mémoire : { user_id: {product_id: qty} }
CARTS: dict[int, dict[str, int]] = {}


def get_cart(user_id: int) -> dict[str, int]:
    return CARTS.setdefault(user_id, {})


# --- Écrans ------------------------------------------------------------

def menu_categories() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(c, callback_data=f"cat:{c}")] for c in CATEGORIES]
    rows.append([InlineKeyboardButton("🛒 Mon panier", callback_data="cart")])
    return InlineKeyboardMarkup(rows)


def menu_products(cat: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"{p['name']} — {p['price']}€", callback_data=f"add:{pid}")]
        for pid, p in PRODUCTS.items() if p["cat"] == cat
    ]
    rows.append([InlineKeyboardButton("⬅️ Catégories", callback_data="menu")])
    return InlineKeyboardMarkup(rows)


def menu_cart(user_id: int) -> tuple[str, InlineKeyboardMarkup]:
    cart = get_cart(user_id)
    if not cart:
        text = "Ton panier est vide."
        rows = [[InlineKeyboardButton("⬅️ Catégories", callback_data="menu")]]
        return text, InlineKeyboardMarkup(rows)

    lines = ["🛒 *Ton panier*\n"]
    total = 0
    for pid, qty in cart.items():
        p = PRODUCTS[pid]
        line_total = p["price"] * qty
        total += line_total
        lines.append(f"• {p['name']} x{qty} — {line_total}€")
    lines.append(f"\n*Total : {total}€*")

    rows = [
        [InlineKeyboardButton("✅ Commander", callback_data="checkout")],
        [InlineKeyboardButton("🗑 Vider", callback_data="clear")],
        [InlineKeyboardButton("⬅️ Catégories", callback_data="menu")],
    ]
    return "\n".join(lines), InlineKeyboardMarkup(rows)


# --- Handlers ------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bienvenue 👋\nChoisis une catégorie :",
        reply_markup=menu_categories(),
    )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "menu":
        await query.edit_message_text("Choisis une catégorie :", reply_markup=menu_categories())

    elif data.startswith("cat:"):
        cat = data.split(":", 1)[1]
        await query.edit_message_text(f"📂 {cat}", reply_markup=menu_products(cat))

    elif data.startswith("add:"):
        pid = data.split(":", 1)[1]
        cart = get_cart(user_id)
        cart[pid] = cart.get(pid, 0) + 1
        await query.answer(f"Ajouté : {PRODUCTS[pid]['name']}", show_alert=False)

    elif data == "cart":
        text, kb = menu_cart(user_id)
        await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")

    elif data == "clear":
        CARTS[user_id] = {}
        text, kb = menu_cart(user_id)
        await query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")

    elif data == "checkout":
        cart = get_cart(user_id)
        if not cart:
            await query.answer("Panier vide.", show_alert=True)
            return
        total = sum(PRODUCTS[pid]["price"] * qty for pid, qty in cart.items())
        # TODO : brancher un vrai paiement ici (Telegram Payments, crypto, virement...)
        await query.edit_message_text(
            f"✅ Commande enregistrée — total {total}€.\n"
            "Un vendeur va te contacter pour le paiement et la livraison.",
        )
        CARTS[user_id] = {}


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))
    app.run_polling()


if __name__ == "__main__":
    main()

