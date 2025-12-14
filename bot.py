import telebot
import json
from telebot import types

TOKEN = "8338700633:AAEqcTmh2yRW_X4AtoKfeanRw_T3zjDpfAI"
bot = telebot.TeleBot(TOKEN)

# ---------- utils ----------

def load_json(file):
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_sets():
    return load_json("sets_accounts.json")

# ---------- start ----------

@bot.message_handler(commands=["start"])
def start(message):
    user_id = str(message.from_user.id)
    users = load_json("users.json")

    if user_id not in users:
        users[user_id] = {
            "balance": 0,
            "used_promos": [],
            "bought": 0
        }
        save_json("users.json", users)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👤 Профиль", "🎁 Ввести промокод")
    markup.add("🧰 Купить сет", "🛒 Купить прокси")

    bot.send_message(
        message.chat.id,
        "🔥 Добро пожаловать в ProxyBot\nВыбирай, что нужно 👇",
        reply_markup=markup
    )

# ---------- profile ----------

@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(message):
    users = load_json("users.json")
    user = users[str(message.from_user.id)]

    text = (
        f"👤 ID: {message.from_user.id}\n"
        f"💰 Баланс: {user['balance']} ₽\n"
        f"📦 Куплено прокси: {user['bought']}"
    )
    bot.send_message(message.chat.id, text)

# ---------- promo ----------

@bot.message_handler(func=lambda m: m.text == "🎁 Ввести промокод")
def ask_promo(message):
    bot.send_message(message.chat.id, "✍️ Введи промокод:")
    bot.register_next_step_handler(message, use_promo)


def use_promo(message):
    promo = message.text.strip()

    users = load_json("users.json")
    promos = load_json("promocodes.json")
    user = users[str(message.from_user.id)]

    if promo not in promos:
        bot.send_message(
            message.chat.id,
            "❌ Такого промокода нет или он уже использован"
        )
        return

    # начисляем деньги
    user["balance"] += promos[promo]

    # ❌ УДАЛЯЕМ промокод навсегда
    del promos[promo]

    save_json("users.json", users)
    save_json("promocodes.json", promos)

    bot.send_message(
        message.chat.id,
        "✅ Промокод принят!\n"
        "💰 +10 ₽ зачислено\n"
        "⛔ Промокод больше недоступен"
    )


# ---------- buy set ----------

@bot.message_handler(func=lambda m: m.text == "🧰 Купить сет")
def buy_set_menu(message):
    sets = load_sets()
    markup = types.InlineKeyboardMarkup()

    for server, data in sets.items():
        count = len(data["accounts"])
        markup.add(
            types.InlineKeyboardButton(
                text=f"{server} (в наличии: {count})",
                callback_data=f"set_{server}"
            )
        )

    bot.send_message(
        message.chat.id,
        "🧰 Выбери сервер для покупки сета:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def show_set(call):
    server = call.data.replace("set_", "")
    sets = load_sets()
    data = sets[server]

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            text=f"✅ Купить за {data['price']} ₽",
            callback_data=f"buyset_{server}"
        )
    )

    with open(data["image"], "rb") as photo:
        bot.send_photo(
            call.message.chat.id,
            photo,
            caption=f"{data['description']}\n💰 Цена: {data['price']} ₽",
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("buyset_"))
def buy_set(call):
    server = call.data.replace("buyset_", "")
    user_id = str(call.from_user.id)

    users = load_json("users.json")
    sets = load_sets()

    user = users[user_id]
    data = sets[server]

    if user["balance"] < data["price"]:
        bot.answer_callback_query(call.id, "❌ Недостаточно средств")
        return

    if not data["accounts"]:
        bot.answer_callback_query(call.id, "❌ Сеты закончились")
        return

    account = data["accounts"].pop(0)

    user["balance"] -= data["price"]
    save_json("users.json", users)
    save_json("sets_accounts.json", sets)

    bot.send_message(
        call.message.chat.id,
        f"✅ УСПЕШНАЯ ПОКУПКА!\n\n"
        f"🧰 PvP сет {server}\n"
        f"⚠️ Сеты могут незначительно отличаться\n\n"
        f"🔐 Данные аккаунта:\n"
        f"👤 Логин: {account['login']}\n"
        f"🔑 Пароль: {account['password']}\n\n"
        f"➡️ Зайди на этот аккаунт — сет уже находится там"
    )

# ---------- buy proxy (пока как было) ----------

@bot.message_handler(func=lambda m: m.text == "🛒 Купить прокси")
def buy_proxy(message):
    users = load_json("users.json")
    user = users[str(message.from_user.id)]

    if user["balance"] < 100:
        bot.send_message(message.chat.id, "❌ Нужно минимум 100 ₽")
        return

    with open("proxies.txt", "r", encoding="utf-8") as f:
        proxies = f.readlines()

    if not proxies:
        bot.send_message(message.chat.id, "❌ Прокси закончились")
        return

    proxy = proxies.pop(0)

    with open("proxies.txt", "w", encoding="utf-8") as f:
        f.writelines(proxies)

    user["balance"] -= 100
    user["bought"] += 1
    save_json("users.json", users)

    bot.send_message(message.chat.id, f"✅ Твоя прокси:\n{proxy}")

# ---------- run ----------

print("🔥 Бот запущен")
bot.polling()
