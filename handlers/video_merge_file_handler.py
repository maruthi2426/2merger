"""Handle file uploads for video merge operations."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.file_manager import FileManager
from handlers.video_merge_manager import (
    get_or_create_queue,
    VideoMetadata,
    show_merge_menu,
)

logger = logging.getLogger(__name__)
file_manager = FileManager()


async def handle_merge_video_upload(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    file_path: str
) -> None:
    """Handle video file upload for merge queue."""
    user_id = update.effective_user.id
    queue = get_or_create_queue(user_id)

    try:
        file_info = update.message.video or update.message.document
        file_name = file_info.file_name or f"video_{len(queue.videos) + 1}.mp4"

        metadata = VideoMetadata(
            msg_id=update.message.message_id,
            file_name=file_name,
            file_path=file_path
        )

        # Validate video
        if metadata.duration == 0:
            await update.message.reply_text(
                "❌ Invalid video file or unable to detect duration.\n\n"
                "Please send a valid video file.",
                reply_to_message_id=update.message.message_id
            )
            file_manager.delete_file(file_path)
            return

        # Add to queue
        if queue.add_video(metadata):

            # Inline buttons instead of separate menu message
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add More", callback_data="merge_menu")],
                [InlineKeyboardButton("✅ Start Merge", callback_data="merge_start_now")],
                [InlineKeyboardButton("🗑 Clear Queue", callback_data="merge_clear")]
            ])

            # ✅ SINGLE reply attached to the video
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    f"✅ Video {len(queue.videos)} added!\n\n"
                    f"📁 File: {file_name}\n"
                    f"⏱ Duration: {VideoMetadata._format_duration(metadata.duration)}\n"
                    f"📊 Size: {metadata.size / (1024*1024):.1f} MB\n"
                    f"🎬 Resolution: {metadata.resolution[0]}x{metadata.resolution[1]}\n\n"
                    f"📂 Queue: {len(queue.videos)} videos\n"
                    f"💾 Total: {queue.get_total_size():.2f} GB"
                ),
                reply_to_message_id=update.message.message_id,
                reply_markup=keyboard
            )

            # 🔕 DO NOT send menu again
            # show_merge_menu is kept but NOT called here

        else:
            await update.message.reply_text(
                "❌ Could not add video to queue.\n"
                "Check file validity or queue size limit (max 20).",
                reply_to_message_id=update.message.message_id
            )
            file_manager.delete_file(file_path)

    except Exception as e:
        logger.error(f"Error handling merge video upload: {e}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}",
            reply_to_message_id=update.message.message_id
        )
        file_manager.delete_file(file_path)
