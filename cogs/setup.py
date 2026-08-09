import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay, Separator, ChannelSelect, Button
from config import Config
from logutil import send_guild_activity_log

class ReviewChannelSelectView(LayoutView):
    def __init__(self, bot, selected_confession_channel_ids: list[int]):
        super().__init__(timeout=300)
        self.bot = bot
        self.selected_confession_channel_ids = selected_confession_channel_ids

        # Button in same row as text
        skip_button = Button(
            label="Skip",
            style=discord.ButtonStyle.secondary,
            custom_id="skip_review_btn"
        )
        skip_button.callback = self.skip_review_callback

        # ChannelSelect must be wrapped in ActionRow for Components V2
        select_row = discord.ui.ActionRow()
        self.select_menu = ChannelSelect(
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            placeholder="Select review channel..."
        )
        self.select_menu.callback = self.review_channel_callback
        select_row.add_item(self.select_menu)

        # Use Section to put text and button on same line
        section = discord.ui.Section(
            "-# Select a channel where confessions awaiting review will be posted, or click the button to skip.",
            accessory=skip_button
        )

        container = Container(
            TextDisplay("# 📜 Review Channel\n\nChannels configured! Next, would you like to review confessions before they are posted?"),
            Separator(),
            section,
            select_row
        )
        self.add_item(container)

    async def review_channel_callback(self, interaction: discord.Interaction):
        review_channel = self.select_menu.values[0]
        guild_id = interaction.guild_id

        await self.bot.db.set_confession_channels(guild_id, self.selected_confession_channel_ids)
        await self.bot.db.set_review_channel(guild_id, review_channel.id)
        await self.bot.cache.clear_guild_config(guild_id)

        await send_guild_activity_log(
            self.bot,
            channel_id=Config.GUILD_LOG_CHANNEL_ID,
            title="Guild Setup Completed",
            description=(
                f"```diff\n+ Setup finished for {interaction.guild.name}\n```"
            ),
            guild=interaction.guild,
            fields=[
                ("Confession Channels", f"`{len(self.selected_confession_channel_ids)}`", True),
                ("Review Channel", f"<#{review_channel.id}>", True),
                ("Configured By", f"`{interaction.user}` (`{interaction.user.id}`)", False),
            ],
            color=0x438C53,
        )

        completion_view = CompletionView()
        await interaction.response.edit_message(view=completion_view)

    async def skip_review_callback(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id

        await self.bot.db.set_confession_channels(guild_id, self.selected_confession_channel_ids)
        await self.bot.db.set_review_channel(guild_id, None)
        await self.bot.cache.clear_guild_config(guild_id)

        await send_guild_activity_log(
            self.bot,
            channel_id=Config.GUILD_LOG_CHANNEL_ID,
            title="Guild Setup Completed",
            description=(
                f"```diff\n+ Setup finished for {interaction.guild.name}\n```"
            ),
            guild=interaction.guild,
            fields=[
                ("Confession Channels", f"`{len(self.selected_confession_channel_ids)}`", True),
                ("Review Channel", "`Skipped`", True),
                ("Configured By", f"`{interaction.user}` (`{interaction.user.id}`)", False),
            ],
            color=0x438C53,
        )

        completion_view = CompletionView()
        await interaction.response.edit_message(view=completion_view)

class CompletionView(LayoutView):
    def __init__(self):
        super().__init__(timeout=None)

        support_button = Button(
            label="Support",
            style=discord.ButtonStyle.link,
            url=Config.SUPPORT_SERVER_URL
        )

        # Use Section to put text and button on same line
        section = discord.ui.Section(
            "-# If you need any assistance with the bot, please join our support server.",
            accessory=support_button
        )

        container = Container(
            TextDisplay("# 🏁 You're done!\nSetup complete! You can now use `/confess` to submit confessions. If you need to make changes, you can use `/panel` to adjust settings at any time."),
            Separator(),
            section
        )
        self.add_item(container)

class ConfessionChannelsSelectView(LayoutView):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot

        # ChannelSelect must be wrapped in ActionRow for Components V2
        select_row = discord.ui.ActionRow()
        self.select_menu = ChannelSelect(
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=25,
            placeholder="Select confessions channels..."
        )
        self.select_menu.callback = self.confession_channels_callback
        select_row.add_item(self.select_menu)

        container = Container(
            TextDisplay("# 🕵️ Confessions channel\n\nThis process will walk you through setting up the Confession bot. Let's get started!"),
            Separator(),
            TextDisplay("First, please select the channels you'd like to use for confessions."),
            select_row
        )
        self.add_item(container)

    async def confession_channels_callback(self, interaction: discord.Interaction):
        selected_channels = self.select_menu.values
        selected_ids = [ch.id for ch in selected_channels]

        review_view = ReviewChannelSelectView(self.bot, selected_ids)
        await interaction.response.edit_message(view=review_view)

class SetupCog(commands.Cog, name="Setup"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Walk through setting up the Confession bot channels and configuration")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction):
        try:
            view = ConfessionChannelsSelectView(self.bot)
            await interaction.response.send_message(view=view)
        except Exception as e:
            logger.exception("Failed to send /setup LayoutView")
            from ui_helpers import schedule_error_report

            schedule_error_report(self.bot, e, interaction, "setup")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Setup UI failed to load. Rebuild the bot image so discord.py 2.6+ is installed:\n"
                    "`docker compose up -d --build confess`",
                    ephemeral=True,
                )

    @setup.error
    async def setup_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ You need **Administrator** permissions to run `/setup`.",
                    ephemeral=True,
                )

async def setup(bot):
    await bot.add_cog(SetupCog(bot))
