from telethon import events
import discord
import os
from os import listdir
from os.path import isfile, join
from datetime import timezone, timedelta
import config


class TelegramHandler:
    """Handles Telegram events and forwards messages to Discord"""
    
    def __init__(self, telegram_client, discord_client):
        """
        Initialize the Telegram handler
        
        Args:
            telegram_client: Telethon client instance
            discord_client: Discord client instance
        """
        self.telegram_client = telegram_client
        self.discord_client = discord_client

        self.telegram_client.on(events.NewMessage(chats=[config.KOFI_PROVOZ_ID])) (
            self.handle_direct_message
        )
    


    def _get_sender_name(self, sender):
        """Extract sender name from Telegram sender object"""
        if hasattr(sender, 'first_name'):
            sender_name = sender.first_name
            if hasattr(sender, 'last_name') and sender.last_name:
                sender_name += f" {sender.last_name}"
            if hasattr(sender, 'username') and sender.username:
                sender_name += f" (@{sender.username})"
        else:
            sender_name = "Unknown Sender"
        
        return sender_name
    
    def _get_chat_name(self, chat):
        """Extract chat name from Telegram chat object"""
        if hasattr(chat, 'title'):
            chat_name = chat.title
        elif hasattr(chat, 'first_name'):
            chat_name = chat.first_name
        else:
            chat_name = "Unknown Chat"
        
        return chat_name
    
    async def _send_with_media(self, event, channel, embed, is_grouped):
        """
        Send message to Discord with media attachments
        
        Args:
            event: Telethon message event
            channel: Discord channel
            embed: Discord embed
            is_grouped: Whether this is a grouped message
            
        Returns:
            discord.Message: Sent Discord message
        """
        if not event.message.media:
            # No media, just send embed
            return await channel.send(embed=embed)
        
        if is_grouped:
            # Handle grouped media (album)
            file_path = f"{config.DOWNLOADS_DIR}/message_{event.message.grouped_id}"
            files = self._prepare_files(file_path)
            return await channel.send(embed=embed, files=files)
        else:
            # Handle single media file
            file_path = f"{config.DOWNLOADS_DIR}/message_{event.message.id}"
            await event.message.download_media(file=f"{file_path}/")
            
            filename = listdir(file_path)[0]
            # Fix hidden files (starting with .)
            if filename[0] == ".":
                os.rename(f"{file_path}/{filename}", f"{file_path}/prefix{filename}")
                filename = f"prefix{filename}"
            
            file = discord.File(f"{file_path}/{filename}")
            return await channel.send(embed=embed, file=file)
    
    def _prepare_files(self, file_path):
        """
        Prepare Discord file attachments from a directory
        
        Args:
            file_path: Path to directory containing files
            
        Returns:
            list[discord.File]: List of Discord file objects
        """
        all_files = [f for f in listdir(file_path) if isfile(join(file_path, f))]
        files = []
        
        for filename in all_files:
            # Fix hidden files (starting with .)
            if filename[0] == ".":
                os.rename(f"{file_path}/{filename}", f"{file_path}/prefix{filename}")
                filename = f"prefix{filename}"
            
            files.append(discord.File(f"{file_path}/{filename}"))
        
        return files
    
    async def handle_direct_message(self, event):
        """
        Send message to Discord without approval
        
        Args:
            event: Telethon message event
        """
        target_channel = await self.discord_client.fetch_channel(config.SMENY_CHANNEL_ID)
        if not target_channel:
            print("Target channel not found")
            return
        
        topic_id = None
        if event.message.reply_to:
            topic_id = event.message.reply_to.reply_to_top_id or event.message.reply_to.reply_to_msg_id

        # Ignore messages not in the specific topic
        if topic_id != config.KOFI_PROVOZ_SMENY_ID:
            print("Message not in the Provoz Smeny topic, ignoring.")
            return

        sender = await event.get_sender()
        sender_name = self._get_sender_name(sender)
        message_text = event.message.text or "[No text content]"

        original_text = None
        original_sender_name = None

        # Only fetch original message if this is a REAL reply
        # A real reply has reply_to_top_id set (meaning it's replying to a message within the topic)
        # If only reply_to_msg_id is set and equals topic_id, it's just an original topic message
        is_real_reply = (
            event.message.reply_to and
            event.message.reply_to.reply_to_top_id is not None and
            event.message.reply_to.reply_to_msg_id != topic_id
        )

        if is_real_reply:
            try:
                original_msg = await self.telegram_client.get_messages(
                    await event.get_chat(),
                    ids=event.message.reply_to.reply_to_msg_id
                )
                if original_msg:
                    original_text = original_msg.text or "[Media / No text]"
                    original_sender = await original_msg.get_sender()
                    original_sender_name = self._get_sender_name(original_sender)
            except Exception as e:
                print(f"Could not fetch original message: {e}")

        embed = self._create_direct_message_embed(event, message_text, sender_name, original_text, original_sender_name)
        await self._send_with_media(event, target_channel, embed, is_grouped=False)

    def _create_direct_message_embed(self, event, message_text, sender_name, original_text=None, original_sender_name=None):
        embed = discord.Embed(
            title=sender_name,
            description=message_text,
            color=0xcc8800
        )

        # If it's a reply, add the original message as a field above
        if original_text and original_sender_name:
            embed.add_field(
                name=f"↩️ Replying to {original_sender_name}",
                value=f">>> {original_text}",
                inline=False
            )

        dt = event.message.date
        gmt_offset = timezone(timedelta(hours=1))
        dt_local = dt.astimezone(gmt_offset)
        formatted_time = dt_local.strftime("%d.%m.%Y %H:%M")

        embed.add_field(name="Date", value=formatted_time, inline=False)

        return embed