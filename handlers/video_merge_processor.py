"""Process and execute video merges with real-time progress."""
import logging
import os
import asyncio
import time
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.file_manager import FileManager
from utils.ffmpeg_processor import FFmpegProcessor
from handlers.video_merge_manager import get_or_create_queue

logger = logging.getLogger(__name__)
file_manager = FileManager()
processor = FFmpegProcessor()


async def process_merge_video(update: Update, context: ContextTypes.DEFAULT_TYPE, filepath: str) -> None:
    """Handle video addition to merge queue - ONLY updates queue message, no extra messages."""
    try:
        user_id = update.effective_user.id
        queue = get_or_create_queue(user_id)
        
        if not os.path.exists(filepath):
            await update.message.reply_text(
                "❌ File not found",
                reply_to_message_id=update.message.message_id
            )
            context.user_data["operation"] = None
            return
        
        # Extract metadata
        from handlers.video_merge_manager import VideoMetadata
        
        try:
            metadata = VideoMetadata(
                msg_id=update.message.message_id,
                file_name=os.path.basename(filepath),
                file_path=filepath
            )
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            await update.message.reply_text(
                f"❌ Cannot read video file: {str(e)}"
            )
            file_manager.delete_file(filepath)
            context.user_data["operation"] = None
            return
        
        # Add to queue
        if queue.add_video(metadata):
            keyboard = [
                [InlineKeyboardButton("➕ Add More", callback_data="merge_add_video")],
                [
                    InlineKeyboardButton("▶️ Merge", callback_data="merge_confirm"),
                    InlineKeyboardButton("❌ Cancel", callback_data="merge_clear"),
                    InlineKeyboardButton("🔙 Back", callback_data="merge_menu"),
                ],
            ]
            
            queue_text = f"✅ Video added!\n\n{queue.format_queue_message()}\n\nAdd more videos or start merge?"
            
            if len(queue.videos) == 1:
                msg = await update.message.reply_text(
                    text=queue_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                queue.queue_message_id = msg.message_id
            else:
                if queue.queue_message_id:
                    try:
                        await context.bot.delete_message(
                            chat_id=user_id,
                            message_id=queue.queue_message_id
                        )
                    except Exception as e:
                        logger.warning(f"Could not delete old message: {e}")
                
                # Send fresh message
                msg = await update.message.reply_text(
                    text=queue_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                queue.queue_message_id = msg.message_id
        else:
            await update.message.reply_text(
                "❌ Cannot add video to queue\n"
                "Max 20 videos per merge"
            )
        
        context.user_data["operation"] = None
    
    except Exception as e:
        logger.error(f"Error processing merge video: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")
        context.user_data["operation"] = None


async def execute_smart_merge(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Execute actual merge using FFmpeg concat (FAST - no re-encoding by default)."""
    user_id = update.effective_user.id
    query = update.callback_query
    queue = get_or_create_queue(user_id)
    
    if len(queue.videos) < 2:
        await query.answer("Need at least 2 videos!", show_alert=True)
        return
    
    status_msg = None
    concat_file = None
    output_file = None
    
    try:
        start_time = time.time()
        
        # This prevents "Message to edit not found" errors
        try:
            status_msg = await query.edit_message_text(
                text="🔀 MERGING VIDEOS\n━━━━━━━━━━━━━━━━━━\n\n"
                     "⏳ Stage 1: Preparing Files\n"
                     "📊 Progress: 0%"
            )
        except Exception as e:
            logger.error(f"Could not edit message: {e}")
            # Fallback: create new message if edit fails
            status_msg = await context.bot.send_message(
                chat_id=user_id,
                text="🔀 MERGING VIDEOS\n━━━━━━━━━━━━━━━━━━\n\n"
                     "⏳ Stage 1: Preparing Files\n"
                     "📊 Progress: 0%"
            )
        
        await asyncio.sleep(0.5)
        
        # Stage 1: Create concat file
        concat_file = os.path.join(file_manager.TEMP_FOLDER, "concat_list.txt")
        with open(concat_file, "w", encoding="utf-8") as f:
            for video in queue.videos:
                abs_path = os.path.abspath(video.file_path).replace("\\", "/")
                f.write(f"file '{abs_path}'\n")
        
        total_size_mb = sum(os.path.getsize(v.file_path) / (1024 * 1024) for v in queue.videos)
        total_duration = queue.get_total_duration()
        output_file = os.path.join(file_manager.TEMP_FOLDER, "merged_video.mp4")
        
        try:
            await status_msg.edit_text(
                text="🔀 MERGING VIDEOS\n━━━━━━━━━━━━━━━━━━\n\n"
                     "✅ Stage 1: Files Ready\n"
                     "⏳ Stage 2: Merging (FAST - Stream Copy)\n\n"
                     "📊 Progress: 5%\n"
                     f"📁 Total Size: {total_size_mb:.2f}MB\n"
                     "⏱️ ETA: Calculating..."
            )
        except Exception as e:
            logger.warning(f"Could not update status: {e}")
        
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel", "error",
            "-f", "concat",
            "-safe", "0",
            "-fflags", "+genpts",
            "-i", concat_file,
            "-map", "0:v:0",
            "-map", "0:a?",
            "-c", "copy",
            "-movflags", "+faststart",
            output_file
        ]
        
        # Run FFmpeg in thread to avoid blocking async event loop
        def run_ffmpeg():
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600
            )
        
        process_result = await asyncio.to_thread(run_ffmpeg)
        
        # Check if merge succeeded
        if process_result.returncode != 0:
            logger.error(f"FFmpeg merge failed with return code: {process_result.returncode}")
            logger.error(f"FFmpeg stderr: {process_result.stderr}")
            
            try:
                await status_msg.edit_text(
                    text="❌ MERGE FAILED\n━━━━━━━━━━━━━━━━━━\n\n"
                         "Error: Check if videos have compatible formats.\n"
                         "Try converting to same format first."
                )
            except:
                pass
            
            # Cleanup
            try:
                if concat_file and os.path.exists(concat_file):
                    os.remove(concat_file)
                if output_file and os.path.exists(output_file):
                    os.remove(output_file)
            except:
                pass
            return
        
        if not os.path.exists(output_file) or os.path.getsize(output_file) < 1024:
            logger.error(f"Output file missing or too small: {output_file}")
            try:
                await status_msg.edit_text(
                    text="❌ MERGE FAILED\n━━━━━━━━━━━━━━━━━━\n\n"
                         "Error: Output file corrupted or empty.\n"
                         "Ensure videos are valid MP4 files."
                )
            except:
                pass
            
            try:
                if output_file and os.path.exists(output_file):
                    os.remove(output_file)
                if concat_file and os.path.exists(concat_file):
                    os.remove(concat_file)
            except:
                pass
            return
        
        file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
        
        try:
            await status_msg.edit_text(
                text="🔀 MERGING VIDEOS\n━━━━━━━━━━━━━━━━━━\n\n"
                     "✅ Stage 1: Files Ready\n"
                     "✅ Stage 2: Merge Complete\n"
                     "⏳ Stage 3: Uploading to Telegram\n\n"
                     "📊 Progress: 95%"
            )
        except:
            pass
        
        # Upload with progress tracking
        upload_start = time.time()
        with open(output_file, 'rb') as f:
            await context.bot.send_document(
                chat_id=user_id,
                document=f,
                caption=f"✅ MERGE COMPLETE!\n━━━━━━━━━━━━━━━━━━\n\n"
                        f"📹 merged_video.mp4\n"
                        f"📁 Size: {file_size_mb:.2f}MB\n"
                        f"⏱️ Duration: {queue._format_duration(queue.get_total_duration())}\n\n"
                        f"⏲️ Processing time: {int(time.time() - start_time)}s"
            )
        
        upload_time = time.time() - upload_start
        upload_speed = (file_size_mb / upload_time) if upload_time > 0 else 0
        
        try:
            await status_msg.delete()
        except:
            pass
        
        # Cleanup
        queue.clear_all()
        try:
            if output_file and os.path.exists(output_file):
                os.remove(output_file)
            if concat_file and os.path.exists(concat_file):
                os.remove(concat_file)
        except:
            pass
    
    except Exception as e:
        logger.error(f"Error executing merge: {e}", exc_info=True)
        try:
            if status_msg:
                await status_msg.edit_text(f"❌ Merge error: {str(e)}")
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"❌ Merge error: {str(e)}"
                )
        except Exception as edit_error:
            logger.error(f"Could not send error message: {edit_error}")
        
        # Cleanup on error
        try:
            if concat_file and os.path.exists(concat_file):
                os.remove(concat_file)
            if output_file and os.path.exists(output_file):
                os.remove(output_file)
        except:
            pass
