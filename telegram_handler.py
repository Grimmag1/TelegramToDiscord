from telethon import events
import discord
import os
import shutil
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
        
        # Register event handlers
        self.telegram_client.on(events.NewMessage(chats=config.MONITORED_CHATS))(
            self.handle_new_message
        )
    
    async def handle_new_message(self, event):
        """
        Handle new messages from Telegram
        
        Args:
            event: Telethon NewMessage event
        """
        # Check existence of approval channel
        approval_channel = self.discord_client.get_channel(config.APPROVAL_CHANNEL_ID)
        if not approval_channel:
            print("Approval channel not found! Please configure APPROVAL_CHANNEL_ID.")
            return
        
        # Handle grouped messages (albums)
        if event.message.grouped_id:
            await self._handle_grouped_message(event, approval_channel)
        else:
            await self._handle_single_message(event, approval_channel)
    
    async def _handle_grouped_message(self, event, approval_channel):
        """Handle messages that are part of a group (album)"""
        # Download media to grouped folder
        await event.message.download_media(
            file=f"{config.DOWNLOADS_DIR}/message_{event.message.grouped_id}/"
        )
        
        # Check if this is the last message in the group
        latest_message = await self.telegram_client.get_messages(
            config.PERSONAL_ID, 
            limit=1
        )
        
        is_last_in_group = (
            latest_message[0].grouped_id == event.message.grouped_id and 
            latest_message[0].id == event.message.id
        )
        
        if not is_last_in_group:
            return  # Wait for the last message in the group
        
        # Process and send the grouped message
        await self._send_message_to_discord(event, approval_channel, is_grouped=True)
    
    async def _handle_single_message(self, event, approval_channel):
        """Handle single messages (not part of a group)"""
        await self._send_message_to_discord(event, approval_channel, is_grouped=False)
    
    async def _send_message_to_discord(self, event, approval_channel, is_grouped=False):
        """
        Send message to Discord approval channel
        
        Args:
            event: Telethon message event
            approval_channel: Discord channel to send to
            is_grouped: Whether this is a grouped message (album)
        """
        # Get message details
        message_text = event.message.text or "[No text content]"
        sender = await event.get_sender()
        chat = await event.get_chat()
        
        # Create embed
        embed = self._create_embed(event, message_text, sender, chat)
        
        # Handle media
        discord_message = await self._send_with_media(
            event, 
            approval_channel, 
            embed, 
            is_grouped
        )
        
        # Add approval reaction
        await discord_message.add_reaction("✅")
        
        # Cleanup downloads
        if os.path.exists(config.DOWNLOADS_DIR):
            shutil.rmtree(config.DOWNLOADS_DIR)
        
        # Log the forwarding
        sender_name = self._get_sender_name(sender)
        print(f"Telegram message from {sender_name} forwarded to Discord approval channel")
    
    def _create_embed(self, event, message_text, sender, chat):
        """
        Create Discord embed for the message
        
        Args:
            event: Telethon message event
            message_text: Text content of the message
            sender: Message sender
            chat: Chat where message was sent
            
        Returns:
            discord.Embed: Formatted embed
        """
        embed = discord.Embed(
            title="New Telegram Message",
            description=message_text,
            color=0x0088cc
        )
        
        # Format timestamp
        dt = event.message.date
        gmt_offset = timezone(timedelta(hours=1))
        dt_local = dt.astimezone(gmt_offset)
        formatted_time = dt_local.strftime("%d.%m.%Y %H:%M")
        
        # Add fields
        sender_name = self._get_sender_name(sender)
        chat_name = self._get_chat_name(chat)
        
        embed.add_field(name="From", value=sender_name, inline=True)
        embed.add_field(name="Chat", value=chat_name, inline=True)
        embed.add_field(name="Time", value=formatted_time, inline=True)
        embed.set_footer(text="React with ✅ to approve and post to main channel")
        
        return embed
    
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