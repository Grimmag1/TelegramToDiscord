import discord
from discord import app_commands, datetime
import config
import requests
from bs4 import BeautifulSoup
import asyncio
import re
import pandas as pd
from datetime import datetime

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
        self.shifts = pd.DataFrame()
        # Register event handlers
        self.client.event(self.on_ready)

        # Register slash commands
        @self.client.tree.command(name="scrape", description="Scrape data from IS")
        async def scrape(interaction: discord.Interaction):
            await interaction.response.defer()
            results = await asyncio.to_thread(self._do_scrape)
            if results is None:
                await interaction.followup.send("Login failed")
            elif results.empty:
                await interaction.followup.send("Failed to retrieve shifts")
            else:
                self.shifts = results
                await interaction.followup.send(f"Scraped {len(results)} shifts")

        @self.client.tree.command(name="today", description="Show shifts for today")
        @app_commands.describe(location="Which truck to show")
        @app_commands.choices(location=[
            #app_commands.Choice(name="All", value="All"),
            app_commands.Choice(name="Batch Brew", value="Batch Brew"),
            app_commands.Choice(name="Česká", value="Česká"),
            app_commands.Choice(name="Dětská nemocnice", value="Dětská nemocnice"),
            app_commands.Choice(name="Fakultní nemocnice Brno", value="Fakultní nemocnice Brno"),
            app_commands.Choice(name="Grand", value="Grand"),
            app_commands.Choice(name="Hlavní nádraží", value="Hlavní nádraží"),
            app_commands.Choice(name="Husitská", value="Husitská"),
            app_commands.Choice(name="Janáček", value="Janáček"),
            app_commands.Choice(name="Kampus", value="Kampus"),
            app_commands.Choice(name="Kampus 2", value="Kampus 2"),
            app_commands.Choice(name="Maliňák", value="Maliňák"),
            app_commands.Choice(name="Moravák", value="Moravák"),
            app_commands.Choice(name="MUNI", value="MUNI"),
            app_commands.Choice(name="Obilňák", value="Obilňák"),
            app_commands.Choice(name="Svatá Anna", value="Svatá Anna"),
            app_commands.Choice(name="Svoboďák", value="Svoboďák"),
            app_commands.Choice(name="Šelepka", value="Šelepka"),
            app_commands.Choice(name="Šilingrovo náměstí", value="Šilingrovo náměstí"),
            app_commands.Choice(name="Technopark", value="Technopark")
        ])
        async def today(interaction: discord.Interaction, location: app_commands.Choice[str]):
            if self.shifts.empty:
                await interaction.response.send_message("No shift data available. Please run /scrape first.")
                return
            # Get today's day name in Czech
            today_english = datetime.now().strftime('%A')

            # Convert to Czech
            czech_day = None
            for czech, english in config.CZECH_TO_ENGLISH_DAYS.items():
                if english == today_english:
                    czech_day = czech
                    break
            if czech_day is None:
                await interaction.response.send_message("Could not determine today's day.")
                return
            
            today_shifts = self.shifts[(self.shifts['truck'] == location.value) & (self.shifts['day'] == czech_day)]
            if today_shifts.empty:
                await interaction.response.send_message(f"No shifts found for {location.value} today.")
                return

            await interaction.response.send_message(f"Shifts for {location.value} on {czech_day}:\n" + "\n".join(f"{row['time']} - {row['name']} ({row['position']})" for _, row in today_shifts.iterrows()))
        
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
            return pd.DataFrame()  # page fetch failed

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
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results)
        df['day_categorical'] = pd.Categorical(df['day'], categories=config.DAY_ORDER, ordered=True)
        df['position_priority'] = df['position'].apply(self._get_position_priority)
        df['start_time_minutes'] = df['time'].apply(self._get_start_time)
        
        df = df.sort_values(
            ['day_categorical', 'truck', 'position_priority', 'start_time_minutes']
        ).reset_index(drop=True)

        return df
    
    # Helper function to assign position priority
    def _get_position_priority(self, position):
        """Assign priority to positions for sorting"""
        pos_lower = position.lower()
        
        if 'barista' in pos_lower and ('dopoledne' in pos_lower or 'vikend' in pos_lower and 'odpoledne' not in pos_lower):
            return 1
        elif 'prisluha' in pos_lower and ('dopoledne' in pos_lower or 'vikend' in pos_lower and 'odpoledne' not in pos_lower):
            return 2
        elif 'barista' in pos_lower and 'odpoledne' in pos_lower:
            return 3
        elif 'prisluha' in pos_lower and 'odpoledne' in pos_lower:
            return 4
        else:
            return 5

    # Helper function to extract start time
    def _get_start_time(self, time_str):
        """Extract start time from time string for sorting"""
        try:
            start = time_str.split('-')[0].strip()
            hours, minutes = start.split(':')
            return int(hours) * 60 + int(minutes)  # Convert to minutes for easy comparison
        except:
            return 9999  # Put invalid times at the end

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