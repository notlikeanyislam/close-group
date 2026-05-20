"""
Telegram Chat Lock Bot — Render.com (webhook mode)
===================================================
Commands (admins only):
  /close  — Lock the chat (members can't send messages)
  /open   — Unlock the chat (restore normal permissions)
  /status — Show whether the chat is locked or open
"""

import os
import asyncio
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
    can_send_polls=False,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
    can_change_info=False,
    can_invite_users=True,
    can_pin_messages=False,
    can_react_to_messages=True,
)

CLOSED_PERMISSIONS = ChatPermissions(
    can_invite_users=True,
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
    can_react_to_messages=True,

)

# ── Helpers ───────────────────────────────────────────────────────────────────

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    admins = await context.bot.get_chat_administrators(chat_id)
    return any(admin.user.id == user_id for admin in admins)

async def not_admin_reply(update: Update) -> None:
    await update.message.reply_text("⛔ يمكن للمسؤولين فقط استخدام هذا الأمر.")

# ── Handlers ──────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 أهلاً! أنا روبوت اغلاق المحادثة الجماعية.\n\n"
        "أضفني إلى مجموعة، واجعلني مسؤولاً بإذن 'تقييد الأعضاء'، ثم استخدم:\n\n"
        "🔒 /close — اغلاق المحادثة (لا يمكن للأعضاء إرسال الرسائل)\n"
        "🔓 /open — فتح المحادثة\n"
        "📊 /status — تحقق مما إذا كانت المحادثة مفتوحة أم مغلقة\n\n"
        "تعمل هذه الأوامر داخل المجموعة فقط."
    )

async def group_only(update: Update) -> bool:
    if update.effective_chat.type == "private":
        await update.message.reply_text("⚠️ هذا الأمر يعمل فقط داخل المجموعة.")
        return False
    return True

async def close_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await group_only(update):
        return
    if not await is_admin(update, context):
        await not_admin_reply(update)
        return
    try:
        await context.bot.set_chat_permissions(update.effective_chat.id, CLOSED_PERMISSIONS)
        await update.message.reply_text("🔒 تم إغلاق المحادثة. استخدم /open لإعادة الفتح.")
        logger.info("Chat %s closed by %s", update.effective_chat.id, update.effective_user.id)
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {e}")

async def open_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await group_only(update):
        return
    if not await is_admin(update, context):
        await not_admin_reply(update)
        return
    try:
        await context.bot.set_chat_permissions(update.effective_chat.id, OPEN_PERMISSIONS)
        await update.message.reply_text("🔓 تم فتح المحادثة. يمكن للأعضاء إرسال الرسائل مرة أخرى!")
        logger.info("Chat %s opened by %s", update.effective_chat.id, update.effective_user.id)
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {e}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await group_only(update):
        return
    try:
        perms = (await context.bot.get_chat(update.effective_chat.id)).permissions
        state = "🔓 OPEN" if (perms and perms.can_send_messages) else "🔒 مغلق"
        await update.message.reply_text(f"الدردشة حاليا {state}.")
    except Exception as e:
        await update.message.reply_text(f"❌ لم يتمكن من عرض الحالة: {e}")

# ── Entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("close",  close_chat))
    app.add_handler(CommandHandler("open",   open_chat))
    app.add_handler(CommandHandler("status", status))


    async with app:
        await app.updater.start_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="webhook",
            webhook_url=f"{WEBHOOK_URL}/webhook",
        )
        await app.start()
        logger.info("Bot is live and listening …")
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
