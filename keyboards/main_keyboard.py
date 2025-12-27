"""Inline keyboard builders for the bot."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_keyboard() -> InlineKeyboardMarkup:
    """
    Create main menu keyboard with categories.
    Added close button to main menu (no back button on start page)
    
    Returns:
        InlineKeyboardMarkup: Main menu with Video Tools, Audio Tools, Upload Mode, and Close button
    """
    keyboard = [
        # Row 1: Video Tools and Audio Tools
        [
            InlineKeyboardButton("🎬 Video Tools", callback_data="menu_video_tools"),
            InlineKeyboardButton("🎵 Audio Tools", callback_data="menu_audio_tools"),
        ],
        # Row 2: Upload Mode and Extra Settings
        [
            InlineKeyboardButton("📤 Upload Mode", callback_data="menu_upload_mode"),
            InlineKeyboardButton("⚙️ Extra Settings", callback_data="menu_settings"),
        ],
        # Row 3: Close button only (no back on start page)
        [
            InlineKeyboardButton("❌ Close", callback_data="close"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_video_tools_keyboard() -> InlineKeyboardMarkup:
    """
    Create video tools submenu keyboard.
    Added close button alongside back button
    
    Returns:
        InlineKeyboardMarkup: Video tools with all operations and back/close buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("➕ Video + Video", callback_data="video_merge"),
            InlineKeyboardButton("🎬 Video + Audio", callback_data="video_swap_audio"),
        ],
        [
            InlineKeyboardButton("📝 Video + Subtitle", callback_data="video_subtitle"),
            InlineKeyboardButton("🌊 Watermark", callback_data="video_watermark"),
        ],
        [
            InlineKeyboardButton("✅ Compress", callback_data="video_compress"),
            InlineKeyboardButton("✂️ Trim", callback_data="video_trim"),
        ],
        [
            InlineKeyboardButton("🔊 Extract Audio", callback_data="video_extract"),
            InlineKeyboardButton("❌ Remove Stream", callback_data="video_remove_stream"),
        ],
        [
            InlineKeyboardButton("🔄 Convert Format", callback_data="video_convert"),
            InlineKeyboardButton("📋 Thumbnail", callback_data="video_thumbnail"),
        ],
        [
            InlineKeyboardButton("📊 Metadata", callback_data="video_metadata"),
        ],
        # Row with Back and Close buttons
        [
            InlineKeyboardButton("🔙 Back", callback_data="back_main"),
            InlineKeyboardButton("❌ Close", callback_data="close"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_audio_tools_keyboard() -> InlineKeyboardMarkup:
    """
    Create audio tools submenu keyboard.
    Added close button alongside back button
    
    Returns:
        InlineKeyboardMarkup: Audio tools with combine and sync subtitle, back/close buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("🎬 Video + Audio", callback_data="audio_combine"),
            InlineKeyboardButton("⏱️ Sync Subtitle", callback_data="audio_sync_sub"),
        ],
        # Row with Back and Close buttons
        [
            InlineKeyboardButton("🔙 Back", callback_data="back_main"),
            InlineKeyboardButton("❌ Close", callback_data="close"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_upload_mode_keyboard() -> InlineKeyboardMarkup:
    """
    Create upload mode selection keyboard.
    Added close button alongside back button
    
    Returns:
        InlineKeyboardMarkup: Upload mode options with back/close buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("📱 Telegram Upload", callback_data="upload_telegram"),
            InlineKeyboardButton("☁️ Rclone Upload", callback_data="upload_rclone"),
        ],
        # Row with Back and Close buttons
        [
            InlineKeyboardButton("🔙 Back", callback_data="back_main"),
            InlineKeyboardButton("❌ Close", callback_data="close"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_telegram_format_keyboard() -> InlineKeyboardMarkup:
    """
    Create Telegram upload format selection keyboard.
    Choose between Video or Document format.
    
    Returns:
        InlineKeyboardMarkup: Format options for Telegram upload
    """
    keyboard = [
        [
            InlineKeyboardButton("🎥 Video Format", callback_data="telegram_format_video"),
            InlineKeyboardButton("📁 Document Format", callback_data="telegram_format_document"),
        ],
        # Row with Back button
        [
            InlineKeyboardButton("🔙 Back", callback_data="menu_upload_mode"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """
    Create settings submenu keyboard.
    Added close button alongside back button
    
    Returns:
        InlineKeyboardMarkup: Settings options with back/close buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("📋 Metadata", callback_data="settings_metadata"),
            InlineKeyboardButton("🎬 Video Quality", callback_data="settings_quality"),
        ],
        [
            InlineKeyboardButton("🗑️ Clear Cache", callback_data="settings_clear_cache"),
            InlineKeyboardButton("ℹ️ About", callback_data="settings_about"),
        ],
        # Row with Back and Close buttons
        [
            InlineKeyboardButton("🔙 Back", callback_data="back_main"),
            InlineKeyboardButton("❌ Close", callback_data="close"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_close_keyboard() -> InlineKeyboardMarkup:
    """
    Get keyboard with just back and close buttons for operation dialogs.
    New function for operation pages that need back/close
    
    Returns:
        InlineKeyboardMarkup: Back and Close buttons only
    """
    keyboard = [
        [
            InlineKeyboardButton("🔙 Back", callback_data="back_main"),
            InlineKeyboardButton("❌ Close", callback_data="close"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
