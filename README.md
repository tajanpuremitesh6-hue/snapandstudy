# Snap & Study

Snap & Study is a Streamlit study assistant. Ask questions or share study material, get explanations from Google Gemini, and send a concise conversation summary to Telegram.

## Features

- Chat about study topics and uploaded study material.
- Upload images (`.jpg`, `.jpeg`, `.png`) or PDFs.
- Send a concise study summary to a configured Telegram chat.

## Requirements

- Python 3.10 or later
- A Google Gemini API key
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

## Setup

1. Clone the repository and open its folder:

   ```powershell
   git clone https://github.com/tajanpuremitesh6-hue/snapandstudy.git
   cd snapandstudy
   ```

2. Create and activate a virtual environment (PowerShell):

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

4. Create `.streamlit/secrets.toml` and add your credentials:

   ```toml
   GEMINI_API_KEY = "your-gemini-api-key"
   TELEGRAM_BOT_TOKEN = "your-telegram-bot-token"
   TELEGRAM_CHAT_ID = "your-private-telegram-chat-id"
   ```

   You can omit `TELEGRAM_CHAT_ID` and enter it during onboarding instead. The app also accepts these settings as environment variables.

5. In Telegram, open your bot and send `/start`. The app does not reply to `/start`; sending it lets the bot initiate the private chat. Use the private chat ID for `TELEGRAM_CHAT_ID`, not the bot's ID or the number at the start of its token. You can find your personal ID with a Telegram ID bot such as [@userinfobot](https://t.me/userinfobot).

6. Start the app:

   ```powershell
   streamlit run app.py
   ```

Enter your name when prompted. If no chat ID is configured, enter your Telegram chat ID on the onboarding screen. After an exchange with the study assistant, use **Send summary to Telegram**.

## Secrets and privacy

Do not commit `.streamlit/secrets.toml` or paste API keys and bot tokens into source files. The repository's `.gitignore` excludes the secrets file, virtual environments, Python cache directories, and bytecode files. If a credential is exposed, revoke or rotate it with its provider.
