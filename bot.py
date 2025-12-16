import telebot
import json
from telebot import types

TOKEN = "8338700633:AAEqcTmh2yRW_X4AtoKfeanRw_T3zjDpfAI"
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 1896845654
CHANNEL_USERNAME = "@oT3iBu"

# ---------- utils ----------

def load_json(file):
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_sets():
    return load_json("sets_accounts.json")

def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ["member", "administrator", "creator"]
    except:
        return False

# ---------- START ----------

@bot.message_handler(commands=["start"])
def start(message):
    users = load_json("users.json")
    uid = str(message.from_user.id)

    if uid not in users:
        users[uid] = {"balance": 0, "bought": 0}
        save_json("users.json", users)

    if not is_subscribed(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔔 Подписаться", url="https://t.me/oT3iBu"))
        markup.add(types.InlineKeyboardButton("✅ Проверить подписку", callback_data="check_sub"))

        bot.send_message(
            message.chat.id,
            "❗ Для использования бота необходимо подписаться на канал:",
            reply_markup=markup
        )
        return

    show_main_menu(message)

def show_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👤 Профиль", "🎁 Ввести промокод")
    markup.add("🧰 Купить сет", "🛒 Купить прокси")

    if message.from_user.id == ADMIN_ID:
        markup.add("⚙️ Админ-панель")

    bot.send_message(
        message.chat.id,
        "🔥 Добро пожаловать в ProxyBot",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Подписка подтверждена")
        show_main_menu(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ Ты не подписался", show_alert=True)

# ---------- PROFILE ----------

@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(message):
    users = load_json("users.json")
    user = users[str(message.from_user.id)]

    bot.send_message(
        message.chat.id,
        f"👤 ID: {message.from_user.id}\n"
        f"💰 Баланс: {user['balance']} ₽\n"
        f"📦 Куплено: {user['bought']}"
    )

# ---------- PROMO (ОДНОРАЗОВЫЕ, ИСПРАВЛЕНО) ----------

@bot.message_handler(func=lambda m: m.text == "🎁 Ввести промокод")
def ask_promo(message):
    bot.send_message(message.chat.id, "✍️ Введи промокод:")
    bot.register_next_step_handler(message, use_promo)

def use_promo(message):
    promo = message.text.strip()
    users = load_json("users.json")
    promos = load_json("promocodes.json")

    if promo not in promos:
        bot.send_message(message.chat.id, "❌ Промокод недействителен")
        return

    amount = promos[promo]

    users[str(message.from_user.id)]["balance"] += amount
    del promos[promo]

    save_json("users.json", users)
    save_json("promocodes.json", promos)

    bot.send_message(
        message.chat.id,
        f"✅ Промокод принят!\n💰 +{amount} ₽ зачислено"
    )

# ---------- BUY SET ----------

@bot.message_handler(func=lambda m: m.text == "🧰 Купить сет")
def buy_set_menu(message):
    sets = load_sets()
    markup = types.InlineKeyboardMarkup()

    for server, data in sets.items():
        markup.add(types.InlineKeyboardButton(
            f"{server} (в наличии: {len(data['accounts'])})",
            callback_data=f"set_{server}"
        ))

    bot.send_message(message.chat.id, "🧰 Выбери сервер:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_"))
def show_set(call):
    server = call.data.replace("set_", "")
    sets = load_sets()
    data = sets[server]

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        f"Купить за {data['price']} ₽",
        callback_data=f"buyset_{server}"
    ))

    with open(data["image"], "rb") as photo:
        bot.send_photo(
            call.message.chat.id,
            photo,
            caption=f"{data['description']}\nЦена: {data['price']} ₽",
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("buyset_"))
def buy_set(call):
    server = call.data.replace("buyset_", "")
    users = load_json("users.json")
    sets = load_sets()

    user = users[str(call.from_user.id)]
    data = sets[server]

    if user["balance"] < data["price"]:
        bot.answer_callback_query(call.id, "❌ Недостаточно средств")
        return

    account = data["accounts"].pop(0)
    user["balance"] -= data["price"]
    user["bought"] += 1

    save_json("users.json", users)
    save_json("sets_accounts.json", sets)

    bot.send_message(
        call.message.chat.id,
        f"✅ УСПЕШНАЯ ПОКУПКА\n\n"
        f"👤 Логин: {account['login']}\n"
        f"🔑 Пароль: {account['password']}"
    )

# ---------- BUY PROXY ----------

@bot.message_handler(func=lambda m: m.text == "🛒 Купить прокси")
def buy_proxy(message):
    users = load_json("users.json")
    user = users[str(message.from_user.id)]

    if user["balance"] < 100:
        bot.send_message(message.chat.id, "❌ Нужно 100 ₽")
        return

    with open("proxies.txt", "r", encoding="utf-8") as f:
        proxies = f.readlines()

    proxy = proxies.pop(0)

    with open("proxies.txt", "w", encoding="utf-8") as f:
        f.writelines(proxies)

    user["balance"] -= 100
    user["bought"] += 1
    save_json("users.json", users)

    bot.send_message(message.chat.id, f"✅ Твоя прокси:\n{proxy}")

# ---------- ADMIN PANEL ----------

@bot.message_handler(func=lambda m: m.text == "⚙️ Админ-панель")
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Промокод", "➕ Прокси")
    markup.add("➕ Аккаунт сета", "⬅️ Назад")

    bot.send_message(message.chat.id, "⚙️ Админ-панель", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "➕ Промокод")
def add_promo(message):
    bot.send_message(message.chat.id, "Формат: CODE 50")
    bot.register_next_step_handler(message, save_promo)

def save_promo(message):
    code, amount = message.text.split()
    promos = load_json("promocodes.json")
    promos[code] = int(amount)
    save_json("promocodes.json", promos)
    bot.send_message(message.chat.id, "✅ Промокод добавлен")

@bot.message_handler(func=lambda m: m.text == "➕ Прокси")
def add_proxy(message):
    bot.send_message(message.chat.id, "Отправь прокси")
    bot.register_next_step_handler(
        message,
        lambda m: open("proxies.txt", "a", encoding="utf-8").write(m.text + "\n")
    )

@bot.message_handler(func=lambda m: m.text == "➕ Аккаунт сета")
def add_set_acc(message):
    bot.send_message(message.chat.id, "Формат: HolyWorld login password")
    bot.register_next_step_handler(message, save_set_acc)

def save_set_acc(message):
    server, login, password = message.text.split()
    sets = load_sets()
    sets[server]["accounts"].append({"login": login, "password": password})
    save_json("sets_accounts.json", sets)
    bot.send_message(message.chat.id, "✅ Аккаунт добавлен")

@bot.message_handler(func=lambda m: m.text == "⬅️ Назад")
def back(message):
    show_main_menu(message)

# ---------- RUN ----------

print("🔥 Бот запущен")
bot.polling()
