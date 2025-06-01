import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
STEAM_API_KEY = os.getenv("STEAM_API_KEY")


# 📜 تنظیم لاگ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# 🔎 تبدیل vanity به steamID64
def resolve_vanity(vanity):
    url = f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={STEAM_API_KEY}&vanityurl={vanity}"
    r = requests.get(url).json()
    if r["response"]["success"] == 1:
        return r["response"]["steamid"]
    return None

# 🎮 گرفتن اطلاعات پروفایل استیم
def get_steam_profile(steam_id):
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={STEAM_API_KEY}&steamids={steam_id}"
    r = requests.get(url).json()
    if not r["response"]["players"]:
        return None
    return r["response"]["players"][0]

# 🧪 دستور `/steam`
async def steam_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🎮 لطفاً Steam ID یا آیدی کوتاهت (vanity) رو هم وارد کن:\nمثال: /steam ali_the_gamer")
        return

    user_input = context.args[0]
    steam_id = user_input if user_input.isdigit() else resolve_vanity(user_input)

    if not steam_id:
        await update.message.reply_text("❌ نتونستم این آیدی رو پیدا کنم. یه بار دیگه چک کن رفیق.")
        return

    profile = get_steam_profile(steam_id)
    if not profile:
        await update.message.reply_text("🤷‍♂️ نتونستم اطلاعات پروفایل رو بگیرم. یا پروفایل خصوصی بوده یا اشتباهی شده.")
        return

    name = profile.get("personaname", "نامشخص")
    country = profile.get("loccountrycode", "نامشخص")
    game = profile.get("gameextrainfo", "هیچی")
    profile_url = profile.get("profileurl", "")
    avatar = profile.get("avatarfull", "")
    status = {
        0: "آفلاین",
        1: "آنلاین",
        2: "بیکاره",
        3: "مشغول",
        4: "Away",
        5: "Snooze",
        6: "مشغول ترید",
        7: "مشغول بازی"
    }.get(profile.get("personastate", 0), "نامشخص")

    msg = f"""🎮 پروفایل استیم:

👤 Name: {name}
🌍 Country: {country}
🔌 Status: {status}
🕹️ Playing: {game}
🔗 Profile: {profile_url}
"""

    await update.message.reply_photo(photo=avatar, caption=msg)

# 🏁 اجرای اصلی
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("steam", steam_command))
    print("🤖 ربات استارت شد... منتظره دستوره!")

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
