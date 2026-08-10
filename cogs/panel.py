import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import (
    LayoutView,
    Container,
    TextDisplay,
    Separator,
    Select,
    Button,
    Modal,
    TextInput,
    Label,
    FileUpload,
)
from emojis import APPROVE, DENY, WARN, WRENCH


class CustomizeBotModal(Modal, title="Customize Confession Bot"):
    name_label = Label(
        text="Confession bot new name",
        component=TextInput(
            custom_id="bot_nick",
            style=discord.TextStyle.short,
            required=False,
            max_length=32,
            placeholder="Leave blank to keep the current name",
        ),
    )
    avatar_label = Label(
        text="Confession's avatar",
        description="Upload a new server profile avatar",
        component=FileUpload(
            custom_id="bot_avatar",
            required=False,
            min_values=0,
            max_values=1,
        ),
    )
    banner_label = Label(
        text="Confession's banner",
        description="Upload a new server profile banner",
        component=FileUpload(
            custom_id="bot_banner",
            required=False,
            min_values=0,
            max_values=1,
        ),
    )
    bio_label = Label(
        text="Confession's bio",
        component=TextInput(
            custom_id="bot_bio",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=190,
            placeholder="Short bio shown on the bot's server profile",
        ),
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        guild_id = interaction.guild_id
        settings = await self.bot.db.get_guild_settings(guild_id)

        nick_input = self.name_label.component.value.strip()
        bio_input = self.bio_label.component.value.strip()
        avatar_files = self.avatar_label.component.values
        banner_files = self.banner_label.component.values

        edit_kwargs = {}
        if nick_input:
            edit_kwargs["nick"] = nick_input
        if bio_input:
            edit_kwargs["bio"] = bio_input
        if avatar_files:
            edit_kwargs["avatar"] = await avatar_files[0].read()
        if banner_files:
            edit_kwargs["banner"] = await banner_files[0].read()

        try:
            if edit_kwargs:
                await guild.me.edit(**edit_kwargs)

            avatar_url = settings.get("avatar_url")
            if avatar_files:
                avatar_url = avatar_files[0].url
            elif edit_kwargs.get("avatar"):
                avatar_url = guild.me.display_avatar.url

            banner_url = settings.get("banner_url")
            if banner_files:
                banner_url = banner_files[0].url
            elif edit_kwargs.get("banner") and guild.me.banner:
                banner_url = guild.me.banner.url

            bot_nick = nick_input or settings.get("bot_nick")
            bot_bio = bio_input or settings.get("bot_bio")

            await self.bot.db.set_guild_customization(
                guild_id,
                bot_nick=bot_nick,
                avatar_url=avatar_url,
                banner_url=banner_url,
                bot_bio=bot_bio,
            )
            await self.bot.cache.clear_guild_config(guild_id)

            resp_view = LayoutView()
            resp_view.add_item(Container(
                TextDisplay(
                    f"# {APPROVE} Bot Customized\n\n"
                    "Your confession bot profile has been updated for this server."
                ),
            ))
            await interaction.response.send_message(view=resp_view, ephemeral=True)
        except Exception as e:
            err_view = LayoutView()
            err_view.add_item(Container(
                TextDisplay(
                    f"# {DENY} Failed to Update Bot\n\n{str(e)}\n\n"
                    "Make sure uploaded files are valid images and the bot has permission to change its profile."
                ),
            ))
            await interaction.response.send_message(view=err_view, ephemeral=True)


class AddWordModal(Modal, title="Add Blocked Words"):
    words_input = TextInput(
        label="Words to Block",
        style=discord.TextStyle.short,
        placeholder="Enter words separated by commas (e.g. badword, spam, test)",
        required=True,
        max_length=500,
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
        max_length=500,
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

    button_row = discord.ui.ActionRow()
    button_row.add_item(add_btn)
    button_row.add_item(rem_btn)
    button_row.add_item(clear_btn)

    container = Container(
        TextDisplay(f"# {WARN} Filter Words Management"),
        Separator(),
        TextDisplay(f"{words_text}\n\nUse the buttons below to add or remove words from the filter list."),
        button_row,
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
                description="Name, avatar, banner, and bio",
            ),
            discord.SelectOption(
                label="Filter words",
                value="filter_words",
                description="View and manage blocked words",
            ),
        ]
        super().__init__(
            placeholder="Select a customization option...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="panel_select_option",
        )

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        if selected == "customize":
            await interaction.response.send_modal(CustomizeBotModal(self.bot))
        elif selected == "filter_words":
            await send_filter_words_panel(interaction, self.bot)


class PanelView(LayoutView):
    def __init__(self, bot):
        super().__init__(timeout=300)

        select_row = discord.ui.ActionRow()
        select_menu = PanelSelectMenu(bot)
        select_row.add_item(select_menu)

        container = Container(
            TextDisplay(f"# {WRENCH} Customize your confession bot!"),
            Separator(),
            TextDisplay("Use the options below to customize the bot according to your server preferences."),
            select_row,
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
                    f"{DENY} Panel failed to load. Rebuild the bot: `docker compose up -d --build confess`",
                    ephemeral=True,
                )

    @panel.error
    async def panel_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"{DENY} You need **Administrator** permissions to use `/panel`.",
                    ephemeral=True,
                )


async def setup(bot):
    await bot.add_cog(PanelCog(bot))
