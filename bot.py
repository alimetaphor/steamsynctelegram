import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

# توکن‌ها از Environment Variable خونده می‌شن
BOT_TOKEN = os.getenv("BOT_TOKEN")
STEAM_API_KEY = os.getenv("STEAM_API_KEY")

# لاگ ساده
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# استارت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎮 سلام رفیق! من SteamSyncBot هستم. بگو چیکار کنم؟")

# گرفتن پروفایل استیم
async def steam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("👀 اول SteamID یا Vanity URL بده بهم.")
        return

    steam_id = context.args[0]
    try:
        r = requests.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={STEAM_API_KEY}&steamids={steam_id}")
        data = r.json()
        player = data["response"]["players"][0]
        username = player["personaname"]
        profile_url = player["profileurl"]
        game = player.get("gameextrainfo", "Not in-game")

        msg = f"""🧑‍🚀 نام کاربر: {username}
🎮 وضعیت: {game}
🌐 پروفایل: {profile_url}
        """
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text("😕 مشکلی پیش اومد یا SteamID اشتباهه.")

# اپلیکیشن رو بساز
app = ApplicationBuilder().token(BOT_TOKEN).build()

# دستورها رو اضافه کن
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("steam", steam))

# مستقیم بدون asyncio.run اجرا کن
if __name__ == "__main__":
    print("🤖 ربات استارت شد... منتظره دستوره!")
    app.run_polling()
