"""
Telegram Chat Lock Bot — Render.com (webhook mode)
===================================================
Commands (admins only):
  /close  — Lock the chat (members can't send messages)
  /open   — Unlock the chat (restore normal permissions)
  /status — Show whether the chat is locked or open
"""

import os
import logging
from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ── Config (set these as Environment Variables on Render) ─────────────────────
BOT_TOKEN   = os.environ["BOT_TOKEN"]          # your BotFather token
WEBHOOK_URL = os.environ["WEBHOOK_URL"]        # e.g. https://your-app.onrender.com
PORT        = int(os.environ.get("PORT", 8443))
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Permissions ───────────────────────────────────────────────────────────────

OPEN_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_audios=True,
    can_send_documents=True,
    can_send_photos=True,
    can_send_videos=True,
    can_send_video_notes=True,
    can_send_voice_notes=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
    can_change_info=False,
    can_invite_users=True,
    can_pin_messages=False,
)

CLOSED_PERMISSIONS = ChatPermissions(
    can_send_messages=False,
    can_send_audios=False,
    can_send_documents=False,
    can_send_photos=False,
    can_send_videos=False,
    can_send_video_notes=False,
    can_send_voice_notes=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    admins = await context.bot.get_chat_administrators(chat_id)
    return any(admin.user.id == user_id for admin in admins)

async def not_admin_reply(update: Update) -> None:
    await update.message.reply_text("⛔ Only admins can use this command.")

# ── Handlers ──────────────────────────────────────────────────────────────────

async def close_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin(update, context):
        await not_admin_reply(update)
        return
    try:
        await context.bot.set_chat_permissions(update.effective_chat.id, CLOSED_PERMISSIONS)
        await update.message.reply_text("🔒 Chat closed. Use /open to reopen.")
        logger.info("Chat %s closed by %s", update.effective_chat.id, update.effective_user.id)
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {e}")

async def open_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin(update, context):
        await not_admin_reply(update)
        return
    try:
        await context.bot.set_chat_permissions(update.effective_chat.id, OPEN_PERMISSIONS)
        await update.message.reply_text("🔓 Chat opened. Members can send messages again.")
        logger.info("Chat %s opened by %s", update.effective_chat.id, update.effective_user.id)
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {e}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        perms = (await context.bot.get_chat(update.effective_chat.id)).permissions
        state = "🔓 OPEN" if (perms and perms.can_send_messages) else "🔒 CLOSED"
        await update.message.reply_text(f"Chat is currently {state}.")
    except Exception as e:
        await update.message.reply_text(f"❌ Could not fetch status: {e}")

# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("close",  close_chat))
    app.add_handler(CommandHandler("open",   open_chat))
    app.add_handler(CommandHandler("status", status))

    logger.info("Starting webhook on port %d …", PORT)
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{WEBHOOK_URL}/webhook",
        url_path="/webhook",
    )

if __name__ == "__main__":
    main()
