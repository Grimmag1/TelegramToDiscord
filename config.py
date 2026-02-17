import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Discord Channel IDs
APPROVAL_CHANNEL_ID = 1279161260348280914
MAIN_CHANNEL_ID = 1279120985156620421
SMENY_CHANNEL_ID = 1279120985156620421

# Telegram API Credentials
API_ID = int(os.getenv('API_ID'))
API_HASH = str(os.getenv('API_HASH'))
TELEGRAM_SESSION=str(os.getenv('SESSION').strip())

# Discord Bot Token
DISCORD_TOKEN = str(os.getenv('TOKEN'))

# Telegram Chat IDs to monitor
KOFI_NEWS_ID = -1002682414503
KOFI_PROVOZ_ID = -1003386278317
KOFI_PROVOZ_SMENY_ID = 139
KOFI_FLYBOYS_ID = -4782369870
KOFI_SMENY_ID = -1003444865618
KOFI_FOTOCHECK_ID = -1003388534514
PERSONAL_ID = int(os.getenv('PERSONAL_ID'))
TESTING_ID = -1003456617977
TESTING_TOPIC_ID = 2

# List of all chats to monitor
MONITORED_CHATS = [
    PERSONAL_ID,
    KOFI_NEWS_ID,
    KOFI_FLYBOYS_ID,
    KOFI_PROVOZ_ID,
    KOFI_SMENY_ID
]

# File paths
DOWNLOADS_DIR = "downloads"
SESSION_NAME = "anon"