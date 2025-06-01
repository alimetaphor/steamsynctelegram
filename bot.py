
# bot.py - نمونه ساده اولیه با استفاده از دیتابیس و دستور /steam

import logging
import sqlite3
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import requests
import os
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
STEAM_API_KEY = os.getenv("STEAM_API_KEY")

conn = sqlite3.connect("steamsync_users.db", check_same_thread=False)
cursor = conn.cursor()

logging.basicConfig(level=logging.INFO)

def save_user_data(telegram_id, username, steam_id, display_name, last_data):
    cursor.execute("""
        INSERT INTO users (telegram_id, username, steam_id, display_name, last_seen, last_fetched_data)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
            steam_id=excluded.steam_id,
            display_name=excluded.display_name,
            last_seen=excluded.last_seen,
            last_fetched_data=excluded.last_fetched_data
    """, (telegram_id, username, steam_id, display_name, datetime.utcnow(), json.dumps(last_data)))
    conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text(
    "🎮 سلام رفیق! برای دیدن اطلاعات استیمت، بنویس:\n"
    "مثلاً:\n"
    "`/steamid YOUR_ID`\n\n"
    "یا از آیدی دلخواهت استفاده کن:\n"
    "`/steamid gaben`"
)

def fetch_steam_summary(steam_id):
    r = requests.get(f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steam_id}")
    return r.json()["response"]["players"][0]

def fetch_owned_games(steam_id):
    r = requests.get(f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={STEAM_API_KEY}&steamid={steam_id}&include_appinfo=1&format=json")
    return r.json()["response"].get("games", [])

async def steam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
   await update.message.reply_text("""🧩 لطفاً Steam ID خودت رو وارد کن:
مثلاً:
76561197960435530 یا gaben""")

        return
    steam_id = context.args[0]
    summary = fetch_steam_summary(steam_id)
    games = fetch_owned_games(steam_id)
    player_name = summary["personaname"]
    avatar = summary["avatarfull"]

    # ذخیره اطلاعات در دیتابیس
    save_user_data(
        str(update.effective_user.id),
        update.effective_user.username,
        steam_id,
        player_name,
        {"summary": summary, "games": games}
    )

    keyboard = [[InlineKeyboardButton("اطلاعات بیشتر 🎮", callback_data=f"more_{steam_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_photo(
        photo=avatar,
        caption=f"🧑‍🚀 {player_name} on Steam
🎮 تعداد بازی‌ها: {len(games)}",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("more_"):
        steam_id = data.split("_")[1]
        games = fetch_owned_games(steam_id)
        top_games = sorted(games, key=lambda x: x.get("playtime_forever", 0), reverse=True)[:5]
        game_lines = [f"🎯 {g['name']} - {round(g['playtime_forever']/60)}h" for g in top_games]
        nickname = "🔥 افسانه‌ی بی‌وقفه" if top_games and top_games[0]["playtime_forever"] > 10000 else "🎲 گیمر معمولی"
        text = "🎮 ۵ بازی پرکاربرد:
" + "\n".join(game_lines) + f"\n\nلقب: {nickname}"
        await query.edit_message_caption(caption=text)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("steam", steam))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
