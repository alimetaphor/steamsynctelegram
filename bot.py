from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from steam_api import SteamAPI
from db import Database
import os
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random
from steam_api import SteamAPI
import sqlite3
from utils.imagegen import generate_profile_card
import telebot
from steam_api import SteamAPI
from database import save_user_to_db
from graphics import generate_profile_card
from datetime import datetime


# بارگذاری متغیرهای محیطی
steam = SteamAPI()
load_dotenv()
# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class SteamBot:
    def __init__(self, token, steam_api_key):
        self.bot = telebot.TeleBot(token)
        self.steam = SteamAPI(steam_api_key)

        # اتصال به هندلرهای دستورها
        self.bot.message_handler(commands=["steam"])(self.handle_steam_command)
        self.db = Database()
        self.ADMINS = [40746772]  # آیدی عددی خودتان را اینجا قرار دهید
        
        # لیست لقب‌های بامزه
        self.nicknames = [
            "👑 سلطان گیم", "🔥 افسانه بی‌وقفه", "⚔️ جنگجوی استیم", 
            "🎮 گیمر حرفه‌ای", "🌟 ستاره بازی", "🧙‍♂️ جادوگر دیجیتال",
            "🚀 مسافر فضایی", "🏆 قهرمان استیم", "🎯 تیرانداز دقیق",
            "🧪 دانشمند بازی", "🦸‍♂️ ابرقهرمان گیم", "🕵️‍♂️ کارآگاه بازی",
            "🏰 مدافع قلعه", "🧟‍♂️ زامبی گیمینگ", "👽 بیگانه بازی"
        ]
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🎮 به ربات SteamSync خوش آمدید!\n\n"
            "برای شروع، آیدی استیم خود را با دستور زیر وارد کنید:\n"
            "/steam [آی‌دی_شما]"
        )
    
    async  def handle_steam_command(self, message):
        args = message.text.split()

        if len(args) < 2:
            self.bot.reply_to(message, "⛔ لطفاً SteamID یا نام کاربری Steam رو بعد از دستور بنویس.\nمثال:\n/steam gaben")
            return

        user_input = args[1]
        steam_id = user_input

        # اگه Vanity URL باشه، تبدیلش می‌کنیم به steamid واقعی
        if not steam_id.isdigit():
            steam_id = self.steam.resolve_vanity_url(user_input)
            if not steam_id:
                self.bot.reply_to(message, "😕 نتونستم SteamID رو پیدا کنم. لطفاً بررسی کن درست باشه.")
                return

        profile = self.steam.get_player_summary(steam_id)
        games = self.steam.get_owned_games(steam_id)
        total_games = len(games)

        if profile:
            display_name = profile.get("personaname", "نامشخص")
            avatar_url = profile.get("avatarfull", "")
            last_seen = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

            # ذخیره در دیتابیس
            save_user_to_db(
                telegram_id=message.from_user.id,
                steam_id=steam_id,
                display_name=display_name,
                avatar_url=avatar_url,
                total_games=total_games,
                last_updated=last_seen
            )

            # ساخت کارت گرافیکی
            generate_profile_card(
                display_name=display_name,
                avatar_url=avatar_url,
                total_games=total_games,
                last_seen=last_seen
            )

            self.bot.reply_to(
                message,
                f"🧑‍🚀 نام: {display_name}\n🎮 تعداد بازی‌ها: {total_games}\n✅ اطلاعات ذخیره شد."
            )
        else:
            self.bot.reply_to(message, "😐 پروفایلی با این SteamID پیدا نکردم.")

    def run(self):
        self.bot.infinity_polling()
            
            # انتخاب یک لقب تصادفی
            random_nickname = random.choice(self.nicknames)
            
            keyboard = [
                [InlineKeyboardButton("🎮 بازی‌های پرکاربرد", callback_data=f"games_{steam_id}"),
                InlineKeyboardButton("📊 آمار من", callback_data=f"stats_{steam_id}")],
                [InlineKeyboardButton("👨‍💻 اطلاعات پروفایل", callback_data=f"profile_{steam_id}")]
            ]
            
            await update.message.reply_photo(
                photo=summary["avatarfull"],
                caption=f"""🧑‍🚀 {summary["personaname"]}
🎮 تعداد بازی‌ها: {len(games)}
🏷️ لقب شما: {random_nickname}""",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            logging.error(f"Error: {e}")
            await update.message.reply_text("خطایی رخ داد! لطفاً آیدی را بررسی کنید")

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        steam_id = data.split('_')[1]
        
        if data.startswith("games_"):
            games = self.steam_api.get_owned_games(steam_id)
            
            # فیلتر بازی‌هایی که زمان بازی دارند و مرتب‌سازی
            games_with_playtime = [g for g in games if g.get("playtime_forever", 0) > 0]
            top_games = sorted(games_with_playtime, key=lambda x: x.get("playtime_forever", 0), reverse=True)[:5]
            
            if not top_games:
                response = "هنوز بازی‌ای با زمان بازی ثبت نشده! 🎮"
            else:
                response = "🎮 ۵ بازی پرکاربرد شما:\n\n" + "\n".join(
                    f"{i+1}. {g['name']} - {round(g['playtime_forever']/60)} ساعت"
                    for i, g in enumerate(top_games)
                )
            
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=response
            )
        
        elif data.startswith("stats_"):
            games = self.steam_api.get_owned_games(steam_id)
            games_with_playtime = [g for g in games if g.get("playtime_forever", 0) > 0]
            total_hours = sum(g['playtime_forever'] for g in games_with_playtime) // 60
            total_games = len(games)
            
            # انتخاب لقب بر اساس ساعت بازی
            nickname = "🎲 نوب سگ"
            if total_hours > 1000:
                nickname = "🔥 افسانه بی‌وقفه"
            elif total_hours > 500:
                nickname = "⚔️ جنگجوی تازه‌کار"
            elif total_hours > 100:
                nickname = "🎯 تیرانداز حرفه‌ای"
            
            response = f"""📊 آمار بازی‌های شما:
            
🎮 تعداد بازی‌ها: {total_games}
⏳ مجموع ساعت‌های بازی: {total_hours} ساعت
🏆 لقب شما: {nickname}"""
            
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=response
            )
        
        elif data.startswith("profile_"):
            summary = self.steam_api.get_player_summary(steam_id)
        
        # وضعیت آنلاین/آفلاین
        status_map = {
            0: "🟢 آنلاین",
            1: "🔴 آفلاین",
            2: "🟠 مشغول",
            3: "⏰ اشغال",
            4: "🍃 دورباش",
            5: "💼 مایل به معامله",
            6: "💤 مایل به پلی"
        }
        status_code = summary.get('personastate', 1)
        status_text = status_map.get(status_code, "🔴 آفلاین")
        
        # بازی فعلی
        current_game = "در حال بازی: " + summary.get('gameextrainfo', 'هیچ بازی') if 'gameextrainfo' in summary else "در حال حاضر بازی نمی‌کند"
        
        response = f"""🧑‍🚀 اطلاعات پروفایل:
        
🆔 SteamID: {steam_id}
👤 نام نمایشی: {summary['personaname']}
🔗 پروفایل: {summary['profileurl']}
📶 وضعیت: {status_text} {f'| {current_game}' if status_code != 1 else ''}"""
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=response
        )


async def admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in self.ADMINS:
        await update.message.reply_text("⛔ دسترسی ممنوع!")
        return
    
    total_users = self.db.get_total_users()
    recent_users = self.db.get_recent_users()
    
    response = f"""📊 آمار دیتابیس:
    
👥 تعداد کل کاربران: {total_users}
    
🆕 آخرین کاربران:"""
    
    for user in recent_users:
        response += f"\n- {user[0]} (SteamID: {user[1]}) - آخرین فعالیت: {user[2]}"
    
    await update.message.reply_text(response)
    
async def online_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش کاربران آنلاین در گروه"""
        if update.effective_chat.type not in ["group", "supergroup"]:
            await update.message.reply_text("این دستور فقط در گروه‌ها قابل استفاده است!")
            return
        
        recent_users = self.db.get_recent_users(limit=20)
        online_list = []

        for user in recent_users:
            steam_id = user[1]
            try:
                summary = self.steam_api.get_player_summary(steam_id)
                if summary.get('personastate', 0) > 0:
                    game = summary.get('gameextrainfo', 'بدون بازی')
                    online_list.append(f"👤 {user[0]} - 🎮 {game}")
            except Exception as e:
                logging.warning(f"خطا در بررسی وضعیت کاربر {steam_id}: {e}")
                continue
        
        if not online_list:
            response = "هیچ کاربر آنلاینی در گروه پیدا نشد! 😢"
        else:
            response = "🎮 کاربران آنلاین گروه:\n\n" + "\n".join(online_list)
        
        await update.message.reply_text(response)

if __name__ == "__main__":
    steam = SteamAPI()
    db = Database()

    # ۱. گرفتن اطلاعات پروفایل
    profile = steam.get_player_summary(STEAM_ID)
    if not profile:
        print("❌ نتونستم پروفایل استیم رو دریافت کنم.")
    else:
        # ۲. گرفتن بازی‌ها
        games = steam.get_owned_games(STEAM_ID)
        total_games = len(games)

        # ۳. ذخیره در دیتابیس
        db.save_user_data(
            telegram_id=TEST_TELEGRAM_ID,
            username=TEST_USERNAME,
            steam_id=STEAM_ID,
            display_name=profile.get("personaname", "Unknown"),
            last_data=profile
        )

        # ۴. ساختن کارت گرافیکی پروفایل
        generate_profile_card(
            display_name=profile.get("personaname", "Unknown"),
            avatar_url=profile.get("avatarfull", ""),
            total_games=total_games,
            last_seen=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        )

if __name__ == "__main__":
    bot = SteamBot()
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("steam", bot.steam))
    app.add_handler(CommandHandler("adminstats", bot.admin_stats))
    app.add_handler(CommandHandler("online", bot.online_users))  # دستور جدید
    app.add_handler(CallbackQueryHandler(bot.button_handler))
    
    app.run_polling()
