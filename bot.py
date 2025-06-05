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
        self.ADMINS = [40746772]  # آیدی ادمین‌ها
        self.nicknames = [
            "سلطان گیم", "افسانه بی‌وقفه", "جنگجوی استیم", 
            "گیمر حرفه‌ای", "ستاره بازی", "جادوگر دیجیتال",
            "مسافر فضایی", "قهرمان استیم", "تیرانداز دقیق"
        ]

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🎮 به SteamSyncBot خوش اومدی!\n\n"
            "🔹 /steam [SteamID یا vanity URL]\n"
            "   دریافت پروفایل و بازی‌ها\n"
            "🔹 دکمه‌ها برای آمار و کارت پروفایل\n"
            "🔹 /status @username | /online | /setdeals | /notify\n"
        )

    async def steam(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or "unknown"

        if context.args:
            input_id = context.args[0]
            try:
                steam_id = input_id if input_id.isdigit() else self.steam_api.resolve_vanity_url(input_id)
            except Exception:
                await update.message.reply_text("🔑 آیدی اشتباهه! دوباره امتحان کن.")
                return
        else:
            steam_id = self.db.get_user_by_username(username)
            if not steam_id:
                await update.message.reply_text("👀 اول یک‌بار آیدی استیمتو بده:\n/steam [SteamID یا vanity URL]")
                return

        try:
            summary = self.steam_api.get_player_summary(steam_id)
            games = self.steam_api.get_owned_games(steam_id)
            self.db.save_user_data(
                telegram_id=user_id,
                username=username,
                steam_id=steam_id,
                display_name=summary["personaname"],
                last_data={"summary": summary, "games": games}
            )

            if update.effective_chat.type in ["group", "supergroup"]:
                self.db.link_user_to_group(user_id, str(update.effective_chat.id), username)

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
                f"🧑‍🚀 {summary['personaname']}\\n"
                f"🎮 تعداد بازی‌هات: {len(games)}\\n"
                f"🏷️ لقبت: {nickname}\\n"
                f"📶 وضعیت: {status}" + (f" | 🎲 {game}" if game else "") + "\\n"
                f"🌍 ریجن: {country}"
            )

            buttons = [
                [InlineKeyboardButton("🎮 بازی‌های پرکاربرد", callback_data=f"games_{steam_id}"),
                 InlineKeyboardButton("📊 آمار من", callback_data=f"stats_{steam_id}")],
                [InlineKeyboardButton("🧑‍🚀 پروفایل تصویری", callback_data=f"profilepic_{steam_id}")]
            ]

            if context.args:
                await update.message.reply_text("✅ آیدی استیمت ذخیره شد.")

            await update.message.reply_photo(
                photo=summary["avatarfull"],
                caption=caption,
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        except Exception as e:
            logging.error(e)
            await update.message.reply_text("یه مشکلی پیش اومد! احتمالاً آیدی اشتباهه.")

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

                msg = "🎮 پرپلی‌ترین‌ بازی‌هات:\\n\\n" + "\\n".join(
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
                f"📊 آمار کلی:\\nتعداد بازی‌هات: {len(games)}\\nتایم پلی: {total} ساعت\\nلقب: {nickname}"
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

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("مثال: /status @username")
            return

        username = context.args[0].replace("@", "")
        steam_id = self.db.get_user_by_username(username)
        if not steam_id:
            await update.message.reply_text("این کاربر هنوز استیمشو ست نکرده.")
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
            response = f"👤 @{username}\\n📶 وضعیت: {status}"
            if game:
                response += f"\\n🎮 بازی فعلی: {game}"

            await update.message.reply_text(response)
        except Exception as e:
            logging.error(e)
            await update.message.reply_text("خطا در دریافت وضعیت کاربر.")

    async def online_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type not in ["group", "supergroup"]:
            await update.message.reply_text("این دستور فقط توی گروه‌ها کار می‌کند.")
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
            await update.message.reply_text("کسی از بچه‌ها آنلاین نیست 😴")
        else:
            msg = "🎮 اعضای آنلاین گروه:\\n\\n" + "\\n".join(online)
            await update.message.reply_text(msg)

    async def set_deals_topic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type not in ["supergroup"]:
            await update.message.reply_text("این دستور فقط توی سوپرگروه‌ها کار می‌کند.")
            return

        if not context.args:
            await update.message.reply_text("لطفاً آیدی تاپیک را وارد کنید. مثال:\\n/setdeals 123456")
            return

        topic_id = context.args[0]
        group_id = str(update.effective_chat.id)
        self.db.set_auto_post_target(group_id, topic_id, "deals")
        await update.message.reply_text(f"✅ ذخیره شد! هر روز تخفیف‌ها در تاپیک {topic_id} ارسال می‌شوند.")

    async def post_mock_deals(self):
        while True:
            targets = self.db.get_post_targets_by_purpose("deals")
            for group_id, topic_id in targets:
                try:
                    text = "🔥 تخفیف‌های امروز Steam:\n\n"
                    for i in range(1, 11):
                        text += f"{i}. Game {{i}} - {{random.randint(40,90)}}% Off\\n"
                    text += "\\n🎮 ادامه دارد..."
                    await self.bot.send_message(
                        chat_id=group_id,
                        message_thread_id=int(topic_id),
                        text=text
                    )
                except Exception as e:
                    logging.error(f"خطا در ارسال تخفیف‌ها: {e}")
            await asyncio.sleep(86400)

    async def notify(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("ترکیب دستور نادرسته!\nمثال:\n/notify @username GameName [here]")
            return

        watcher_id = str(update.effective_user.id)
        target_username = args[0].lstrip("@")
        game_name = args[1]
        scope = "private"
        group_id = None

        # اگر آرگومان سوم "here" باشه، نوتیف در گروپ میره
        if len(args) == 3 and args[2].lower() == "here":
            if update.effective_chat.type not in ["group", "supergroup"]:
                await update.message.reply_text("برای ارسال در گروه باید این دستور را در گروه بفرستی.")
                return
            scope = "group"
            group_id = str(update.effective_chat.id)

        req_id = self.db.add_notify_request(watcher_id, target_username, game_name, scope, group_id)
        await update.message.reply_text(f"✅ درخواست نوتیف ذخیره شد (ID: {req_id}).")

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
            await update.message.reply_text("شما هیچ درخواست نوتیفی ندارید.")
            return

        text = "🔔 درخواست‌های نوتیف شما:\n"
        for row in rows:
            _id, target, game, scope, grp = row
            text += f"{_id}. @{target} plays {game} - {'در گروه '+grp if scope=='group' else 'پیام خصوصی'}\\n"
        await update.message.reply_text(text)

    async def remove_notif(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("مثال: /removenotif 5")
            return
        try:
            req_id = int(context.args[0])
            self.db.remove_notify_request(req_id)
            await update.message.reply_text("✅ درخواست نوتیف حذف شد.")
        except:
            await update.message.reply_text("خطا: نتوانستم درخواست را پیدا کنم یا حذف کنم.")

    async def check_notify_requests(self):
        await asyncio.sleep(10)  # небольшой Delay قبل از استارت ابزار
        while True:
            rows = self.db.get_all_notify_requests()
            for row in rows:
                _id, watcher_id, target_username, game_name, scope, grp = row
                # ابتدا از جدول users، steam_id معادل target_username را بگیر
                steam_id = self.db.get_user_by_username(target_username)
                if not steam_id:
                    continue
                try:
                    summary = self.steam_api.get_player_summary(steam_id)
                    current_game = summary.get("gameextrainfo", "")
                    if current_game and game_name.lower() in current_game.lower():
                        # ارسال پیام
                        if scope == "private":
                            await self.bot.send_message(chat_id=int(watcher_id),
                                                        text=f"🔔 @{target_username} هم اکنون در حال بازی {game_name} است!")
                        else:
                            await self.bot.send_message(chat_id=int(grp),
                                                        text=f"🔔 @{target_username} دارد {game_name} بازی می‌کند!")
                        # حذف درخواست (یک بار نوتیف)
                        self.db.remove_notify_request(_id)
                except:
                    continue

            await asyncio.sleep(300)  # هر 5 دقیقه بررسی کن

if __name__ == "__main__":
    load_dotenv()
    nest_asyncio.apply()
    app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
    bot = SteamBot(app)

    # Handler های دستورات قبلی
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(CommandHandler("steam", bot.steam))
    app.add_handler(CommandHandler("status", bot.status))
    app.add_handler(CommandHandler("online", bot.online_users))
    app.add_handler(CommandHandler("setdeals", bot.set_deals_topic))
    app.add_handler(CommandHandler("notify", bot.notify))
    app.add_handler(CommandHandler("mynotifs", bot.my_notifs))
    app.add_handler(CommandHandler("removenotif", bot.remove_notif))
    app.add_handler(CallbackQueryHandler(bot.button_handler))

    # تسک‌های پس‌زمینه
    asyncio.get_event_loop().create_task(bot.post_mock_deals())
    asyncio.get_event_loop().create_task(bot.check_notify_requests())

    print("🤖 SteamSyncBot داره گوش می‌دهد...")
    asyncio.get_event_loop().run_until_complete(app.run_polling())
