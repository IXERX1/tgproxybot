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
    markup.add("🛒 Купить прокси")

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
        bot.send_message(message.chat.id, "❌ Такого промокода нет")
        return

    if promo in user["used_promos"]:
        bot.send_message(message.chat.id, "❌ Ты уже юзал этот промокод")
        return

    user["balance"] += promos[promo]
    user["used_promos"].append(promo)
    save_json("users.json", users)

    bot.send_message(message.chat.id, f"✅ Промокод принят! +{promos[promo]} ₽")

# ---------- buy proxy ----------

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
