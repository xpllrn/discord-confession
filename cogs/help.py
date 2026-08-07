import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay, Separator, Button
from config import Config

class HelpCog(commands.Cog, name="Help"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Display information about the bot and available commands")
    async def help(self, interaction: discord.Interaction):
        # Create support server button
        support_btn = Button(
            label="Support Server",
            style=discord.ButtonStyle.link,
            url=Config.SUPPORT_SERVER_URL
        )
        
        button_row = discord.ui.ActionRow()
        button_row.add_item(support_btn)
        
        # Build help text sections
        commands_text = """**Available Commands:**

**For Everyone:**
• `/confess` - Submit an anonymous confession
• `/help` - Show this help message

**For Administrators:**
• `/setup` - Initial bot configuration (channels & review)
• `/panel` - Access customization options

**Features:**
• **Anonymous Confessions** - Submit secrets completely anonymously
• **Confession Buttons** - Quick confess and reply options on each post
• **Reply Threads** - Create discussion threads for confessions
• **Content Filter** - Block specific words from confessions
• **Review System** - Optional moderator approval before posting
• **Custom Avatar** - Set a unique bot avatar for your server"""

        container = Container(
            TextDisplay("# 🕵️ Anonymous Confession Bot"),
            Separator(),
            TextDisplay(commands_text),
            Separator(),
            TextDisplay("-# Need help? Join our support server for assistance!"),
            button_row
        )
        
        view = LayoutView()
        view.add_item(container)
        
        await interaction.response.send_message(view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
