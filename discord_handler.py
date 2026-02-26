import discord
from discord import app_commands
import config
import requests
from bs4 import BeautifulSoup
import asyncio
import re

class DiscordHandler:
    """Handles Discord events including message approvals"""
    
    def __init__(self, client):
        """
        Initialize the Discord handler
        
        Args:
            client: Discord client instance
        """
        self.client = client
        self.payload = {
            'login': str(config.LOGIN),
            'heslo': str(config.PASSWORD),
            'ok': 'Přihlásit se'
        }
        self.shifts = []
        # Register event handlers
        self.client.event(self.on_ready)

        # Register slash commands
        @self.client.tree.command(name="scrape", description="Scrape data from IS")
        async def scrape(interaction: discord.Interaction):
            await interaction.response.defer()
            results = await asyncio.to_thread(self._do_scrape)
            if results is None:
                await interaction.followup.send("Login failed")
            elif results == []:
                await interaction.followup.send("Failed to retrieve shifts")
            else:
                self.shifts = results
                await interaction.followup.send(f"Scraped {len(results)} shifts")

    

    def _do_scrape(self):
        """Blocking scrape — runs in a thread via asyncio.to_thread"""
        login_url = "https://is.kofikofi.cz/"
        shift_url = "https://is.kofikofi.cz/index.php?what=read2&truck=0"
        session = requests.Session()
        response = session.post(login_url, data=self.payload)
        if not (response.status_code == 200 and "Burza" in response.text):
            session.close()
            return None  # login failed

        response = session.get(shift_url)
        session.close()
        if response.status_code != 200:
            return []  # page fetch failed

        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        for table in soup.find_all("table", class_="smeny_tab"):
            headline = table.find("th", class_="headline")
            if not headline:
                continue
            truck_name = headline.get_text(strip=True)
            for row in table.find_all("tr"):
                day_th = row.find("th")
                if not day_th:
                    continue
                day = day_th.get_text(strip=True)
                if day == "":
                    continue
                for td in row.find_all("td"):
                    cell_id = td.get("id")
                    if not cell_id:
                        continue
                    parts = cell_id.split("|")
                    if len(parts) != 3:
                        continue
                    position = parts[2]
                    for div in td.find_all("div", class_="neni_me"):
                        a = div.find("a")
                        if not a:
                            continue
                        name = a.get_text(strip=True)
                        text = div.get_text(" ", strip=True)
                        time_match = re.search(r"\((.*?)\)", text)
                        time = time_match.group(1) if time_match else None
                        results.append({
                            "truck": truck_name,
                            "day": day,
                            "position": position,
                            "name": name,
                            "time": time
                        })
        return results

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