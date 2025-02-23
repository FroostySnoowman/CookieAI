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

GROQ_API_KEY = data["API"]["GROQ_API_KEY"]
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

EMBED_CHAR_LIMIT = 4096

def load_system_prompt() -> str:
    with open("prompt.txt", "r", encoding="utf-8") as file:
        return file.read().strip()

class AIModal(discord.ui.Modal, title="Ask CookieAI"):
    def __init__(self, ai_type: str = None):
        super().__init__(timeout=None)
        self.ai_type = ai_type

    message = discord.ui.TextInput(
        label="What is your prompt?",
        max_length=4000,
        style=discord.TextStyle.long,
    )

    def get_system_prompt(self) -> str:
        base_prompt = load_system_prompt()

        type_prompts = {
            "redesign_ui": " Your task is to **redesign the provided code** entirely, making it **modern, clean, and optimized for user experience**.",
            "code_new_scripts": " Your task is to **develop new FiveM scripts** from the ground up or **improve existing ones** for better performance and functionality.",
            "code_new_bots": " Your task is to **create new Discord bots** in the specified programming language. Default to `discord.py` if not specified.",
            "bug_error_fixing": " Your task is to **analyze code, identify bugs and errors, and provide efficient fixes** while maintaining code quality.",
        }

        return base_prompt + type_prompts.get(self.ai_type, "")

    async def fetch_ai_response(self, prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GROQ_API_KEY}",
        }
        system_prompt = self.get_system_prompt()

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

        if self.ai_type:
            await interaction.response.edit_message(embed=embeds[0], view=None)
            for embed in embeds[1:]:
                await interaction.channel.send(embed=embed)
        else:
            await interaction.followup.send(embed=embeds[0])
            for embed in embeds[1:]:
                await interaction.channel.send(embed=embed)

    async def on_submit(self, interaction: discord.Interaction):
        if not self.ai_type:
            await interaction.response.defer(thinking=True)

        response = await self.fetch_ai_response(self.message.value)
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
            embed = discord.Embed(title="CookieAI", description="Select the type of Discord AI you would like to use!", color=discord.Color.from_str(embed_color))
            embed.timestamp = datetime.now()

            await interaction.response.edit_message(embed=embed, view=DiscordAIDropdownView())

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
        await interaction.response.send_modal(AIModal(self.values[0]))

class FiveMScripsAIDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(FiveMScripsAIDropdown())

class DiscordAIDropdown(discord.ui.Select):
    def __init__(self):
            options = [
                discord.SelectOption(label='Discord Bots'),
            ]
            super().__init__(placeholder='What type of AI would you like?', min_values=1, max_values=1, options=options, custom_id="discord_ai_dropdown:1")

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "Discord Bots":
            embed = discord.Embed(title="CookieAI", description="Select the type of Discord Bots AI you would like to use!", color=discord.Color.from_str(embed_color))
            embed.timestamp = datetime.now()
            await interaction.response.edit_message(embed=embed, view=DiscordBotsAIDropdownView())

class DiscordAIDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(DiscordAIDropdown())

class DiscordBotsAIDropdown(discord.ui.Select):
    def __init__(self):
            options = [
                discord.SelectOption(label='Code New Bots'),
                discord.SelectOption(label='Bug/Error Fixing'),
            ]
            super().__init__(placeholder='What type of AI would you like?', min_values=1, max_values=1, options=options, custom_id="discord_bots_ai_dropdown:1")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AIModal(self.values[0]))

class DiscordBotsAIDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(DiscordBotsAIDropdown())

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