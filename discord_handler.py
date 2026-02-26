import discord
from discord import app_commands


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