# Telegram File to Cloud Bot (Google Drive Uploader)

[![GitHub Repo stars](https://img.shields.io/github/stars/frenkiofficial/Telegram-File-to-Cloud-Bot?style=social)](https://github.com/frenkiofficial/Telegram-File-to-Cloud-Bot)

This bot allows users to upload files directly from Telegram to their Google Drive account. It's a convenient way to save documents, images, videos, or other files from Telegram chats without using up your device or Telegram cloud storage.

---

## ✨ Features (Current Version)

*   **⬆️ Upload Files to Google Drive:** Send a file (document, photo, video, audio) to the bot, and it will be uploaded to your connected Google Drive.
*   **🔗 Generate Download Link:** After a successful upload, the bot provides a direct Google Drive link to access the file.
*   **📂 List Uploaded Files:** Use the `/myfiles` command to view a list of files uploaded via the bot (based on the bot's history).
*   ** B File Size Limit:** Configurable limit for the maximum size of files that can be uploaded (e.g., 100MB).

---

## 📋 Prerequisites

Before you begin, ensure you have met the following requirements:

1.  **Python:** Python 3.7 or higher installed.
2.  **Telegram Bot Token:**
    *   Talk to `@BotFather` on Telegram.
    *   Create a new bot using `/newbot`.
    *   Copy the **HTTP API token**.
3.  **Google Cloud Project & API Credentials:**
    *   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    *   Create a new project or select an existing one.
    *   Enable the **Google Drive API** (APIs & Services -> Library).
    *   Create **OAuth 2.0 Client IDs** credentials (APIs & Services -> Credentials -> Create Credentials -> OAuth client ID).
    *   Select **Desktop app** as the application type.
    *   Download the credentials JSON file. Rename it to `credentials.json` and place it in the project directory.
    *   Configure the **OAuth consent screen** if prompted (User Type: External, add your Google account email as a Test User during development/testing).
4.  **(Optional) Google Drive Folder ID:**
    *   Create a folder in your Google Drive where you want files uploaded.
    *   Open the folder. The ID is the last part of the URL (e.g., `https://drive.google.com/drive/folders/THIS_IS_THE_FOLDER_ID`).

---

## 🚀 Setup & Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/frenkiofficial/Telegram-File-to-Cloud-Bot.git
    cd Telegram-File-to-Cloud-Bot
    ```

2.  **Install Dependencies:**
    ```bash
    pip install python-telegram-bot==20.* google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv
    ```
    *(**Note:** Consider creating a `requirements.txt` file for easier dependency management)*

3.  **Place Credentials File:**
    *   Ensure the `credentials.json` file you downloaded from Google Cloud Console is in the main project directory.

4.  **Create Configuration File:**
    *   Create a file named `.env` in the project directory.
    *   Add the following lines, replacing the placeholders with your actual values:
        ```dotenv
        TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE
        GOOGLE_DRIVE_FOLDER_ID=YOUR_GOOGLE_DRIVE_FOLDER_ID_HERE # Optional: Leave empty to upload to root "My Drive"
        MAX_FILE_SIZE_MB=100 # Optional: Set the max upload size in MB (default is 100)
        # OWNER_ID=YOUR_TELEGRAM_USER_ID # Optional: Add your Telegram User ID for potential future restricted commands
        ```

5.  **First Run & Google Authentication:**
    *   Run the bot for the first time:
        ```bash
        python telegram_gdrive_bot.py
        ```
    *   The script will attempt to authenticate with Google Drive. If `token.json` doesn't exist or is invalid, it will print a URL in your console.
    *   **Copy this URL and paste it into your web browser.**
    *   Log in with the Google account associated with the Drive you want to use.
    *   Grant the application permission to access your Google Drive files.
    *   If successful, the browser will show a confirmation, and the script will create a `token.json` file in the project directory. This file stores your authorization tokens so you don't have to authenticate via the browser every time.
    *   **Keep `token.json` secure!** Add it to your `.gitignore` file if you use Git.

6.  **Run the Bot:**
    *   After the initial authentication, you can stop the bot (Ctrl+C) and run it normally:
        ```bash
        python telegram_gdrive_bot.py
        ```
    *   The bot should now start polling for updates.

---

## ⚙️ How to Use

1.  **Find your Bot:** Open Telegram and search for the bot username you created with BotFather.
2.  **Start Chat:** Send the `/start` command to initiate a conversation.
3.  **Get Help:** Send `/help` to see the available commands and instructions.
4.  **Upload File:** Simply send any file (document, photo, video, audio) directly to the bot chat.
    *   The bot will show status messages (Downloading, Uploading...).
    *   If the upload is successful and within the size limit, it will reply with the file name and a Google Drive link.
5.  **List Files:** Send `/myfiles` to get a list of files the bot has successfully uploaded (based on its local record `uploaded_files.json`).

---

## 🛠️ Want More Features or Need Help?

This bot provides basic file uploading functionality. If you require more advanced features or custom modifications, feel free to reach out!

**Potential Additional Features (Available upon request):**

*   🔹 **Multi-Cloud Support:** Integration with Dropbox, OneDrive, etc.
*   🗂️ **User-Defined Folders:** Allow users to specify target folders within their Drive.
*   🔄 **Automatic Conversion:** Convert files (e.g., JPG to PDF, HEIC to JPG) before uploading.
*   👥 **Multi-User OAuth2:** Enable individual users to connect their *own* Google Drive accounts securely.
*   🔔 **Enhanced Notifications:** Customize notifications for uploads, errors, etc.
*   📊 **Usage Tracking & Quotas:** Implement per-user limits or tracking.

**Contact Me:**

If you're interested in these features, have suggestions, or need assistance, you can contact me through:

*   **GitHub:** [frenkiofficial](https://github.com/frenkiofficial) (Create an Issue or Discussion)
*   **Hugging Face:** [frenkiofficial](https://huggingface.co/frenkiofficial)
*   **Telegram:** [@FrenkiOfficial](https://t.me/FrenkiOfficial)
*   **Twitter:** [@officialfrenki](https://twitter.com/officialfrenki)
*   **Fiverr:** [frenkimusic](https://www.fiverr.com/frenkimusic/) (For custom development gigs)

---

## 🔒 Security Note

*   Your `TELEGRAM_BOT_TOKEN`, `credentials.json`, and especially `token.json` contain sensitive information.
*   **DO NOT** share these files publicly or commit them to version control.
*   Use a `.gitignore` file to prevent accidental commits of sensitive data. Add at least the following lines to your `.gitignore`:
    ```gitignore
    credentials.json
    token.json
    .env
    *.pyc
    __pycache__/
    ```

---

Feel free to contribute to this project by creating Pull Requests or Issues!
