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
    def __init__(self, app):
        self.db = Database()
        self.steam_api = SteamAPI(os.getenv("STEAM_API_KEY"))
        self.bot = app.bot
        # لیست adminها (در صورت نیاز)
        self.ADMINS = [40746772]
        self.nicknames = [
            "سلطان گیم", "افسانه بی‌وقفه", "جنگجوی استیم",
            "گیمر حرفه‌ای", "ستاره بازی", "جادوگر دیجیتال",
            "مسافر فضایی", "قهرمان استیم", "تیرانداز دقیق"
        ]

    # ---------------------------------------
    # /// دستور /start
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🎮 به SteamSyncBot خوش اومدی!\n\n"
            "برای کار با ربات:\n"
            "🔹 /linksteam [SteamID یا vanity URL]  (ثبت آیدی برای اولین بار)\n"
            "🔹 /steam          (نمایش اطلاعات استیم خودت)\n"
            "🔹 /steam [id]     (نمایش اطلاعات کاربر دیگر بدون ذخیره‌سازی)\n\n"
            "🔹 /help               (راهنمای کامل دستورات)"
        )

    # ---------------------------------------
    # /// دستور /help
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = """🛠️ راهنمای استیم‌بات:

📌 دستورات شخصی:
  /linksteam [SteamID یا vanity URL]
    • ثبت یک‌باره آیدی استیم برای پیگیری خودکار
  /steam
    • نمایش اطلاعات پروفایل استیم خودت (اگر قبلاً ثبت کرده باشی)
  /steam [SteamID یا vanity URL]
    • نمایش اطلاعات استیم کاربر دیگر (بدون ثبت/ذخیره)

  /status @username
    • وضعیت آنلاین/آفلاین کاربر و بازی فعلی

  /notify @username GameName [here]
    • وقتی آن یوزر بازی خاص رو پلی کرد، خبر بده
      - اگر بنویسی “here”، خبر در گروه اعلام می‌شه
      - در غیر این صورت، خبر در پیام خصوصی (PV) شما می‌ره
  /mynotifs
    • فهرست نوتیف‌های ثبت‌شده توسط شما
  /removenotif [ID]
    • حذف یک نوتیف ثبت‌شده

📌 دستورات گروهی:
  /online
    • نمایش اعضای آنلاین گروهی که قبلاً /linksteam زدن
  /setdeals [topic_id]
    • تنظیم تاپیک مخصوص ارسال روزانه تخفیف‌ها
    • مثال: /setdeals 45 

  🔔 هر ۵ دقیقه: بات بررسی می‌کنه ببینه آیا کاربری درخواست `/notify` داره یا نه
  ⏲️ هر ۲۴ ساعت: بات لیست تخفیف‌ها رو توی تاپیک تعریف‌شده ارسال می‌کنه
  🧾 دیگه چی؟ بزودی:
- /compare
- /rank
- ...

"""
        await update.message.reply_text(text)

    # ---------------------------------------
    # /// دستور /linksteam [id]
    # ثبت یک‌باره آیدی استیم (SteamID64 یا vanity URL) و ذخیره در دیتابیس
    async def linksteam(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or "unknown"

        if not context.args:
            await update.message.reply_text(
                "🚫 لطفاً یک آیدی استیم بنویس:\n"
                "مثال:\n/linksteam gaben\nیا\n/linksteam 76561197960287930"
            )
            return

        input_id = context.args[0]
        try:
            steam_id = input_id if input_id.isdigit() else self.steam_api.resolve_vanity_url(input_id)
        except Exception:
            await update.message.reply_text("🔑 این آیدی استیم معتبر نیست. دوباره امتحان کن.")
            return

        # فراخوانی API برای دریافت پروفایل و ذخیره در دیتابیس
        try:
            summary = self.steam_api.get_player_summary(steam_id)
            games = self.steam_api.get_owned_games(steam_id)

            self.db.save_user_data(
                telegram_id=user_id,
                username=username,
                steam_id=steam_id,
                display_name=summary.get("personaname", ""),
                last_data={"summary": summary, "games": games}
            )
            await update.message.reply_text("✅ آیدی استیم شما با موفقیت ثبت شد!")
        except Exception as e:
            logging.error(e)
            await update.message.reply_text("❌ مشکلی پیش اومد. دوباره تلاش کن!")

    # ---------------------------------------
    # /// دستور /steam [id?]
    # بدون آرگومان: نمایش اطلاعات خودِ کاربر (اگر قبلاً ثبت شده باشد)
    # با آرگومان: نمایش اطلاعات هر SteamID یا vanity URL (بدون ثبت)
    async def steam(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or "unknown"

        # اگر آرگومان داده شده باشد → فقط نمایش اطلاعات آن کاربر (ثبت نمی‌شود)
        if context.args:
            input_id = context.args[0]
            try:
                steam_id = input_id if input_id.isdigit() else self.steam_api.resolve_vanity_url(input_id)
            except Exception:
                await update.message.reply_text("🔑 این آیدی استیم معتبر نیست. دوباره امتحان کن.")
                return

            # دریافت پروفایل برای آن SteamID
            try:
                summary = self.steam_api.get_player_summary(steam_id)
                games = self.steam_api.get_owned_games(steam_id)
            except Exception as e:
                logging.error(e)
                await update.message.reply_text("❌ مشکلی پیش اومد. دوباره تلاش کن!")
                return

        # اگر آرگومان نداشته باشد → سعی کن SteamID خودِ کاربر را از دیتابیس بگیری
        else:
            row = self.db.conn.execute(
                "SELECT steam_id FROM users WHERE telegram_id = ?", (user_id,)
            ).fetchone()
            if not row:
                await update.message.reply_text(
                    "👀 اول باید آیدی استیم خودتو ثبت کنی:\n"
                    "/linksteam [SteamID یا vanity URL]"
                )
                return

            steam_id = row[0]
            try:
                summary = self.steam_api.get_player_summary(steam_id)
                games = self.steam_api.get_owned_games(steam_id)
            except Exception as e:
                logging.error(e)
                await update.message.reply_text("❌ مشکلی پیش اومد. دوباره تلاش کن!")
                return

        # اگر اطلاعات بدست آمد → نمایشش بده
        nickname = random.choice(self.nicknames)
        state = summary.get("personastate", 0)
        status_map = {
            0: "🔴 آفلاین", 1: "🟢 آنلاین", 2: "🟠 مشغول",
            3: "⏰ اشغال", 4: "🍃 دور باش", 5: "💼 معامله",
            6: "🎮 در حال بازی"
        }
        status = status_map.get(state, "نامشخص")
        game = summary.get("gameextrainfo", None)
        country = summary.get("loccountrycode", "نامشخص")

        caption = (
            f"🧑‍🚀 {summary.get('personaname','')}\n"
            f"🎮 تعداد بازی‌هات: {len(games)}\n"
            f"🏷️ لقبت: {nickname}\n"
            f"📶 وضعیت: {status}" + (f" | 🎲 {game}" if game else "") + "\n"
            f"🌍 ریجن: {country}"
        )

        buttons = [
            [InlineKeyboardButton("🎮 بازی‌های پرکاربرد", callback_data=f"games_{steam_id}"),
             InlineKeyboardButton("📊 آمار من", callback_data=f"stats_{steam_id}")],
            [InlineKeyboardButton("🧑‍🚀 پروفایل تصویری", callback_data=f"profilepic_{steam_id}")]
        ]

        await update.message.reply_photo(
            photo=summary.get("avatarfull", ""),
            caption=caption,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # ---------------------------------------
    # /// هندلر دکمه‌ها (بازی‌های پرکاربرد، آمار، پروفایل تصویری)
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
                    f"{i+1}. {g.get('name','نامشخص')} - {g.get('playtime_forever',0)//60} ساعت"
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
                f"📊 آمار کلی:\nتعداد بازی‌هات: {len(games)}\n"
                f"تایم پلی: {total} ساعت\nلقب: {nickname}"
            )

        elif data.startswith("profilepic_"):
            summary = self.steam_api.get_player_summary(steam_id)
            games = self.steam_api.get_owned_games(steam_id)
            filename = f"/tmp/{steam_id}_card.png"
            generate_profile_card(
                display_name=summary.get("personaname",""),
                avatar_url=summary.get("avatarfull",""),
                total_games=len(games),
                last_seen=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                filename=filename
            )
            with open(filename, "rb") as photo:
                await query.message.reply_photo(photo=photo)

    # ---------------------------------------
    # /// دستور /status @username
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("مثال: /status @username")
            return

        target = context.args[0].lstrip("@")
        steam_id = self.db.get_user_by_username(target)
        if not steam_id:
            await update.message.reply_text("این کاربر هنوز آیدی استیمشو ثبت نکرده.")
            return

        try:
            summary = self.steam_api.get_player_summary(steam_id)
            state = summary.get("personastate", 0)
            status_map = {
                0: "🔴 آفلاین", 1: "🟢 آنلاین", 2: "🟠 مشغول",
                3: "⏰ اشغال", 4: "🍃 دور باش", 5: "💼 معامله",
                6: "🎮 پلی"
            }
            status = status_map.get(state, "نامشخص")
            game = summary.get("gameextrainfo", None)
            response = f"👤 @{target}\n📶 وضعیت: {status}"
            if game:
                response += f"\n🎮 بازی فعلی: {game}"
            await update.message.reply_text(response)
        except Exception as e:
            logging.error(e)
            await update.message.reply_text("خطا در دریافت وضعیت کاربر.")

    # ---------------------------------------
    # /// دستور /online (نمایش اعضای آنلاین گروه)
    async def online_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type not in ["group", "supergroup"]:
            await update.message.reply_text("این دستور فقط در گروه‌ها قابل استفاده است.")
            return

        group_id = str(update.effective_chat.id)
        users = self.db.get_users_in_group(group_id)
        online = []
        for username, steam_id in users:
            try:
                summary = self.steam_api.get_player_summary(steam_id)
                if summary.get("personastate", 0) > 0:
                    game = summary.get("gameextrainfo", "بدون بازی")
                    online.append(f"👤 @{username} – 🎮 {game}")
            except:
                continue

        if not online:
            await update.message.reply_text("هیچ‌کس آنلاین نیست 😢")
        else:
            msg = "🎮 اعضای آنلاین گروه:\n\n" + "\n".join(online)
            await update.message.reply_text(msg)

    # ---------------------------------------
    # /// دستور /setdeals [topic_id]
    # ثبت تاپیک جداگانه برای ارسال روزانهٔ تخفیف‌ها
    async def set_deals_topic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type not in ["supergroup"]:
            await update.message.reply_text("این دستور فقط در سوپرگروه‌ها کار می‌کند.")
            return

        if not context.args:
            await update.message.reply_text(
                "🚫 لطفاً آیدی تاپیک (thread_id) را وارد کن:\n"
                "مثال:\n/setdeals 45"
            )
            return

        topic_id = context.args[0]
        group_id = str(update.effective_chat.id)
        self.db.set_auto_post_target(group_id, topic_id, "deals")
        await update.message.reply_text(
            f"✅ ذخیره شد! هر ۲۴ ساعت تخفیف‌ها در تاپیک {topic_id} ارسال می‌شوند."
        )

    # ---------------------------------------
    # /// تسک دوره‌ای ارسال تخفیف‌ها (فعلاً mock)
    async def post_mock_deals(self):
        await asyncio.sleep(10)  # صبر اولیه قبل از استارت پریود
        while True:
            targets = self.db.get_post_targets_by_purpose("deals")
            for group_id, topic_id in targets:
                try:
                    text = "🔥 تخفیف‌های امروز Steam:\n\n"
                    for i in range(1, 11):
                        # اینجا می‌آید درصد تخفیف واقعی را از API دریافت کنی
                        text += f"{i}. Game {{i}} - {{random.randint(40,90)}}% Off\n"
                    text += "\n🎮 ادامه دارد..."

                    await self.bot.send_message(
                        chat_id=group_id,
                        message_thread_id=int(topic_id),
                        text=text
                    )
                except Exception as e:
                    logging.error(f"خطا در ارسال تخفیف‌ها: {e}")

            await asyncio.sleep(86400)  # هر ۲۴ ساعت

    # ---------------------------------------
    # /// دستور /notify @username GameName [here]
    async def notify(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "🚫 ترکیب نادرست!\n"
                "مثال‌ها:\n"
                "/notify @username Rust\n"
                "/notify @username Rust here"
            )
            return

        watcher_id = str(update.effective_user.id)
        target_username = args[0].lstrip("@")
        game_name = args[1]
        scope = "private"
        group_id = None

        # اگر آرگومان سوم "here" باشد → ارسال در همین گروه
        if len(args) == 3 and args[2].lower() == "here":
            if update.effective_chat.type not in ["group", "supergroup"]:
                await update.message.reply_text("برای نوتیف در گروه باید این دستور را در گروه بنویسی.")
                return
            scope = "group"
            group_id = str(update.effective_chat.id)

        req_id = self.db.add_notify_request(watcher_id, target_username, game_name, scope, group_id)
        await update.message.reply_text(f"✅ درخواست نوتیف با ID {req_id} ثبت شد.")

    # ---------------------------------------
    # /// دستور /mynotifs
    async def my_notifs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        watcher_id = str(update.effective_user.id)
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT id, target_username, game_name, scope, group_id
            FROM notify_requests
            WHERE watcher_telegram_id = ?
        """, (watcher_id,))
        rows = cursor.fetchall()

        if not rows:
            await update.message.reply_text("🚫 شما هیچ درخواست نوتیفی ندارید.")
            return

        text = "🔔 درخواست‌های نوتیف شما:\n"
        for row in rows:
            _id, target, game, scope, grp = row
            text += f"{_id}. @{target} بازی {game} – {'در گروه ' + grp if scope == 'group' else 'پیام خصوصی'}\n"

        await update.message.reply_text(text)

    # ---------------------------------------
    # /// دستور /removenotif [ID]
    async def remove_notif(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("مثال: /removenotif 5")
            return
        try:
            req_id = int(context.args[0])
            self.db.remove_notify_request(req_id)
            await update.message.reply_text("✅ درخواست نوتیف حذف شد.")
        except Exception:
            await update.message.reply_text("❌ امکان حذف وجود ندارد. ID را بررسی کن.")

    # ---------------------------------------
    # /// تسک دوره‌ای چک کردن درخواست‌های نوتیف
    async def check_notify_requests(self):
        await asyncio.sleep(10)  # صبر اولیه
        while True:
            rows = self.db.get_all_notify_requests()
            for row in rows:
                _id, watcher_id, target_username, game_name, scope, grp = row
                # ابتدا steam_id هدف را از جدول users دریافت کن
                steam_id = self.db.get_user_by_username(target_username)
                if not steam_id:
                    continue
                try:
                    summary = self.steam_api.get_player_summary(steam_id)
                    current_game = summary.get("gameextrainfo", "")
                    # اگر اسم بازی موردنظر در جزییات بازی فعلی پیدا شد
                    if current_game and game_name.lower() in current_game.lower():
                        if scope == "private":
                            await self.bot.send_message(
                                chat_id=int(watcher_id),
                                text=f"🔔 @{target_username} هم‌اکنون در حال بازی {game_name} است!"
                            )
                        else:
                            await self.bot.send_message(
                                chat_id=int(grp),
                                text=f"🔔 @{target_username} هم‌اکنون در حال بازی {game_name} است!"
                            )
                        # حذف درخواست (فقط یک‌بار ارسال می‌شود)
                        self.db.remove_notify_request(_id)
                except Exception:
                    continue

            await asyncio.sleep(300)  # هر ۵ دقیقه

if __name__ == "__main__":
    load_dotenv()
    nest_asyncio.apply()

    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    bot = SteamBot(app)

    # ثبت handler ها
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("help", bot.help_command))
    app.add_handler(CommandHandler("linksteam", bot.linksteam))
    app.add_handler(CommandHandler("steam", bot.steam))
    app.add_handler(CommandHandler("status", bot.status))
    app.add_handler(CommandHandler("online", bot.online_users))
    app.add_handler(CommandHandler("setdeals", bot.set_deals_topic))
    app.add_handler(CommandHandler("notify", bot.notify))
    app.add_handler(CommandHandler("mynotifs", bot.my_notifs))
    app.add_handler(CommandHandler("removenotif", bot.remove_notif))
    app.add_handler(CallbackQueryHandler(bot.button_handler))

    # Taskهای پس‌زمینه
    asyncio.get_event_loop().create_task(bot.post_mock_deals())
    asyncio.get_event_loop().create_task(bot.check_notify_requests())

    print("🤖 SteamSyncBot داره گوش می‌دهد...")
    asyncio.get_event_loop().run_until_complete(app.run_polling())
