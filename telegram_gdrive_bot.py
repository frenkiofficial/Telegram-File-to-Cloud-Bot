import logging
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Google Drive API related imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Telegram Bot related imports
from telegram import Update, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode

# --- Configuration ---
load_dotenv()  # Load variables from .env file

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", None) # Optional target folder
try:
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 100))
except ValueError:
    MAX_FILE_SIZE_MB = 100 # Default if invalid value in .env
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Google API Scopes - If modifying these scopes, delete the token.json file.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CREDENTIALS_FILE = "credentials.json" # Downloaded from Google Cloud Console
TOKEN_FILE = "token.json"             # Stores user's access and refresh tokens
UPLOADED_FILES_DB = "uploaded_files.json" # Simple JSON DB to store file info

# --- Logging Setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING) # Reduce verbosity from http library
logger = logging.getLogger(__name__)

# --- Google Drive Authentication ---
def get_drive_service():
    """Authenticates with Google Drive API and returns the service object."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            logger.error(f"Error loading credentials from {TOKEN_FILE}: {e}")
            creds = None # Force re-authentication

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Refreshing Google API token.")
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Error refreshing token: {e}. Need re-authentication.")
                creds = None # Force re-authentication by deleting token file if refresh fails
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
        else:
            logger.info("Google API credentials not found or invalid. Starting auth flow.")
            if not os.path.exists(CREDENTIALS_FILE):
                logger.error(f"'{CREDENTIALS_FILE}' not found. Download it from Google Cloud Console.")
                print(f"\nERROR: '{CREDENTIALS_FILE}' not found. Download it from Google Cloud Console and place it here.\n")
                return None
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                # Run local server needed for Desktop App flow
                creds = flow.run_local_server(port=0)
                logger.info("Authentication successful.")
            except Exception as e:
                logger.error(f"Error during authentication flow: {e}")
                print(f"\nError during authentication flow: {e}\nCheck if you have downloaded the correct 'credentials.json' for a 'Desktop app'.\n")
                return None

        # Save the credentials for the next run
        if creds:
            try:
                with open(TOKEN_FILE, "w") as token:
                    token.write(creds.to_json())
                logger.info(f"Credentials saved to {TOKEN_FILE}")
            except Exception as e:
                 logger.error(f"Error saving credentials to {TOKEN_FILE}: {e}")


    # Build the Drive v3 service
    try:
        service = build("drive", "v3", credentials=creds)
        logger.info("Google Drive service created successfully.")
        return service
    except HttpError as error:
        logger.error(f"An error occurred building the Drive service: {error}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred building the Drive service: {e}")
        return None

# --- Persistence Functions (Simple JSON DB) ---
def load_uploaded_files() -> list:
    """Loads the list of uploaded files from the JSON database."""
    try:
        if os.path.exists(UPLOADED_FILES_DB):
            with open(UPLOADED_FILES_DB, 'r') as f:
                return json.load(f)
        else:
            return []
    except json.JSONDecodeError:
        logger.error(f"Error decoding {UPLOADED_FILES_DB}. Returning empty list.")
        return []
    except Exception as e:
        logger.error(f"Error loading {UPLOADED_FILES_DB}: {e}")
        return []

def save_uploaded_files(files_list: list):
    """Saves the list of uploaded files to the JSON database."""
    try:
        with open(UPLOADED_FILES_DB, 'w') as f:
            json.dump(files_list, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving {UPLOADED_FILES_DB}: {e}")

# --- Telegram Bot Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! 👋",
        reply_markup=None, # Optional: Add inline keyboard later if needed
    )
    await help_command(update, context) # Show help message as well

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message when the /help command is issued."""
    help_text = (
        f"🤖 **Welcome to the File to Cloud Bot!**\n\n"
        f"I can upload files you send me directly to Google Drive.\n\n"
        f"**How to use:**\n"
        f"1. Just send me any file (document, photo, video, audio).\n"
        f"2. I will upload it to the configured Google Drive folder.\n"
        f"3. I'll send you back the Google Drive link.\n\n"
        f"**Commands:**\n"
        f"/start - Start the bot\n"
        f"/help - Show this help message\n"
        f"/myfiles - List files you've uploaded via this bot\n\n"
        f"**File Size Limit:** {MAX_FILE_SIZE_MB} MB per file."
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def myfiles_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lists the files uploaded by the user (stored in the bot's simple DB)."""
    user_id = update.effective_user.id
    uploaded_files = load_uploaded_files()

    # In this simple version, we list all files. For per-user tracking,
    # the data structure in uploaded_files.json would need to change.
    # e.g., { "user_id": [ {file_info}, ... ], ... }
    # For now, let's assume it's a personal bot or lists all files globally.

    if not uploaded_files:
        await update.message.reply_text("You haven't uploaded any files yet using this bot.")
        return

    message_text = "📂 **Your Uploaded Files:**\n\n"
    file_count = 0
    # Let's only show the latest N files to avoid super long messages
    max_files_to_show = 25
    start_index = max(0, len(uploaded_files) - max_files_to_show)

    for i, file_info in enumerate(uploaded_files[start_index:], start=start_index + 1):
        file_name = file_info.get("name", "Unknown File")
        file_link = file_info.get("link", None)
        if file_link:
            # Escape markdown characters in filename
            escaped_name = file_name.replace('_', r'\_').replace('*', r'\*').replace('[', r'\[').replace('`', r'\`')
            message_text += f"{i}. [{escaped_name}]({file_link})\n"
            file_count += 1
        else:
            # Handle files stored before link was saved (or if save failed)
             message_text += f"{i}. {file_name} (Link unavailable)\n"
             file_count += 1


    if file_count == 0 :
         await update.message.reply_text("Couldn't find any files with links.")
         return

    if len(uploaded_files) > max_files_to_show:
         message_text += f"\n_Showing the latest {max_files_to_show} files._"

    try:
        await update.message.reply_text(message_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error sending file list: {e}")
        # Fallback to plain text if markdown fails
        plain_text = "Your Uploaded Files:\n\n"
        for i, file_info in enumerate(uploaded_files[start_index:], start=start_index+1):
             plain_text += f"{i}. {file_info.get('name', 'Unknown File')} - Link: {file_info.get('link', 'N/A')}\n"
        if len(uploaded_files) > max_files_to_show:
            plain_text += f"\nShowing the latest {max_files_to_show} files."
        await update.message.reply_text(plain_text, disable_web_page_preview=True)


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles incoming files (documents, photos, videos, audio)."""
    message = update.message
    user = update.effective_user
    file_to_upload = None
    file_name = "Unnamed File"
    file_size = 0
    file_id = None
    mime_type = None

    # Determine file type and get necessary attributes
    if message.document:
        file_to_upload = message.document
        file_name = file_to_upload.file_name or f"telegram_doc_{file_to_upload.file_unique_id}"
        mime_type = file_to_upload.mime_type
    elif message.photo:
        # Get the largest photo size
        file_to_upload = message.photo[-1]
        # Photos don't have a name, create one
        file_name = f"telegram_photo_{file_to_upload.file_unique_id}.jpg"
        mime_type = "image/jpeg" # Assume JPEG for photos
    elif message.video:
        file_to_upload = message.video
        file_name = file_to_upload.file_name or f"telegram_video_{file_to_upload.file_unique_id}.mp4"
        mime_type = file_to_upload.mime_type
    elif message.audio:
        file_to_upload = message.audio
        file_name = file_to_upload.file_name or f"telegram_audio_{file_to_upload.file_unique_id}.mp3"
        mime_type = file_to_upload.mime_type
    # Add elif for other types like voice notes if needed

    if not file_to_upload:
        # Should not happen if filters are set correctly, but good practice
        logger.warning("handle_file called but no file found in message.")
        return

    file_id = file_to_upload.file_id
    file_size = file_to_upload.file_size

    # 1. Check file size limit
    if file_size > MAX_FILE_SIZE_BYTES:
        logger.info(f"User {user.id} tried to upload file '{file_name}' ({file_size / 1024 / 1024:.2f} MB) - Exceeds limit.")
        await update.message.reply_text(
            f"❌ **File Too Large!**\n\n"
            f"The file '{file_name}' is {file_size / 1024 / 1024:.2f} MB. "
            f"The maximum allowed size is {MAX_FILE_SIZE_MB} MB.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # 2. Get Google Drive Service (checks auth)
    drive_service = get_drive_service()
    if not drive_service:
        logger.error("Failed to get Google Drive service. Upload aborted.")
        await update.message.reply_text(
            "⚠️ Could not connect to Google Drive. Authentication might be needed or configuration is wrong. Please check the bot logs or contact the administrator."
            )
        return # Stop processing if Drive service fails

    # 3. Download the file from Telegram
    download_path = Path(f"./temp_{file_id}") # Store temporarily
    try:
        status_message = await update.message.reply_text(f" SDownloading '{file_name}' from Telegram...")
        tg_file = await context.bot.get_file(file_id)
        await tg_file.download_to_drive(download_path)
        logger.info(f"File '{file_name}' downloaded to '{download_path}'")

    except Exception as e:
        logger.error(f"Failed to download file {file_id} from Telegram: {e}")
        await status_message.edit_text(f"❌ Error downloading file from Telegram: {e}")
        return # Stop if download fails

    # 4. Upload the file to Google Drive
    try:
        await status_message.edit_text(f"⏳ Uploading '{file_name}' to Google Drive...")

        file_metadata = {
            "name": file_name,
        }
        # Add to specific folder if ID is provided
        if GOOGLE_DRIVE_FOLDER_ID:
             file_metadata["parents"] = [GOOGLE_DRIVE_FOLDER_ID]

        media = MediaFileUpload(
            download_path,
            mimetype=mime_type, # Provide mimetype if known
            resumable=True # Good for larger files
            )

        # Make the API request
        request = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, name, webViewLink" # Request fields needed
        )

        gdrive_file = None
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                 progress = int(status.progress() * 100)
                 logger.info(f"Uploading '{file_name}': {progress}%")
                 # Avoid flooding Telegram with progress updates, update maybe every 20%
                 # Or just show the initial 'uploading' message
                 # await status_message.edit_text(f"⏳ Uploading '{file_name}' to Google Drive... {progress}%")


        gdrive_file = response # response contains the file metadata upon completion

        if gdrive_file and gdrive_file.get("id"):
            file_id_drive = gdrive_file.get("id")
            file_link_drive = gdrive_file.get("webViewLink")
            uploaded_file_name = gdrive_file.get("name")
            logger.info(f"File '{uploaded_file_name}' uploaded successfully. ID: {file_id_drive}, Link: {file_link_drive}")

            # 5. Store file info in our simple DB
            uploaded_files_list = load_uploaded_files()
            uploaded_files_list.append({
                "name": uploaded_file_name,
                "id": file_id_drive,
                "link": file_link_drive,
                "telegram_user_id": user.id # Optional: store who uploaded
            })
            save_uploaded_files(uploaded_files_list)

            # 6. Send confirmation and link to user
            await status_message.edit_text(
                f"✅ **Upload Successful!**\n\n"
                f"📄 File: `{uploaded_file_name}`\n"
                f"🔗 Link: {file_link_drive}",
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=False # Show preview for the Drive link
            )
        else:
             logger.error(f"Google Drive API did not return expected file info after upload for '{file_name}'. Response: {gdrive_file}")
             await status_message.edit_text(f"❌ Upload completed but failed to get file details from Google Drive.")

    except HttpError as error:
        logger.error(f"An API error occurred during upload: {error}")
        await status_message.edit_text(f"❌ Google Drive API Error: {error}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during upload: {e}")
        await status_message.edit_text(f"❌ An unexpected error occurred during upload: {e}")
    finally:
        # 7. Clean up the downloaded file
        if download_path.exists():
            try:
                os.remove(download_path)
                logger.info(f"Temporary file '{download_path}' removed.")
            except OSError as e:
                logger.error(f"Error removing temporary file '{download_path}': {e}")

# --- Main Bot Execution ---
def main() -> None:
    """Start the bot."""
    # Basic check for token
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("TELEGRAM_BOT_TOKEN not found in environment variables! Bot cannot start.")
        print("\nERROR: TELEGRAM_BOT_TOKEN is missing. Set it in the .env file or environment variables.\n")
        return

    # First, try to authenticate with Google Drive on startup
    # This will trigger the browser flow if token.json is missing/invalid
    print("Attempting initial Google Drive authentication...")
    drive_service = get_drive_service()
    if not drive_service:
        logger.critical("Failed initial Google Drive authentication. Check logs and configuration. Bot will start but uploads will fail.")
        print("\nWarning: Could not authenticate with Google Drive. Uploads will fail until authenticated.\n")
        # Decide if you want the bot to exit or continue running without upload functionality
        # return # Uncomment this line to stop the bot if auth fails initially

    else:
        print("Google Drive authentication successful or token loaded.")


    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # --- Register Handlers ---
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("myfiles", myfiles_command))

    # Add handlers for different file types
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    application.add_handler(MessageHandler(filters.PHOTO, handle_file))
    application.add_handler(MessageHandler(filters.VIDEO, handle_file))
    application.add_handler(MessageHandler(filters.AUDIO, handle_file))
    # You can add more filters (e.g., filters.VOICE) if needed

    # --- Start the Bot ---
    print("Starting Telegram bot polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    print("Bot stopped.")


if __name__ == "__main__":
    main()
