from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from steam_api import SteamAPI
from db import Database
import os
import logging
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv()

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class SteamBot:
    def __init__(self):
        self.db = Database()
        self.steam_api = SteamAPI(os.getenv("STEAM_API_KEY"))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🎮 سلام رفیق! من ربات SteamSyncام.!\n\n"
            "برای شروع، آیدی استیم خودتو وارد کن:\n"
            "/steam [آی‌دی_شما]"
        )
    
    async def steam(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("لطفاً آیدی استیم خودتو وارد کن\nمثال:\n/steam 76561197960435530")
            return
        
        steam_id = context.args[0]
        try:
            # دریافت اطلاعات از API
            summary = self.steam_api.get_player_summary(steam_id)
            games = self.steam_api.get_owned_games(steam_id)
            
            # ذخیره در دیتابیس
            self.db.save_user_data(
                str(update.effective_user.id),
                update.effective_user.username,
                steam_id,
                summary["personaname"],
                {"summary": summary, "games": games}
            )
            
            # ایجاد دکمه‌ها
            keyboard = [
                [InlineKeyboardButton("🎮 بازی‌های من", callback_data=f"games_{steam_id}")],
                [InlineKeyboardButton("📊 آمار من", callback_data=f"stats_{steam_id}")]
            ]
            
            await update.message.reply_photo(
                photo=summary["avatarfull"],
                caption=f"""🧑‍🚀 {summary["personaname"]}
🎮 تعداد بازی‌ها: {len(games)}""",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            logging.error(f"Error: {e}")
            await update.message.reply_text("لطفاً آیدی عددی استیمت رو بنویس")

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    steam_id = data.split('_')[1]
    
    if data.startswith("games_"):
        games = self.steam_api.get_owned_games(steam_id)
        top_games = sorted(games, key=lambda x: x.get("playtime_forever", 0), reverse=True)[:5]
        
        response = "🎮 ۵ بازی پرکاربرد شما:\n\n" + "\n".join(
            f"{i+1}. {g['name']} - {g['playtime_forever']//60} ساعت"
            for i, g in enumerate(top_games)
        )
        
        # ارسال پیام جدید بدون تغییر پست اصلی
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=response
        )
    
    elif data.startswith("stats_"):
        games = self.steam_api.get_owned_games(steam_id)
        total_hours = sum(g['playtime_forever'] for g in games) // 60
        total_games = len(games)
        
        response = f"""📊 آمار بازی‌های شما:
        
🎮 تعداد بازی‌ها: {total_games}
⏳ مجموع ساعت‌های بازی: {total_hours} ساعت
🏆 میانگین ساعت بازی برای هر بازی: {total_hours//total_games if total_games > 0 else 0} ساعت"""
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=response
        )

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # لیست ادمین‌های مجاز (آیدی عددی شما)
    ADMINS = [40746772]  # آیدی عددی خودتون رو اینجا قرار بدید
    
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("⛔ دسترسی ممنوع!")
        return
    
    cursor = self.db.conn.cursor()
    
    # آمار کلی کاربران
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    # کاربران اخیر
    cursor.execute("SELECT username, steam_id, last_seen FROM users ORDER BY last_seen DESC LIMIT 5")
    recent_users = cursor.fetchall()
    
    response = f"""📊 آمار دیتابیس:
    
👥 تعداد کل کاربران: {total_users}
    
🆕 آخرین کاربران:"""
    
    for user in recent_users:
        response += f"\n- {user[0]} (SteamID: {user[1]}) - آخرین فعالیت: {user[2]}"
    
    await update.message.reply_text(response)
    
if __name__ == "__main__":
    bot = SteamBot()
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("steam", bot.steam))
    app.add_handler(CallbackQueryHandler(bot.button_handler))
    
    app.run_polling()
