import logging
import os
from telegram import Update
from telegram.ext import ContextTypes
from utils.file_manager import FileManager
from utils.ffmpeg_processor import FFmpegProcessor
from handlers.media_processor import (
    process_extract, process_trim,
    process_convert, process_compress, process_remove_stream,
    process_swap_audio, process_combine, process_watermark,
    process_subtitle
)
from handlers.video_merge_processor import process_merge_video

logger = logging.getLogger(__name__)
file_manager = FileManager()
processor = FFmpegProcessor()


async def handle_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all file uploads and process based on operation."""
    try:
        operation = context.user_data.get("operation")

        # ✅ HARD STOP: merge videos must NOT be handled here
        if operation in ["merge", "merge_add"] and update.message.video:
            return

        if not operation:
            await update.message.reply_text(
                "❌ No operation selected. Use /merge, /extract, /trim, /convert, "
                "/compress, /swap_audio, /combine, /watermark, /subtitle, "
                "/remove_stream, /sync_sub, or /rename",
                reply_to_message_id=update.message.message_id
            )
            return

        # Get file
        file = update.message.document or update.message.video or update.message.audio
        if not file:
            return

        file_obj = await context.bot.get_file(file.file_id)
        filename = file.file_name or f"file_{file.file_id[:8]}"
        filepath = os.path.join(file_manager.TEMP_FOLDER, filename)

        file_manager.create_temp_folder()

        # 🟡 MERGE (fallback safety – should not normally hit)
        if operation in ["merge", "merge_add"]:
            await file_obj.download_to_drive(filepath)
            await process_merge_video(update, context, filepath)
            return

        # 🔵 ALL OTHER OPERATIONS
        await file_obj.download_to_drive(filepath)
        file_size = file_manager.get_file_size(filepath) / (1024 * 1024)

        await update.message.reply_text(
            f"📥 Downloaded: {filename} ({file_size:.2f} MB)",
            reply_to_message_id=update.message.message_id
        )

        if "files" not in context.user_data:
            context.user_data["files"] = []
        context.user_data["files"].append(filepath)

        if operation == "extract":
            await process_extract(update, context, filepath)
        elif operation == "trim":
            await process_trim(update, context, filepath)
        elif operation == "convert":
            await process_convert(update, context, filepath)
        elif operation == "compress":
            await process_compress(update, context, filepath)
        elif operation == "remove_stream":
            await process_remove_stream(update, context, filepath)
        elif operation == "swap_audio":
            await process_swap_audio(update, context, filepath)
        elif operation == "combine":
            await process_combine(update, context, filepath)
        elif operation == "watermark":
            await process_watermark(update, context, filepath)
        elif operation == "subtitle":
            await process_subtitle(update, context, filepath)

    except Exception as e:
        logger.error(f"Error handling file: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ Error: {str(e)}",
            reply_to_message_id=update.message.message_id
        )
