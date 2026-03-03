import discord
from discord import app_commands
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
        self.paginated_messages = {}  # message_id -> {trucks, index, czech_day, day_shifts}

        self.location_choices = [
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
        ]
        self.day_choices = [
            app_commands.Choice(name="Pondělí", value="Pondělí"),
            app_commands.Choice(name="Úterý", value="Úterý"),
            app_commands.Choice(name="Středa", value="Středa"),
            app_commands.Choice(name="Čtvrtek", value="Čtvrtek"),
            app_commands.Choice(name="Pátek", value="Pátek"),
            app_commands.Choice(name="Sobota", value="Sobota"),
            app_commands.Choice(name="Neděle", value="Neděle")
        ]
        # Register event handlers
        self.client.event(self.on_ready)
        self.client.event(self.on_raw_reaction_add)




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
        @app_commands.choices(location=self.location_choices)
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

            await interaction.response.send_message(embed=self._create_embed(today_shifts, location.value, czech_day))

        @self.client.tree.command(name="today-all", description="Show shifts for all trucks today")
        async def today_all(interaction: discord.Interaction):
            if self.shifts.empty:
                await interaction.response.send_message("No shift data available. Please run /scrape first.")
                return

            today_english = datetime.now().strftime('%A')
            czech_day = None
            for czech, english in config.CZECH_TO_ENGLISH_DAYS.items():
                if english == today_english:
                    czech_day = czech
                    break
            if czech_day is None:
                await interaction.response.send_message("Could not determine today's day.")
                return

            day_shifts = self.shifts[self.shifts['day'] == czech_day]
            if day_shifts.empty:
                await interaction.response.send_message("No shifts found for today.")
                return

            trucks = list(day_shifts['truck'].unique())
            first_shifts = day_shifts[day_shifts['truck'] == trucks[0]]
            embed = self._create_embed(first_shifts, trucks[0], czech_day)
            embed.set_footer(text=f"{trucks[0]}  •  1 / {len(trucks)}")

            await interaction.response.send_message(embed=embed)
            message = await interaction.original_response()
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")

            self.paginated_messages[message.id] = {
                "mode": "trucks",
                "trucks": trucks,
                "index": 0,
                "czech_day": czech_day,
                "day_shifts": day_shifts,
            }

        @self.client.tree.command(name="week", description="Show shifts for a specific truck for the whole week")
        @app_commands.describe(location="Which truck to show")
        @app_commands.choices(location=self.location_choices)
        async def week(interaction: discord.Interaction, location: app_commands.Choice[str]):
            if self.shifts.empty:
                await interaction.response.send_message("No shift data available. Please run /scrape first.")
                return

            truck_shifts = self.shifts[self.shifts['truck'] == location.value]
            if truck_shifts.empty:
                await interaction.response.send_message(f"No shifts found for {location.value}.")
                return

            days = [d for d in config.DAY_ORDER if d in truck_shifts['day'].values]

            first_day_shifts = truck_shifts[truck_shifts['day'] == days[0]]
            embed = self._create_embed(first_day_shifts, location.value, days[0])
            embed.set_footer(text=f"{days[0]}  •  1 / {len(days)}")

            await interaction.response.send_message(embed=embed)
            message = await interaction.original_response()
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")

            self.paginated_messages[message.id] = {
                "mode": "days",
                "days": days,
                "index": 0,
                "truck": location.value,
                "truck_shifts": truck_shifts,
            }

        @self.client.tree.command(name="day", description="Show shifts for a specific truck for a given day")
        @app_commands.describe(day="What day to show", location="Which truck to show")
        @app_commands.choices(day=self.day_choices, location=self.location_choices)
        async def day(interaction: discord.Interaction, day: app_commands.Choice[str], location: app_commands.Choice[str]):
            if self.shifts.empty:
                await interaction.response.send_message("No shift data available. Please run /scrape first.")
                return
            day_truck_shifts = self.shifts[(self.shifts['truck'] == location.value) & (self.shifts['day'] == day.value)]
            if day_truck_shifts.empty:
                await interaction.response.send_message(f"No shifts found for {location.value} on {day.value}.")
                return
            embed = self._create_embed(day_truck_shifts, location.value, day.value)
            await interaction.response.send_message(embed=embed)

    def _create_embed(self, today_shifts, location_name, day):
        def format_group(df_group):
            if df_group.empty:
                return "-"
            return "\n".join(f"{row['name']} ({row['time']})" for _, row in df_group.iterrows())
        dop_barista = today_shifts[today_shifts['position_priority'] == 1]
        dop_prisluha = today_shifts[today_shifts['position_priority'] == 2]
        odp_barista  = today_shifts[today_shifts['position_priority'] == 3]
        odp_prisluha = today_shifts[today_shifts['position_priority'] == 4]

        embed = discord.Embed(title=f"{location_name} — {day}", color=0x88cc00)
        embed.add_field(name="☀️ **Dopoledne — Barista**", value=format_group(dop_barista), inline=True)
        embed.add_field(name="**Příluha**", value=format_group(dop_prisluha), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)  # spacer to end row
        embed.add_field(name="🌙 **Odpoledne — Barista**", value=format_group(odp_barista), inline=True)
        embed.add_field(name="**Příluha**", value=format_group(odp_prisluha), inline=True)
        return embed

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
        df['truck_categorical'] = pd.Categorical(df['truck'], categories=config.TRUCK_ORDER, ordered=True)
        df['position_priority'] = df['position'].apply(self._get_position_priority)
        df['start_time_minutes'] = df['time'].apply(self._get_start_time)

        df = df.sort_values(
            ['day_categorical', 'truck_categorical', 'position_priority', 'start_time_minutes']
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
        elif 'barista' in pos_lower:
            return 3
        elif 'prisluha' in pos_lower:
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

    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.client.user.id:
            return
        if payload.message_id not in self.paginated_messages:
            return
        emoji = str(payload.emoji)
        if emoji not in ("⬅️", "➡️"):
            return

        state = self.paginated_messages[payload.message_id]
        mode = state["mode"]
        items = state["trucks"] if mode == "trucks" else state["days"]
        index = state["index"]

        if emoji == "➡️":
            index = (index + 1) % len(items)
        else:
            index = (index - 1) % len(items)
        state["index"] = index

        if mode == "trucks":
            truck = items[index]
            shifts = state["day_shifts"][state["day_shifts"]["truck"] == truck]
            embed = self._create_embed(shifts, truck, state["czech_day"])
            embed.set_footer(text=f"{truck}  •  {index + 1} / {len(items)}")
        else:
            day = items[index]
            shifts = state["truck_shifts"][state["truck_shifts"]["day"] == day]
            embed = self._create_embed(shifts, state["truck"], day)
            embed.set_footer(text=f"{day}  •  {index + 1} / {len(items)}")

        channel = self.client.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        await message.edit(embed=embed)

        # Remove the user's reaction so they can navigate again
        user = await self.client.fetch_user(payload.user_id)
        await message.remove_reaction(payload.emoji, user)

    async def on_ready(self):
        """Called when the Discord bot is ready"""
        print(f'Logged in as {self.client.user}')
        print('Discord bot is ready!')
        results = await asyncio.to_thread(self._do_scrape)
        if results is not None and not results.empty:
            self.shifts = results
            print(f"Initial scrape completed. Got {len(results)} shift records.")
        else:
            print("Initial scrape failed or returned no data.")


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