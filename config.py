import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Discord Channel IDs
APPROVAL_CHANNEL_FLYBOYS_ID = int(os.getenv('APPROVAL_CHANNEL_FLYBOYS_ID'))
APPROVAL_CHANNEL_NEWS_ID = int(os.getenv('APPROVAL_CHANNEL_NEWS_ID'))
APPROVAL_CHANNEL_PROVOZ_ID = int(os.getenv('APPROVAL_CHANNEL_PROVOZ_ID'))
APPROVAL_CHANNEL_ID = int(os.getenv('APPROVAL_CHANNEL_ID'))
MAIN_CHANNEL_ID = int(os.getenv('MAIN_CHANNEL_ID'))
SMENY_CHANNEL_ID = int(os.getenv('SMENY_CHANNEL_ID'))

# Telegram API Credentials
API_ID = int(os.getenv('API_ID'))
API_HASH = str(os.getenv('API_HASH'))
TELEGRAM_SESSION=str(os.getenv('SESSION').strip())

# Discord Bot Token
DISCORD_TOKEN = str(os.getenv('TOKEN'))

# Telegram Chat IDs to monitor
KOFI_NEWS_ID = int(os.getenv('KOFI_NEWS_ID'))
KOFI_PROVOZ_ID = int(os.getenv('KOFI_PROVOZ_ID'))
KOFI_PROVOZ_SMENY_ID = int(os.getenv('KOFI_PROVOZ_SMENY_ID'))
KOFI_PROVOZ_MAIN_ID = None
KOFI_FLYBOYS_ID = int(os.getenv('KOFI_FLYBOYS_ID'))
KOFI_SMENY_ID = int(os.getenv('KOFI_SMENY_ID'))
KOFI_FOTOCHECK_ID = int(os.getenv('KOFI_FOTOCHECK_ID'))
PERSONAL_ID = int(os.getenv('PERSONAL_ID'))

TESTING_ID = -1003456617977
TESTING_TOPIC_ID = 2

# List of all chats to monitor
MONITORED_CHATS = [
    KOFI_NEWS_ID,
    KOFI_FLYBOYS_ID,
    KOFI_PROVOZ_ID,
]

# Login info for IS
LOGIN = os.getenv('LOGIN')
PASSWORD = os.getenv('PASSWORD')

# File paths
DOWNLOADS_DIR = "downloads"
SESSION_NAME = "anon"