import discord
import aiohttp
import yaml
from discord import app_commands
from discord.ext import commands
from datetime import datetime

with open('config.yml', 'r') as file:
    data = yaml.safe_load(file)

embed_color = data["General"]["EMBED_COLOR"]
staff_roles = data["Staff"]["STAFF_ROLES"]

GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
EMBED_CHAR_LIMIT = 4096

def load_system_prompt():
    with open("prompt.txt", "r", encoding="utf-8") as file:
        return file.read().strip()

class AIModal(discord.ui.Modal, title="Ask CookieAI"):
    def __init__(self, type: str = None):
        super().__init__(timeout=None)
        self.type = type

    name = discord.ui.TextInput(
        label="What is your prompt?",
        max_length=4000,
        style=discord.TextStyle.long,
    )

    async def fetch_ai_response(self, prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}",
        }
        system_prompt = load_system_prompt()

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(GROQ_API_URL, json=payload, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "No response from AI.")
                return f"Error: {resp.status} - {await resp.text()}"

    async def send_embeds(self, interaction: discord.Interaction, response: str):
        embeds = [
            discord.Embed(
                title="CookieAI Response" if i == 0 else "Continued...",
                description=chunk,
                color=discord.Color.blue()
            )
            for i, chunk in enumerate([response[i:i + EMBED_CHAR_LIMIT] for i in range(0, len(response), EMBED_CHAR_LIMIT)])
        ]

        if self.type:
            await interaction.response.edit_message(embed=embeds[0], view=None)
            for embed in embeds[1:]:
                await interaction.channel.send(embed=embed)
        else:
            await interaction.followup.send(embed=embeds[0])
            for embed in embeds[1:]:
                await interaction.channel.send(embed=embed)

    async def on_submit(self, interaction: discord.Interaction):
        if not self.type:
            await interaction.response.defer(thinking=True)
        
        response = await self.fetch_ai_response(self.name.value)
        await self.send_embeds(interaction, response)

class AIDropdown(discord.ui.Select):
    def __init__(self):
            options = [
                discord.SelectOption(label='FiveM'),
                discord.SelectOption(label='Discord'),
            ]
            super().__init__(placeholder='What type of AI would you like?', min_values=1, max_values=1, options=options, custom_id="ai_dropdown:1")

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "FiveM":
            embed = discord.Embed(title="CookieAI", description="Select the type of FiveM AI you would like to use!", color=discord.Color.from_str(embed_color))
            embed.timestamp = datetime.now()

            await interaction.response.edit_message(embed=embed, view=FiveMAIDropdownView())
        elif self.values[0] == "Discord":
            await interaction.response.edit_message(content="Discord AI selected!")

class AIDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(AIDropdown())

class FiveMAIDropdown(discord.ui.Select):
    def __init__(self):
            options = [
                discord.SelectOption(label='FiveM Scripts'),
            ]
            super().__init__(placeholder='What type of AI would you like?', min_values=1, max_values=1, options=options, custom_id="fivem_ai_dropdown:1")

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "FiveM Scripts":
            embed = discord.Embed(title="CookieAI", description="Select the type of FiveM Scripts AI you would like to use!", color=discord.Color.from_str(embed_color))
            embed.timestamp = datetime.now()
            await interaction.response.edit_message(embed=embed, view=FiveMScripsAIDropdownView())

class FiveMAIDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(FiveMAIDropdown())

class FiveMScripsAIDropdown(discord.ui.Select):
    def __init__(self):
            options = [
                discord.SelectOption(label='Redesign UI'),
                discord.SelectOption(label='Code New Scripts'),
            ]
            super().__init__(placeholder='What type of AI would you like?', min_values=1, max_values=1, options=options, custom_id="fivem_scrips_ai_dropdown:1")

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "Redesign UI":
            await interaction.response.send_modal(AIModal("Redesign UI"))
        elif self.values[0] == "Code New Scripts":
            await interaction.response.send_modal(AIModal("Code New Scripts"))

class FiveMScripsAIDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(FiveMScripsAIDropdown())

class AICog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.bot.add_view(AIDropdownView())
        self.bot.add_view(FiveMAIDropdownView())
        self.bot.add_view(FiveMScripsAIDropdownView())

    @app_commands.command(name="ai", description="Asks AI something!")
    async def ai(self, interaction: discord.Interaction) -> None:
        if any(role.id in staff_roles for role in interaction.user.roles):
            await interaction.response.send_modal(AIModal())
        else:
            embed = discord.Embed(title="CookieAI", description="Select the type of AI you would like to use!", color=discord.Color.from_str(embed_color))
            embed.set_author(name=interaction.user, icon_url=interaction.user.avatar.url)
            embed.timestamp = datetime.now()

            await interaction.response.send_message(embed=embed, view=AIDropdownView())

async def setup(bot: commands.Bot):
    await bot.add_cog(AICog(bot))