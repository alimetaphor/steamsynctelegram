
import os
import logging
import asyncio
import nest_asyncio
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from steam_api import SteamAPI
from db import Database
from imagegen import generate_profile_card
from dotenv import load_dotenv
import random
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class SteamBot:
    def __init__(self):
        self.db = Database()
        self.steam_api = SteamAPI(os.getenv("STEAM_API_KEY"))
        self.ADMINS = [123456789]
        self.nicknames = [
            "سلطان گیم", "افسانه بی‌وقفه", "جنگجوی استیم", 
            "گیمر حرفه‌ای", "ستاره بازی", "جادوگر دیجیتال",
            "مسافر فضایی", "قهرمان استیم", "تیرانداز دقیق"
        ]

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "سلام رفیق! من SteamSyncBot هستم.\n"
            "اگه می‌خوای اطلاعات استیمت رو ببینی، اینطوری بزن:\n"
            "/steam آیدی‌ت (یا vanity URL)"
        )

    async def steam(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("آیدی استیمت رو بزن دیگه!\nمثال: /steam gaben")
            return

        steam_id = context.args[0]
        try:
            summary = self.steam_api.get_player_summary(steam_id)
            games = self.steam_api.get_owned_games(steam_id)

            self.db.save_user_data(
                str(update.effective_user.id),
                update.effective_user.username,
                steam_id,
                summary["personaname"],
                {"summary": summary, "games": games}
            )

            nickname = random.choice(self.nicknames)

            # وضعیت آنلاین و بازی
            status_map = {
                0: "🔴 آفلاین",
                1: "🟢 آنلاین",
                2: "🟠 مشغول",
                3: "⏰ اشغال",
                4: "🍃 دور باش",
                5: "💼 مایل به معامله",
                6: "🎮 در حال بازی"
            }
            state = summary.get("personastate", 0)
            status = status_map.get(state, "نامشخص")
            current_game = summary.get("gameextrainfo", None)
            country = summary.get("loccountrycode", "نامشخص")

            keyboard = [
                [InlineKeyboardButton("🎮 بازی‌های پرکاربرد", callback_data=f"games_{steam_id}"),
                 InlineKeyboardButton("📊 آمار من", callback_data=f"stats_{steam_id}")],
                [InlineKeyboardButton("🧑‍🚀 پروفایل تصویری", callback_data=f"profilepic_{steam_id}")]
            ]

            caption = (
                f"{summary['personaname']}\n"
                f"🎮 تعداد بازی‌هات: {len(games)}\n"
                f"🏷️ لقبت: {nickname}\n"
                f"📶 وضعیت: {status}" + 
                (f" | 🎲 در حال بازی: {current_game}" if current_game else "") + "\n"
                f"🌍 ریجن: {country}"
            )

            await update.message.reply_photo(
                photo=summary["avatarfull"],
                caption=caption,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logging.error(e)
            await update.message.reply_text("یه مشکلی پیش اومد! آیدی درست بود؟")

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data
        steam_id = data.split("_")[1]

        if data.startswith("games_"):
            try:
                games = self.steam_api.get_owned_games(steam_id)
                top_games = sorted(
                    [g for g in games if g.get("playtime_forever", 0) > 0],
                    key=lambda g: g["playtime_forever"],
                    reverse=True
                )[:5]

                if not top_games:
                    await query.message.reply_text("هنوز بازی‌ای ثبت نشده!")
                    return

                msg = "🎮 پرپلی‌ترین‌ بازی‌هات:\n\n" + "\n".join(
                    f"{i+1}. {g.get('name', 'نامشخص')} - {g.get('playtime_forever', 0)//60} ساعت"
                    for i, g in enumerate(top_games)
                )
                await query.message.reply_text(msg)
            except Exception as e:
                await query.message.reply_text(f"خطا در پردازش بازی‌ها: {str(e)}")

        elif data.startswith("stats_"):
            games = self.steam_api.get_owned_games(steam_id)
            total = sum(g["playtime_forever"] for g in games) // 60
            nickname = "نوب سگ" if total < 100 else (
                "تازه‌کار جان‌سخت" if total < 500 else (
                    "افسانه‌ی خواب‌ندیده" if total < 1000 else "رئیس قبیله"
                )
            )
            await query.message.reply_text(
                f"📊 آمار کلی:\nتعداد بازی‌هات: {len(games)}\nتایم پلی: {total} ساعت\nلقب: {nickname}"
            )

        elif data.startswith("profilepic_"):
            summary = self.steam_api.get_player_summary(steam_id)
            games = self.steam_api.get_owned_games(steam_id)
            filename = f"/tmp/{steam_id}_card.png"
            generate_profile_card(
                display_name=summary["personaname"],
                avatar_url=summary["avatarfull"],
                total_games=len(games),
                last_seen=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                filename=filename
            )
            with open(filename, "rb") as photo:
                await query.message.reply_photo(photo=photo)

if __name__ == "__main__":
    load_dotenv()
    nest_asyncio.apply()
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    bot = SteamBot()
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("steam", bot.steam))
    app.add_handler(CallbackQueryHandler(bot.button_handler))
    print("🤖 SteamSyncBot داره گوش می‌ده...")
    asyncio.get_event_loop().run_until_complete(app.run_polling())
