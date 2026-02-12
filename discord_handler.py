import discord
from discord import app_commands
import config


class DiscordHandler:
    """Handles Discord events including message approvals"""
    
    def __init__(self, client):
        """
        Initialize the Discord handler
        
        Args:
            client: Discord client instance
        """
        self.client = client
        
        # Register event handlers
        self.client.event(self.on_ready)
        self.client.event(self.on_raw_reaction_add)
    
    async def on_ready(self):
        """Called when the Discord bot is ready"""
        print(f'Logged in as {self.client.user}')
        print('Discord bot is ready!')
    
    async def on_raw_reaction_add(self, payload):
        """
        Handle reaction additions to messages
        
        Args:
            payload: Discord RawReactionActionEvent payload
        """
        # Ignore bot's own reactions
        if payload.user_id == self.client.user.id:
            return
        
        # Check if reaction is in the approval channel
        if payload.channel_id != config.APPROVAL_CHANNEL_ID:
            return
        
        # Check if reaction is a checkmark
        if str(payload.emoji) != "✅":
            return
        
        await self._approve_message(payload)
    
    async def _approve_message(self, payload):
        """
        Approve a message and post it to the main channel
        
        Args:
            payload: Discord reaction payload
        """
        # Get the channels
        approval_channel = self.client.get_channel(config.APPROVAL_CHANNEL_ID)
        main_channel = self.client.get_channel(config.MAIN_CHANNEL_ID)
        
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
        
        # Create a new embed for the main channel (without the approval footer)
        approved_embed = self._create_approved_embed(original_embed)
        
        # Send to main channel with attachments
        await main_channel.send(
            embed=approved_embed,
            files=[await attachment.to_file() for attachment in message.attachments]
        )
        
        # Update the approval message
        await self._mark_as_approved(message, original_embed, payload.user_id)
    
    def _create_approved_embed(self, original_embed):
        """
        Create an embed for the main channel from the approval embed
        
        Args:
            original_embed: Original Discord embed from approval channel
            
        Returns:
            discord.Embed: New embed without approval footer
        """
        approved_embed = discord.Embed(
            title=original_embed.title,
            description=original_embed.description,
            color=original_embed.color
        )
        
        # Copy all fields
        for field in original_embed.fields:
            approved_embed.add_field(
                name=field.name,
                value=field.value,
                inline=field.inline
            )
        
        # Copy author if exists
        if original_embed.author:
            approved_embed.set_author(
                name=original_embed.author.name,
                icon_url=original_embed.author.icon_url
            )
        
        return approved_embed
    
    async def _mark_as_approved(self, message, original_embed, approver_id):
        """
        Update the approval message to show it was approved
        
        Args:
            message: Discord message object
            original_embed: Original embed
            approver_id: ID of the user who approved
        """
        # Get the approver
        approver = await self.client.fetch_user(approver_id)
        
        # Update the footer
        original_embed.set_footer(
            text=f"✅ Approved by {approver.display_name} and posted to main channel"
        )
        await message.edit(embed=original_embed)
        
        # Remove all reactions to prevent double-approval
        await message.clear_reactions()


class MyClient(discord.Client):
    """Custom Discord client with command tree support"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
    
    async def setup_hook(self):
        """Setup hook called when the client is ready"""
        # Sync commands with Discord
        await self.tree.sync()
        print("Commands synced!")