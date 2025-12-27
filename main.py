import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from dotenv import load_dotenv

from handlers.start import start_command
from handlers.callback_handler import handle_callback_query
from handlers.video_handlers import (
    merge_videos,
    extract_audio,
    trim_video,
    convert_video,
)
from handlers.audio_handlers import swap_audio, combine_video_audio
from handlers.media_handlers import (
    add_watermark,
    add_subtitle,
    compress_video,
    remove_stream,
    sync_subtitle,
    rename_file,
)
from handlers.file_handler import handle_files
from handlers.video_merge_file_handler import handle_merge_video_upload  # ✅ IMPORTANT

from utils.logger import setup_logging
from utils.file_manager import FileManager

load_dotenv()
setup_logging()
logger = logging.getLogger(__name__)

# Conversation states
(
    MERGE_VIDEOS,
    EXTRACT_AUDIO,
    TRIM_VIDEO,
    CONVERT_VIDEO,
    SWAP_AUDIO,
    COMBINE_MEDIA,
    ADD_WATERMARK,
    ADD_SUBTITLE,
    COMPRESS_VIDEO,
    REMOVE_STREAM,
    SYNC_SUBTITLE,
    RENAME_FILE,
) = range(12)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL not found")

app = FastAPI()
application = None


@app.on_event("startup")
async def on_startup():
    global application
    application = Application.builder().token(BOT_TOKEN).build()

    FileManager.create_temp_folder()

    # Commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    application.add_handler(CommandHandler("merge", lambda u, c: merge_videos(u, c, MERGE_VIDEOS)))
    application.add_handler(CommandHandler("extract", lambda u, c: extract_audio(u, c, EXTRACT_AUDIO)))
    application.add_handler(CommandHandler("trim", lambda u, c: trim_video(u, c, TRIM_VIDEO)))
    application.add_handler(CommandHandler("convert", lambda u, c: convert_video(u, c, CONVERT_VIDEO)))
    application.add_handler(CommandHandler("swap_audio", lambda u, c: swap_audio(u, c, SWAP_AUDIO)))
    application.add_handler(CommandHandler("combine", lambda u, c: combine_video_audio(u, c, COMBINE_MEDIA)))
    application.add_handler(CommandHandler("watermark", lambda u, c: add_watermark(u, c, ADD_WATERMARK)))
    application.add_handler(CommandHandler("subtitle", lambda u, c: add_subtitle(u, c, ADD_SUBTITLE)))
    application.add_handler(CommandHandler("compress", lambda u, c: compress_video(u, c, COMPRESS_VIDEO)))
    application.add_handler(CommandHandler("remove_stream", lambda u, c: remove_stream(u, c, REMOVE_STREAM)))
    application.add_handler(CommandHandler("sync_sub", lambda u, c: sync_subtitle(u, c, SYNC_SUBTITLE)))
    application.add_handler(CommandHandler("rename", lambda u, c: rename_file(u, c, RENAME_FILE)))

    # ✅ 1️⃣ MERGE VIDEO HANDLER — MUST COME FIRST
    application.add_handler(
        MessageHandler(filters.VIDEO, handle_merge_video_upload)
    )

    # ✅ 2️⃣ GENERIC FILE HANDLER — COMES AFTER
    application.add_handler(
        MessageHandler(filters.Document.ALL | filters.AUDIO, handle_files)
    )

    async def error_handler(update, context):
        logger.error("Exception while handling update", exc_info=context.error)
        if update and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ An unexpected error occurred. Please try again."
                )
            except:
                pass

    application.add_error_handler(error_handler)

    await application.initialize()
    await application.start()
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

    logger.info("✅ Bot started successfully")


@app.on_event("shutdown")
async def on_shutdown():
    await application.stop()
    await application.shutdown()
    logger.info("Bot stopped")


@app.post("/webhook")
async def telegram_webhook(request: Request):
    update = Update.de_json(await request.json(), application.bot)
    await application.process_update(update)
    return {"ok": True}


@app.get("/")
def health_check():
    return {"status": "ok", "service": "Video Merger Bot"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
