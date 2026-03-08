from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import config
api_id = config.API_ID
api_hash = config.API_HASH

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print(client.session.save())