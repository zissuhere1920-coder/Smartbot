import logging
import re
import os
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# =============================================
# CONFIG
# =============================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8821147793:AAHwxqjRKKO89Q1umA7y-vioYYz8BCGlLq8")
ADMIN_ID = 8687306834
MESSAGE = "I love u professor 💓 🎀"
# =============================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

active_groups = []
custom_timers = {}

def parse_time(text):
    text = text.lower().strip()
    match = re.match(r'(\d+)([smhd])', text)
    if not match:
        return None
    num = int(match.group(1))
    unit = match.group(2)
    if unit == 's': return num
    elif unit == 'm': return num * 60
    elif unit == 'h': return num * 60 * 60
    elif unit == 'd': return num * 24 * 60 * 60
    return None

def format_time(seconds):
    if seconds < 60: return f"{seconds} seconds"
    elif seconds < 3600: return f"{seconds//60} minutes"
    elif seconds < 86400: return f"{seconds//3600} hours"
    else: return f"{seconds//86400} days"

async def send_to_all_groups(context, custom_message=None, chat_id=None):
    msg = custom_message if custom_message else MESSAGE
    if chat_id:
        try:
            await context.bot.send_message(chat_id=chat_id, text=msg)
            logger.info(f"✅ Custom sent to {chat_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed {chat_id}: {e}")
            return False
    if not active_groups:
        return
    for gid in active_groups:
        try:
            await context.bot.send_message(chat_id=gid, text=msg)
            logger.info(f"✅ Sent to {gid}")
        except Exception as e:
            logger.error(f"❌ Failed {gid}: {e}")

async def check_custom_timers(context):
    now = datetime.now()
    to_remove = []
    for chat_id, data in custom_timers.items():
        if now >= data["time"]:
            await send_to_all_groups(context, custom_message=data["message"], chat_id=chat_id)
            to_remove.append(chat_id)
    for chat_id in to_remove:
        del custom_timers[chat_id]

async def handle_dm(update, context):
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    text = update.message.text.strip()
    
    if chat_type != "private":
        return
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return
    
    if text.startswith("/addgroup"):
        parts = text.split(" ", 1)
        if len(parts) < 2:
            await update.message.reply_text("❌ Usage: /addgroup group_id")
            return
        try:
            gid = int(parts[1])
            if gid not in active_groups:
                active_groups.append(gid)
                await update.message.reply_text(f"✅ Group {gid} added manually!")
            else:
                await update.message.reply_text("ℹ️ Group already in list.")
        except ValueError:
            await update.message.reply_text("❌ Invalid Group ID. Must be a number.")
        return
    
    if text.startswith("/removegroup"):
        parts = text.split(" ", 1)
        if len(parts) < 2:
            await update.message.reply_text("❌ Usage: /removegroup group_id")
            return
        try:
            gid = int(parts[1])
            if gid in active_groups:
                active_groups.remove(gid)
                await update.message.reply_text(f"✅ Group {gid} removed!")
            else:
                await update.message.reply_text("ℹ️ Group not in list.")
        except ValueError:
            await update.message.reply_text("❌ Invalid Group ID.")
        return
    
    if text.startswith("/send"):
        parts = text.split(" ", 1)
        if len(parts) < 2:
            await update.message.reply_text("❌ Usage: /send Your message")
            return
        await update.message.reply_text(f"⏳ Sending...")
        await send_to_all_groups(context, custom_message=parts[1])
        await update.message.reply_text("✅ Sent to all groups!")
        return
    
    if text.startswith("/timer"):
        parts = text.split(" ", 2)
        if len(parts) < 3:
            await update.message.reply_text("❌ Usage: /timer 5h Your message")
            return
        seconds = parse_time(parts[1])
        if not seconds:
            await update.message.reply_text("❌ Invalid time! Use: 5h, 10m, 30s, 2d")
            return
        if not active_groups:
            await update.message.reply_text("❌ No active groups!")
            return
        timer_time = datetime.now() + timedelta(seconds=seconds)
        for chat_id in active_groups:
            custom_timers[chat_id] = {"time": timer_time, "message": parts[2]}
        await update.message.reply_text(f"✅ Timer set! Will send in {format_time(seconds)}")
        return
    
    if text == "/groups":
        if active_groups:
            await update.message.reply_text(f"📊 Groups ({len(active_groups)}):\n" + "\n".join(f"• {gid}" for gid in active_groups))
        else:
            await update.message.reply_text("❌ No active groups.")
        return
    
    if text == "/timerlist":
        if not custom_timers:
            await update.message.reply_text("⏰ No active timers.")
            return
        msg = "⏰ Active Timers:\n\n"
        for chat_id, data in custom_timers.items():
            remaining = (data["time"] - datetime.now()).total_seconds()
            if remaining < 0: remaining = 0
            msg += f"• Group {chat_id}: {format_time(int(remaining))} left\n  '{data['message']}'\n\n"
        await update.message.reply_text(msg)
        return
    
    if text == "/cancel":
        if custom_timers:
            custom_timers.clear()
            await update.message.reply_text("✅ All timers cancelled!")
        else:
            await update.message.reply_text("⏰ No active timers.")
        return
    
    if text == "/help":
        await update.message.reply_text(
            "📖 *Commands*\n\n"
            "/send msg - Send to all groups\n"
            "/timer 5h msg - Set timer\n"
            "/addgroup 123456789 - Add group manually\n"
            "/removegroup 123456789 - Remove group\n"
            "/groups - List groups\n"
            "/timerlist - Active timers\n"
            "/cancel - Cancel all timers\n\n"
            "⏰ 5h, 10m, 30s, 2d",
            parse_mode="Markdown"
        )
        return
    
    await update.message.reply_text("❌ Unknown. Type /help")

async def auto_5hour_message(context):
    if not active_groups:
        return
    for chat_id in active_groups:
        try:
            await context.bot.send_message(chat_id=chat_id, text=MESSAGE)
            logger.info(f"✅ Auto sent to {chat_id}")
        except Exception as e:
            logger.error(f"❌ Auto failed {chat_id}: {e}")

async def start(update, context):
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        if chat.id not in active_groups:
            active_groups.append(chat.id)
        await update.message.reply_text("✅ Active! DM mein /help")

async def on_join(update, context):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            chat_id = update.effective_chat.id
            if chat_id not in active_groups:
                active_groups.append(chat_id)
            await update.message.reply_text("✅ Thanks! DM mein /help")
            break

async def on_leave(update, context):
    for member in update.message.left_chat_member:
        if member.id == context.bot.id:
            chat_id = update.effective_chat.id
            if chat_id in active_groups:
                active_groups.remove(chat_id)
            if chat_id in custom_timers:
                del custom_timers[chat_id]
            break

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_dm))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_join))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, on_leave))
    
    job = app.job_queue
    if job:
        job.run_repeating(auto_5hour_message, interval=5*60*60, first=10)
        job.run_repeating(check_custom_timers, interval=10, first=5)
    
    logger.info("🤖 Smart Bot chal raha hai...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
