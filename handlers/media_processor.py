import logging
import os
from telegram import Update
from telegram.ext import ContextTypes
from utils.file_manager import FileManager
from utils.ffmpeg_processor import FFmpegProcessor
from utils.progress_tracker import ProgressTracker

logger = logging.getLogger(__name__)
file_manager = FileManager()
processor = FFmpegProcessor()

async def process_merge(update: Update, context: ContextTypes.DEFAULT_TYPE, filepath: str) -> None:
    """Handle video merge operation."""
    files = context.user_data.get("files", [])
    
    if len(files) < 2:
        await update.message.reply_text(
            f"📌 File 1 of 2 added. Send file 2 (or /start to cancel)",
            reply_to_message_id=update.message.message_id
        )
        return
    
    output_file = os.path.join(file_manager.TEMP_FOLDER, "merged_video.mp4")
    status_msg = await update.message.reply_text(
        "⏳ Starting merge...",
        reply_to_message_id=update.message.message_id
    )
    
    progress = ProgressTracker(
        update=update,
        context=context,
        status_msg=status_msg,
        operation="Merging"
    )
    
    success = processor.merge_videos(files, output_file, progress)
    
    if success:
        await progress.final_status(f"✅ Merged! Uploading...")
        file_size = file_manager.get_file_size(output_file) / (1024*1024)
        with open(output_file, 'rb') as f:
            await context.bot.send_document(
                update.effective_chat.id,
                document=f,
                caption=f"📹 Merged Video\n📊 Size: {file_size:.2f} MB",
                reply_to_message_id=update.message.message_id
            )
        await update.message.reply_text(
            "✅ Merge completed!",
            reply_to_message_id=update.message.message_id
        )
        file_manager.delete_file(output_file)
    else:
        await update.message.reply_text(
            "❌ Merge failed",
            reply_to_message_id=update.message.message_id
        )
    
    context.user_data["operation"] = None
    context.user_data["files"] = []

async def process_extract(update: Update, context: ContextTypes.DEFAULT_TYPE, filepath: str) -> None:
    """Handle audio extraction."""
    output_file = os.path.join(file_manager.TEMP_FOLDER, "extracted_audio.mp3")
    status_msg = await update.message.reply_text(
        "⏳ Extracting audio...",
        reply_to_message_id=update.message.message_id
    )
    
    progress = ProgressTracker(
        update=update,
        context=context,
        status_msg=status_msg,
        operation="Extracting"
    )
    
    success = processor.extract_audio(filepath, output_file, progress)
    
    if success:
        await progress.final_status(f"✅ Extracted! Uploading...")
        file_size = file_manager.get_file_size(output_file) / (1024*1024)
        with open(output_file, 'rb') as f:
            await context.bot.send_document(
                update.effective_chat.id,
                document=f,
                caption=f"🎵 Extracted Audio\n📊 Size: {file_size:.2f} MB",
                reply_to_message_id=update.message.message_id
            )
        await update.message.reply_text(
            "✅ Extraction completed!",
            reply_to_message_id=update.message.message_id
        )
        file_manager.delete_file(output_file)
    else:
        await update.message.reply_text(
            "❌ Extraction failed",
            reply_to_message_id=update.message.message_id
        )
    
    context.user_data["operation"] = None
    context.user_data["files"] = []

async def process_trim(update: Update, context: ContextTypes.DEFAULT_TYPE, filepath: str) -> None:
    """Handle video trimming."""
    await update.message.reply_text(
        "⏱️ Enter start time (HH:MM:SS)",
        reply_to_message_id=update.message.message_id
    )
    context.user_data["trim_file"] = filepath
    context.user_data["trim_step"] = "start"

async def process_convert(update: Update, context: ContextTypes.DEFAULT_TYPE, filepath: str) -> None:
    """Handle video conversion."""
    await update.message.reply_text(
        "🔄 Enter output format (mp4, mkv, avi, mov, webm, flv)",
        reply_to_message_id=update.message.message_id
    )
    context.user_data["convert_file"] = filepath

async def process_compress(update: Update, context: ContextTypes.DEFAULT_TYPE, filepath: str) -> None:
    """Handle video compression."""
    output_file = os.path.join(file_manager.TEMP_FOLDER, "compressed_video.mp4")
    status_msg = await update.message.reply_text(
        "⏳ Compressing video...",
        reply_to_message_id=update.message.message_id
    )
    
    progress = ProgressTracker(
        update=update,
        context=context,
        status_msg=status_msg,
        operation="Compressing"
    )
    
    success = processor.compress_video(filepath, crf=28, output_path=output_file, progress=progress)
    
    if success:
        await progress.final_status(f"✅ Compressed! Uploading...")
        original_size = file_manager.get_file_size(filepath) / (1024*1024)
        compressed_size = file_manager.get_file_size(output_file) / (1024*1024)
        reduction = ((original_size - compressed_size) / original_size * 100) if original_size > 0 else 0
        
        with open(output_file, 'rb') as f:
            await context.bot.send_document(
                update.effective_chat.id,
                document=f,
                caption=f"📹 Compressed Video\n📊 Size: {compressed_size:.2f} MB (↓ {reduction:.1f}%)",
                reply_to_message_id=update.message.message_id
            )
        await update.message.reply_text(
            "✅ Compression completed!",
            reply_to_message_id=update.message.message_id
        )
        file_manager.delete_file(output_file)
    else:
        await update.message.reply_text(
            "❌ Compression failed",
            reply_to_message_id=update.message.message_id
        )
    
    context.user_data["operation"] = None
    context.user_data["files"] = []

async def process_remove_stream(update: Update, context: ContextTypes.DEFAULT_TYPE, filepath: str) -> None:
    """Handle stream removal."""
    await update.message.reply_text(
        "🎬 Remove audio or video? (Type: audio or video)",
        reply_to_message_id=update.message.message_id
    )
    context.user_data["remove_file"] = filepath

async def process_swap_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, filepath: str) -> None:
    """Handle audio swap."""
    files = context.user_data.get("files", [])
    if len(files) < 2:
        await update.message.reply_text(
            "📌 Video added. Send audio file",
            reply_to_message_id=update.message.message_id
        )
        return
    
    video_file = files[0]
    audio_file = files[1]
    output_file = os.path.join(file_manager.TEMP_FOLDER, "swapped_audio.mp4")
    status_msg = await update.message.reply_text(
        "⏳ Swapping audio...",
        reply_to_message_id=update.message.message_id
    )
    
    progress = ProgressTracker(
        update=update,
        context=context,
        status_msg=status_msg,
        operation="Swapping"
    )
    
    success = processor.combine_video_audio(video_file, audio_file, output_file, progress)
    
    if success:
        await progress.final_status(f"✅ Swapped! Uploading...")
        file_size = file_manager.get_file_size(output_file) / (1024*1024)
        with open(output_file, 'rb') as f:
            await context.bot.send_document(
                update.effective_chat.id,
                document=f,
                caption=f"📹 Video with New Audio\n📊 Size: {file_size:.2f} MB",
                reply_to_message_id=update.message.message_id
            )
        await update.message.reply_text(
            "✅ Swap completed!",
            reply_to_message_id=update.message.message_id
        )
        file_manager.delete_file(output_file)
    else:
        await update.message.reply_text(
            "❌ Swap failed",
            reply_to_message_id=update.message.message_id
        )
    
    context.user_data["operation"] = None
    context.user_data["files"] = []

async def process_combine(update: Update, context: ContextTypes.DEFAULT_TYPE, filepath: str) -> None:
    """Handle video + audio combine."""
    files = context.user_data.get("files", [])
    if len(files) < 2:
        await update.message.reply_text(
            "📌 File 1 added. Send file 2 (video + audio)",
            reply_to_message_id=update.message.message_id
        )
        return
    
    video_file = files[0]
    audio_file = files[1]
    output_file = os.path.join(file_manager.TEMP_FOLDER, "combined.mp4")
    status_msg = await update.message.reply_text(
        "⏳ Combining files...",
        reply_to_message_id=update.message.message_id
    )
    
    progress = ProgressTracker(
        update=update,
        context=context,
        status_msg=status_msg,
        operation="Combining"
    )
    
    success = processor.combine_video_audio(video_file, audio_file, output_file, progress)
    
    if success:
        await progress.final_status(f"✅ Combined! Uploading...")
        file_size = file_manager.get_file_size(output_file) / (1024*1024)
        with open(output_file, 'rb') as f:
            await context.bot.send_document(
                update.effective_chat.id,
                document=f,
                caption=f"📹 Combined Media\n📊 Size: {file_size:.2f} MB",
                reply_to_message_id=update.message.message_id
            )
        await update.message.reply_text(
            "✅ Combine completed!",
            reply_to_message_id=update.message.message_id
        )
        file_manager.delete_file(output_file)
    else:
        await update.message.reply_text(
            "❌ Combine failed",
            reply_to_message_id=update.message.message_id
        )
    
    context.user_data["operation"] = None
    context.user_data["files"] = []

async def process_watermark(update: Update, context: ContextTypes.DEFAULT_TYPE, filepath: str) -> None:
    """Handle watermark addition."""
    await update.message.reply_text(
        "🖼️ Send watermark image (PNG recommended)",
        reply_to_message_id=update.message.message_id
    )
    context.user_data["watermark_video"] = filepath

async def process_subtitle(update: Update, context: ContextTypes.DEFAULT_TYPE, filepath: str) -> None:
    """Handle subtitle addition."""
    await update.message.reply_text(
        "📄 Send subtitle file (.srt, .ass, .vtt)",
        reply_to_message_id=update.message.message_id
    )
    context.user_data["subtitle_video"] = filepath
