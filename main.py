import sqlite3
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackContext

# 🔐 OpenRouter API KEY
OPENROUTER_API_KEY = "sk-or-v1-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # <--YOUR_OPENAI_KEY
MODEL = "openai/gpt-3.5-turbo"

# 📁 SQLite database
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    chat_id TEXT PRIMARY KEY,
    full_name TEXT,
    username TEXT,
    last_message TEXT
)
""")
conn.commit()


def ask_openrouter(user_message, chat_id):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    messages = [
        {"role": "system", "content": "You are a helpful, friendly assistant. Reply in English."},
        {"role": "user", "content": user_message}
    ]
    payload = {
        "model": MODEL,
        "messages": messages
    }
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        print(f"❌ Error: {response.status_code} — {response.text}")
        return "Something went wrong. Please try again later."

# 🧾 /start command
def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    chat_id = update.message.chat.id
    full_name = f"{user.first_name} {user.last_name or ''}".strip()
    username = user.username if user.username else "unknown"

    cursor.execute("INSERT OR IGNORE INTO users (chat_id, full_name, username) VALUES (?, ?, ?)", (chat_id, full_name, username))
    conn.commit()

    keyboard = [
        ["📩 Contact Admin", "💬 Send Feedback"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text("Welcome! I'm your AI assistant. You can ask me anything in English.", reply_markup=reply_markup)

def handle_message(update: Update, context: CallbackContext):
    chat_id = update.message.chat.id
    text = update.message.text

    if text == "📩 Contact Admin":
        update.message.reply_text("You can contact the admin at: @Farxod_571")
        return
    elif text == "💬 Send Feedback":
        update.message.reply_text("Please type your feedback below. I’ll forward it to the team.")
        return

    reply = ask_openrouter(text, chat_id)
    update.message.reply_text(reply)

    cursor.execute("UPDATE users SET last_message = ? WHERE chat_id = ?", (text, chat_id))
    conn.commit()

# 🚀 Start the bot
def main():
    updater = Updater("YOUR_BOT_TOKEN_HERE", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
