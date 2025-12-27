"""Callback handlers for video merge operations."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.video_merge_manager import get_or_create_queue, show_merge_menu

logger = logging.getLogger(__name__)


async def handle_merge_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Main handler for video merge callbacks."""
    query = update.callback_query
    callback_data = query.data
    user_id = update.effective_user.id
    
    try:
        if callback_data == "video_merge":
            await show_merge_menu(update, context, edit=True)
        
        elif callback_data == "merge_menu":
            await show_merge_menu(update, context, edit=True)
        
        elif callback_data == "merge_add_video":
            context.user_data["operation"] = "merge_add"
            context.user_data["merge_mode"] = True  # Flag to indicate we're in merge mode
            
            await query.edit_message_text(
                text="📹 Send video file to add to queue\n\n"
                     "Supported formats: mp4, mkv, mov, webm\n"
                     "Max file size: 4GB\n\n"
                     "Type /start to cancel",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back", callback_data="merge_menu")
                ]])
            )
        
        elif callback_data == "merge_clear":
            queue = get_or_create_queue(user_id)
            queue.clear_all()
            await query.answer("Queue cleared", show_alert=False)
            await show_merge_menu(update, context, edit=True)
        
        elif callback_data == "merge_confirm":
            queue = get_or_create_queue(user_id)
            if len(queue.videos) < 2:
                await query.answer("Need at least 2 videos!", show_alert=True)
                return
            
            from handlers.video_merge_processor import execute_smart_merge
            await execute_smart_merge(update, context)
        
        elif callback_data == "merge_cancel":
            await show_merge_menu(update, context, edit=True)
        
    except Exception as e:
        logger.error(f"Error in merge callback: {e}")
        await query.answer(f"Error: {str(e)}", show_alert=True)
