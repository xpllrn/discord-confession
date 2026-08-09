import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay, Separator, Select, Button, Modal, TextInput
import aiohttp
import io

class AvatarModal(Modal, title="Set Bot Avatar"):
    avatar_url = TextInput(
        label="Image URL",
        style=discord.TextStyle.short,
        placeholder="Enter image URL (e.g., https://example.com/image.png)",
        required=True,
        max_length=500
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        url = self.avatar_url.value.strip()

        try:
            # Download the image
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise Exception(f"Could not download image (HTTP {resp.status})")
                    image_data = await resp.read()

            # Set guild-specific avatar
            await guild.me.edit(avatar=image_data)
            
            # Store avatar URL in database
            await self.bot.db.set_guild_avatar(guild.id, url)
            await self.bot.cache.clear_guild_config(guild.id)

            resp_view = LayoutView()
            resp_view.add_item(Container(
                TextDisplay("# ✅ Avatar Updated\n\nThe bot's avatar has been updated for this server!")
            ))
            await interaction.response.send_message(view=resp_view, ephemeral=True)

        except Exception as e:
            err_view = LayoutView()
            err_view.add_item(Container(
                TextDisplay(f"# ❌ Failed to Update Avatar\n\n{str(e)}\n\nMake sure the URL is a valid image link.")
            ))
            await interaction.response.send_message(view=err_view, ephemeral=True)

class AddWordModal(Modal, title="Add Blocked Words"):
    words_input = TextInput(
        label="Words to Block",
        style=discord.TextStyle.short,
        placeholder="Enter words separated by commas (e.g. badword, spam, test)",
        required=True,
        max_length=500
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id

        settings = await self.bot.db.get_guild_settings(guild_id)
        current_words = settings.get("filter_words", [])

        raw_words = [w.strip().lower() for w in self.words_input.value.split(",") if w.strip()]
        updated_words = list(set(current_words + raw_words))

        await self.bot.db.set_filter_words(guild_id, updated_words)
        await self.bot.cache.clear_guild_config(guild_id)

        await send_filter_words_panel(interaction, self.bot, updated_words)

class RemoveWordModal(Modal, title="Remove Blocked Words"):
    words_input = TextInput(
        label="Words to Remove",
        style=discord.TextStyle.short,
        placeholder="Enter words separated by commas to remove",
        required=True,
        max_length=500
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id

        settings = await self.bot.db.get_guild_settings(guild_id)
        current_words = settings.get("filter_words", [])

        remove_targets = set(w.strip().lower() for w in self.words_input.value.split(",") if w.strip())
        updated_words = [w for w in current_words if w.lower() not in remove_targets]

        await self.bot.db.set_filter_words(guild_id, updated_words)
        await self.bot.cache.clear_guild_config(guild_id)

        await send_filter_words_panel(interaction, self.bot, updated_words)

async def send_filter_words_panel(interaction: discord.Interaction, bot, filter_words: list[str] = None):
    guild_id = interaction.guild_id
    if filter_words is None:
        settings = await bot.db.get_guild_settings(guild_id)
        filter_words = settings.get("filter_words", [])

    if filter_words:
        formatted_list = ", ".join(f"`{w}`" for w in filter_words)
        words_text = f"**Current Blocked Words ({len(filter_words)}):**\n{formatted_list}"
    else:
        words_text = "**Current Blocked Words:**\n*No words are currently blocked.*"

    add_btn = Button(label="Add Word", style=discord.ButtonStyle.secondary)
    async def add_cb(inter: discord.Interaction):
        await inter.response.send_modal(AddWordModal(bot))
    add_btn.callback = add_cb

    rem_btn = Button(label="Remove Word", style=discord.ButtonStyle.secondary)
    async def rem_cb(inter: discord.Interaction):
        await inter.response.send_modal(RemoveWordModal(bot))
    rem_btn.callback = rem_cb

    clear_btn = Button(label="Clear All", style=discord.ButtonStyle.secondary)
    async def clear_cb(inter: discord.Interaction):
        await bot.db.set_filter_words(guild_id, [])
        await bot.cache.clear_guild_config(guild_id)
        await send_filter_words_panel(inter, bot, [])
    clear_btn.callback = clear_cb

    # Buttons must be wrapped in ActionRow for Components V2
    button_row = discord.ui.ActionRow()
    button_row.add_item(add_btn)
    button_row.add_item(rem_btn)
    button_row.add_item(clear_btn)

    container = Container(
        TextDisplay("# 🚫 Filter Words Management"),
        Separator(),
        TextDisplay(f"{words_text}\n\nUse the buttons below to add or remove words from the filter list."),
        button_row
    )

    view = LayoutView()
    view.add_item(container)

    if interaction.response.is_done():
        await interaction.followup.send(view=view, ephemeral=True)
    else:
        await interaction.response.send_message(view=view, ephemeral=True)

class PanelSelectMenu(Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(
                label="Customize",
                value="customize",
                description="Configure confession options and settings"
            ),
            discord.SelectOption(
                label="Filter words",
                value="filter_words",
                description="View and manage blocked words"
            )
        ]
        super().__init__(
            placeholder="Select a customization option...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="panel_select_option"
        )

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        if selected == "customize":
            # Get current guild settings
            settings = await self.bot.db.get_guild_settings(interaction.guild_id)
            avatar_url = settings.get("avatar_url")
            
            if avatar_url:
                avatar_text = f"**Bot Avatar:**\n[Current Avatar]({avatar_url})"
            else:
                avatar_text = "**Bot Avatar:**\n*Using default avatar*"
            
            # Create avatar button
            avatar_btn = Button(label="Change Avatar", style=discord.ButtonStyle.primary)
            async def avatar_cb(inter: discord.Interaction):
                await inter.response.send_modal(AvatarModal(self.bot))
            avatar_btn.callback = avatar_cb
            
            button_row = discord.ui.ActionRow()
            button_row.add_item(avatar_btn)
            
            container = Container(
                TextDisplay("# 🎨 Customize Bot"),
                Separator(),
                TextDisplay(f"{avatar_text}\n\nClick the button below to upload a new avatar for this server."),
                button_row
            )
            view = LayoutView()
            view.add_item(container)
            await interaction.response.send_message(view=view, ephemeral=True)
        elif selected == "filter_words":
            await send_filter_words_panel(interaction, self.bot)

class PanelView(LayoutView):
    def __init__(self, bot):
        super().__init__(timeout=300)
        
        # Select menu must be wrapped in ActionRow for Components V2
        select_row = discord.ui.ActionRow()
        select_menu = PanelSelectMenu(bot)
        select_row.add_item(select_menu)
        
        container = Container(
            TextDisplay("# ⚙️ Customize your confession bot!"),
            Separator(),
            TextDisplay("Use the options below to customize the bot according to your server preferences."),
            select_row
        )
        self.add_item(container)

class PanelCog(commands.Cog, name="Panel"):
    def __init__(self, bot):
        self.bot = bot

    async def send_panel(self, interaction: discord.Interaction):
        view = PanelView(self.bot)
        if interaction.response.is_done():
            await interaction.followup.send(view=view, ephemeral=True)
        else:
            await interaction.response.send_message(view=view, ephemeral=True)

    @app_commands.command(name="panel", description="Open the confession bot customization panel")
    @app_commands.checks.has_permissions(administrator=True)
    async def panel(self, interaction: discord.Interaction):
        try:
            await self.send_panel(interaction)
        except Exception as e:
            import logging
            from ui_helpers import schedule_error_report

            logging.getLogger(__name__).exception("Failed to send /panel LayoutView")
            schedule_error_report(self.bot, e, interaction, "panel")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Panel failed to load. Rebuild the bot: `docker compose up -d --build confess`",
                    ephemeral=True,
                )

    @panel.error
    async def panel_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ You need **Administrator** permissions to use `/panel`.",
                    ephemeral=True,
                )

async def setup(bot):
    await bot.add_cog(PanelCog(bot))
