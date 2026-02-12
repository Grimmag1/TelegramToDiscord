from telethon import TelegramClient, events
import os
from os import listdir
from os.path import isfile, join
import discord
from discord import app_commands
import asyncio
from datetime import timezone, timedelta
from dotenv import load_dotenv
import shutil


load_dotenv()

APPROVAL_CHANNEL_ID = 1279161260348280914
MAIN_CHANNEL_ID = 1279120985156620421

API_ID = int(os.getenv('API_ID'))
API_HASH = str(os.getenv('API_HASH'))

KOFI_NEWS_ID = -1002682414503
KOFI_PROVOZ_ID = -1003386278317
KOFI_FLYBOYS_ID = -4782369870
KOFI_SMENY_ID = -1003444865618
KOFI_FOTOCHECK_ID = -1003388534514
PERSONAL_ID = int(os.getenv('PERSONAL_ID'))

# Creating Telegram client
T_client = TelegramClient('anon', API_ID, API_HASH)

# Creating Discord client
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Sync commands with Discord
        await self.tree.sync()
        print("Commands synced!")

D_client = MyClient()

@D_client.event
async def on_ready():
    print(f'Logged in as {D_client.user}')
    print('Bot is ready!')



@T_client.on(events.NewMessage(chats=[PERSONAL_ID, KOFI_NEWS_ID, KOFI_FLYBOYS_ID, KOFI_PROVOZ_ID, KOFI_SMENY_ID]))
async def my_event_handler(event):
    # Check existence of approval channel
    approval_channel = D_client.get_channel(APPROVAL_CHANNEL_ID)
    if not approval_channel:
        await print("Approval channel not found! Please configure APPROVAL_CHANNEL_ID.", ephemeral=True)
        return
    
    # If the message contains multiple files, download each one and export to discord only on the last one
    if event.message.grouped_id:
        await event.message.download_media(file=f"downloads/message_{event.message.grouped_id}/")
        latest_message = await T_client.get_messages(PERSONAL_ID,limit=1)
        if not (latest_message[0].grouped_id == event.message.grouped_id and latest_message[0].id == event.message.id):
            return
    
    # Get message details
    message_text = event.message.text or "[No text content]"
    sender = await event.get_sender()
    chat = await event.get_chat()
    
    # Determine sender name
    if hasattr(sender, 'first_name'):
        sender_name = sender.first_name
        if hasattr(sender, 'last_name') and sender.last_name:
            sender_name += f" {sender.last_name}"
        if hasattr(sender, 'username') and sender.username:
            sender_name += f" (@{sender.username})"
    else:
        sender_name = "Unknown Sender"
    
    # Determine chat name
    if hasattr(chat, 'title'):
        chat_name = chat.title
    elif hasattr(chat, 'first_name'):
        chat_name = chat.first_name
    else:
        chat_name = "Unknown Chat"
    
    # Create embed for Discord
    embed = discord.Embed(
        title="New Telegram Message",
        description=message_text,
        color=0x0088cc
    )
    dt = event.message.date
    gmt_plus_1 = timezone(timedelta(hours=1))
    dt_gmt1 = dt.astimezone(gmt_plus_1)
    formatted = dt_gmt1.strftime("%d.%m.%Y %H:%M")

    embed.add_field(name="From", value=sender_name, inline=True)
    embed.add_field(name="Chat", value=chat_name, inline=True)
    embed.add_field(name="Time", value=formatted, inline=True)
    embed.set_footer(text="React with ✅ to approve and post to main channel")
    
    # Handle media/files if present
    if event.message.media:
        #embed.add_field(name="Media", value="📎 Contains media/file", inline=False)

        if event.message.grouped_id:
            file_path=f"downloads/message_{event.message.grouped_id}"
            allfiles = [f for f in listdir(file_path) if isfile(join(file_path, f))]
            files: list[discord.File] = []
            for i,f in enumerate(allfiles):
                if f[0] == ".":
                    os.rename(f"{file_path}/{f}",f"{file_path}/prefix{f}")
                    f=f"prefix{f}"
                files.append(discord.File(f"{file_path}/{f}"))
            discord_message = await approval_channel.send(embed=embed, files=files)

        else:
            file_path=f"downloads/message_{event.message.id}"
            await event.message.download_media(file=f"{file_path}/")
            filename = listdir(file_path)[0]
            if filename[0] == ".":
                os.rename(f"{file_path}/{filename}", f"{file_path}/prefix{filename}")
                filename = f"prefix{filename}"
            file = discord.File(f"{file_path}/{filename}")
            #embed.set_image(url=f"attachement://{filename}")
            discord_message = await approval_channel.send(embed=embed, file=file)
    else:
        # Send to approval channel
        discord_message = await approval_channel.send(embed=embed)
    
    # Add reaction for approval
    await discord_message.add_reaction("✅")
    shutil.rmtree("downloads") 
    print(f"Telegram message from {sender_name} forwarded to Discord approval channel")

@D_client.event
async def on_raw_reaction_add(payload):
    # Ignore bot's own reactions
    if payload.user_id == D_client.user.id:
        return
    
    # Check if reaction is in the approval channel
    if payload.channel_id != APPROVAL_CHANNEL_ID:
        return
    
    # Check if reaction is a checkmark
    if str(payload.emoji) != "✅":
        return
    
    # Get the channels
    approval_channel = D_client.get_channel(APPROVAL_CHANNEL_ID)
    main_channel = D_client.get_channel(MAIN_CHANNEL_ID)
    
    if not main_channel:
        print("Main channel not found! Please configure MAIN_CHANNEL_ID.")
        return
    
    # Get the message
    message = await approval_channel.fetch_message(payload.message_id)
    
    # Check if message has an embed (our approval message)
    if not message.embeds:
        return
    
    # Get the original embed
    original_embed = message.embeds[0]
    
    # Create a new embed for the main channel (without the footer)
    approved_embed = discord.Embed(
        title=original_embed.title,
        description=original_embed.description,
        color=original_embed.color
    )
    for field in original_embed.fields:
        approved_embed.add_field(name=field.name, value=field.value, inline=field.inline)
    
    # Copy author if exists
    if original_embed.author:
        approved_embed.set_author(
            name=original_embed.author.name,
            icon_url=original_embed.author.icon_url
        )
    
    # Get the user who approved
    approver = await D_client.fetch_user(payload.user_id)
    # approved_embed.set_footer(text=f"Approved by {approver.display_name}")
    
    # Send to main channel
    await main_channel.send(embed=approved_embed, files=[await attachment.to_file() for attachment in message.attachments])
    
    # Update the approval message to show it was approved
    original_embed.set_footer(text=f"✅ Approved by {approver.display_name} and posted to main channel")
    await message.edit(embed=original_embed)
    
    # Remove all reactions to prevent double-approval
    await message.clear_reactions()


# Run both Discord and Telegram clients concurrently
async def main():
    """Start both Discord and Telegram clients"""
    
    # Start Telegram client
    await T_client.start()
    print("Telegram client started!")

    # Start Discord client in the background
    async with D_client:
        await D_client.start(str(os.getenv('TOKEN')))

if __name__ == "__main__":
    # Run the main coroutine
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")