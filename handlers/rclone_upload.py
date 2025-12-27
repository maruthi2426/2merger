"""Rclone upload handler for cloud storage integration."""
import logging
import os
import subprocess
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

# Rclone configuration path - update this to your rclone config location
RCLONE_CONFIG_PATH = os.path.expanduser("~/.config/rclone/rclone.conf")
RCLONE_REMOTE = os.getenv("RCLONE_REMOTE", "gdrive")  # Default remote name


async def check_rclone_configured() -> bool:
    """Check if rclone is installed and configured."""
    try:
        result = await asyncio.to_thread(
            subprocess.run,
            ["rclone", "version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Rclone not installed or not in PATH: {e}")
        return False


async def get_rclone_remotes() -> list:
    """Get list of configured rclone remotes."""
    try:
        result = await asyncio.to_thread(
            subprocess.run,
            ["rclone", "listremotes"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            remotes = [r.strip().rstrip(":") for r in result.stdout.strip().split("\n") if r.strip()]
            return remotes
        return []
    except Exception as e:
        logger.error(f"Error getting rclone remotes: {e}")
        return []


async def rclone_driver(status_msg, user_id: int, filepath: str, remote: str = None) -> dict:
    """
    Upload file to rclone configured remote drive.
    
    Args:
        status_msg: Telegram message object for status updates
        user_id: Telegram user ID
        filepath: Full path to file to upload
        remote: Rclone remote name (defaults to RCLONE_REMOTE env var or 'gdrive')
    
    Returns:
        dict: Status with success flag and details
    """
    try:
        # Use provided remote or default
        remote_name = remote or RCLONE_REMOTE
        
        # Check if file exists
        if not os.path.exists(filepath):
            error_msg = f"❌ File not found: {filepath}"
            logger.error(error_msg)
            await status_msg.edit_text(error_msg)
            return {"success": False, "error": "File not found"}
        
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        filename = os.path.basename(filepath)
        
        # Check if rclone is installed
        rclone_ok = await check_rclone_configured()
        if not rclone_ok:
            error_msg = "❌ Rclone not installed or not configured.\nInstall rclone and configure a remote."
            logger.error(error_msg)
            await status_msg.edit_text(error_msg)
            return {"success": False, "error": "Rclone not installed"}
        
        # Get available remotes
        remotes = await get_rclone_remotes()
        if not remotes:
            error_msg = "❌ No rclone remotes configured.\nRun 'rclone config' to set up a remote."
            logger.error(error_msg)
            await status_msg.edit_text(error_msg)
            return {"success": False, "error": "No remotes configured"}
        
        # Check if specified remote exists
        if remote_name not in remotes:
            error_msg = f"❌ Rclone remote '{remote_name}' not found.\nAvailable remotes: {', '.join(remotes)}"
            logger.error(error_msg)
            await status_msg.edit_text(error_msg)
            return {"success": False, "error": f"Remote '{remote_name}' not found"}
        
        # Prepare upload destination
        destination = f"{remote_name}:VideoMerger/{filename}"
        
        await status_msg.edit_text(
            text="☁️ UPLOADING TO RCLONE\n━━━━━━━━━━━━━━━━━━\n\n"
                 f"📁 Remote: {remote_name}\n"
                 f"📄 File: {filename}\n"
                 f"📊 Size: {file_size_mb:.2f}MB\n\n"
                 "⏳ Uploading... 20%"
        )
        
        # Run rclone copy command
        cmd = [
            "rclone",
            "copy",
            filepath,
            f"{remote_name}:VideoMerger/",
            "--progress",
            "--verbose"
        ]
        
        logger.info(f"Running rclone command: {' '.join(cmd)}")
        
        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout for large files
        )
        
        if result.returncode == 0:
            logger.info(f"File uploaded successfully to {destination}")
            
            await status_msg.edit_text(
                text="✅ UPLOAD COMPLETE!\n━━━━━━━━━━━━━━━━━━\n\n"
                     f"☁️ Remote: {remote_name}\n"
                     f"📄 File: {filename}\n"
                     f"📊 Size: {file_size_mb:.2f}MB\n"
                     f"📍 Path: VideoMerger/{filename}\n\n"
                     "✨ Upload successful!"
            )
            
            return {"success": True, "remote": remote_name, "file": filename}
        else:
            error_output = result.stderr or result.stdout
            logger.error(f"Rclone upload failed: {error_output}")
            
            await status_msg.edit_text(
                text="❌ UPLOAD FAILED\n━━━━━━━━━━━━━━━━━━\n\n"
                     f"Error: {error_output[:200]}\n\n"
                     "Check rclone configuration and try again."
            )
            
            return {"success": False, "error": error_output}
    
    except asyncio.TimeoutError:
        error_msg = "❌ Upload timeout - file too large or connection too slow"
        logger.error(error_msg)
        await status_msg.edit_text(error_msg)
        return {"success": False, "error": "Upload timeout"}
    
    except Exception as e:
        error_msg = f"❌ Upload error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        await status_msg.edit_text(error_msg)
        return {"success": False, "error": str(e)}
