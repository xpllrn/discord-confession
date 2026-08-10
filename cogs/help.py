import logging
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay, Separator, Button
from config import Config
from emojis import STAR

logger = logging.getLogger(__name__)

class HelpCog(commands.Cog, name="Help"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Display information about the bot and available commands")
    async def help(self, interaction: discord.Interaction):
        support_btn = Button(
            label="Support Server",
            style=discord.ButtonStyle.link,
            url=Config.SUPPORT_SERVER_URL,
        )

        button_row = discord.ui.ActionRow()
        button_row.add_item(support_btn)

        commands_text = """**Available Commands:**

**For Everyone:**
• `/confess` - Submit an anonymous confession
• `/help` - Show this help message
• `/ping` - Check bot latency

**For Administrators:**
• `/setup` - Initial bot configuration (channels & review)
• `/panel` - Access customization options

**Features:**
• **Anonymous Confessions** - Submit secrets completely anonymously
• **Confession Buttons** - Confess, reply, or report on each post
• **Reply Threads** - Create discussion threads for confessions
• **Content Filter** - Block specific words from confessions
• **Review System** - Optional moderator approval before posting
• **Custom Avatar** - Set a unique bot avatar for your server"""

        try:
            container = Container(
                TextDisplay("## Anonymous Confession Bot"),
                Separator(),
                TextDisplay(commands_text),
                Separator(),
                TextDisplay("-# Need help? Join our support server for assistance!"),
                button_row,
            )

            view = LayoutView()
            view.add_item(container)

            await interaction.response.send_message(view=view, ephemeral=True)
        except Exception as e:
            logger.exception("Failed to send /help LayoutView, falling back to embed")
            from ui_helpers import schedule_error_report

            schedule_error_report(self.bot, e, interaction, "help")
            embed = discord.Embed(
                title="Anonymous Confession Bot",
                description=commands_text,
                color=discord.Color.blurple(),
            )
            link_view = discord.ui.View()
            link_view.add_item(support_btn)
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, view=link_view, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, view=link_view, ephemeral=True)

    @app_commands.command(name="ping", description="Check if the bot is online and show latency")
    async def ping(self, interaction: discord.Interaction):
        latency_ms = round(self.bot.latency * 1000)
        await interaction.response.send_message(
            f"{STAR} Pong! **{latency_ms}ms**",
            ephemeral=True,
        )

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
