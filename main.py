"""
Telegram to Discord Bridge Bot
Main entry point - initializes and runs both Telegram and Discord clients
"""
from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
import config
from telegram_handler import TelegramHandler
from discord_handler import MyClient, DiscordHandler


async def main():
    """Initialize and start both Discord and Telegram clients"""
    
    session_string = config.TELEGRAM_SESSION
    # Initialize Telegram client
    telegram_client = TelegramClient(
        StringSession(session_string),
        config.API_ID,
        config.API_HASH
    )
    
    # Initialize Discord client
    discord_client = MyClient()
    
    # Initialize handlers
    telegram_handler = TelegramHandler(telegram_client, discord_client)
    discord_handler = DiscordHandler(discord_client)
    
    # Start Telegram client
    await telegram_client.start()
    print("Telegram client started!")
    
    # Start Discord client
    print("Starting Discord client...")
    async with discord_client:
        await discord_client.start(config.DISCORD_TOKEN)


if __name__ == "__main__":
    """Run the main coroutine"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")