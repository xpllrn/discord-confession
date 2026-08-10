import logging
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay, Separator, Button, Modal, TextInput, Label, FileUpload

from config import Config
from emojis import APPROVE, DENY, WARN, APPROVE_EMOJI, DENY_EMOJI, TICKET
from logutil import send_report_log
from ui_helpers import schedule_error_report, handle_interaction_error, is_unknown_interaction

logger = logging.getLogger(__name__)


async def _report_error(
    bot,
    error: Exception,
    interaction: discord.Interaction = None,
    command_used: str = "unknown",
    notify_user: bool = False,
):
    if notify_user and interaction:
        await handle_interaction_error(bot, interaction, error, command_used)
    else:
        schedule_error_report(bot, error, interaction, command_used)


def build_confession_embed(confession_num: int, content: str, image_url: str | None = None) -> discord.Embed:
    embed = discord.Embed(
        title=f"Anonymous Confession #{confession_num}",
        description=content,
        color=discord.Color.blurple(),
    )
    if image_url:
        embed.set_image(url=image_url)
    return embed


class ReportModal(Modal, title="Report Confession"):
    reason_input = TextInput(
        label="Reason",
        style=discord.TextStyle.paragraph,
        placeholder="Why are you reporting this confession?",
        required=True,
        min_length=3,
        max_length=500,
    )

    def __init__(self, bot, confession_num: int):
        super().__init__()
        self.bot = bot
        self.confession_num = confession_num

    async def on_submit(self, interaction: discord.Interaction):
        try:
            record = await self.bot.db.get_confession(interaction.guild_id, self.confession_num)
            if not record:
                err_view = LayoutView()
                err_view.add_item(Container(TextDisplay(f"{DENY} Could not find that confession.")))
                await interaction.response.send_message(view=err_view, ephemeral=True)
                return

            author_id = record.get("author_id") or 0
            author_name = "unknown"
            if author_id:
                user = self.bot.get_user(author_id)
                if user is None:
                    try:
                        user = await self.bot.fetch_user(author_id)
                    except Exception:
                        user = None
                if user:
                    author_name = str(user)

            await send_report_log(
                self.bot,
                channel_id=Config.REPORT_LOG_CHANNEL_ID,
                confession_num=self.confession_num,
                confession_content=record.get("content", ""),
                author_id=author_id,
                author_name=author_name,
                reporter=interaction.user,
                reason=self.reason_input.value.strip(),
                guild=interaction.guild,
            )

            ok_view = LayoutView()
            ok_view.add_item(Container(
                TextDisplay(f"## {APPROVE} Report Submitted"),
                Separator(),
                TextDisplay("Thanks — your report has been sent to the bot staff for review."),
            ))
            await interaction.response.send_message(view=ok_view, ephemeral=True)
        except Exception as e:
            await _report_error(self.bot, e, interaction, "report")
            err_view = LayoutView()
            err_view.add_item(Container(TextDisplay(f"{DENY} Failed to submit report. Please try again.")))
            if interaction.response.is_done():
                await interaction.followup.send(view=err_view, ephemeral=True)
            else:
                await interaction.response.send_message(view=err_view, ephemeral=True)


class ReplyModal(Modal, title="Reply to Confession"):
    confession_input = TextInput(
        label="Your Reply Confession",
        style=discord.TextStyle.paragraph,
        placeholder="Type your anonymous reply here...",
        required=True,
        min_length=5,
        max_length=2000,
    )

    def __init__(self, bot, original_message, confession_num: int):
        super().__init__()
        self.bot = bot
        self.original_message = original_message
        self.confession_num = confession_num

    async def _get_or_create_thread(self):
        existing_thread = getattr(self.original_message, "thread", None)
        if existing_thread:
            return existing_thread
        thread_name = f"Confession #{self.confession_num} Replies"
        return await self.original_message.create_thread(name=thread_name)

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        confession_text = self.confession_input.value
        author_id = interaction.user.id

        settings = await self.bot.cache.get_guild_config(guild_id)
        if not settings:
            settings = await self.bot.db.get_guild_settings(guild_id)
            await self.bot.cache.set_guild_config(guild_id, settings)

        filter_words = settings.get("filter_words", [])
        review_channel_id = settings.get("review_channel_id")

        for word in filter_words:
            if word.lower() in confession_text.lower():
                err_view = LayoutView()
                err_view.add_item(Container(
                    TextDisplay(f"## {WARN} Blocked Content"),
                    Separator(),
                    TextDisplay("Your confession contains prohibited words configured by the server administration."),
                ))
                await interaction.response.send_message(view=err_view, ephemeral=True)
                return

        try:
            reply_num = await self.bot.db.next_reply_num(guild_id, self.confession_num)

            # Review enabled: do NOT create a thread until approved
            if review_channel_id:
                review_channel = interaction.guild.get_channel(review_channel_id)
                if not review_channel:
                    try:
                        review_channel = await interaction.guild.fetch_channel(review_channel_id)
                    except Exception:
                        review_channel = None

                if review_channel:
                    await self.bot.db.create_reply(
                        guild_id, self.confession_num, reply_num, confession_text, author_id, status="pending"
                    )
                    review_view = ReplyReviewActionView(
                        self.bot,
                        reply_num,
                        confession_text,
                        self.original_message,
                        self.confession_num,
                        guild_id,
                    )
                    await review_channel.send(view=review_view)

                    resp_view = LayoutView()
                    resp_view.add_item(Container(
                        TextDisplay(f"## {WARN} Reply Sent for Review"),
                        Separator(),
                        TextDisplay(
                            "Your anonymous reply has been submitted for moderator review. "
                            "It will appear in the thread once approved!"
                        ),
                    ))
                    await interaction.response.send_message(view=resp_view, ephemeral=True)
                    return

            # No review: create thread only now, then post
            await self.bot.db.create_reply(
                guild_id, self.confession_num, reply_num, confession_text, author_id, status="posted"
            )
            existing_thread = await self._get_or_create_thread()

            reply_embed = discord.Embed(
                title=f"🕵️ Anonymous Reply #{reply_num}",
                description=confession_text,
                color=discord.Color.blurple(),
            )

            thread_view = discord.ui.View(timeout=None)
            confess_btn = discord.ui.Button(
                label="Confess",
                style=discord.ButtonStyle.grey,
                custom_id=f"thread_confess_btn_{self.confession_num}_{reply_num}",
            )

            async def thread_confess_cb(inter: discord.Interaction):
                modal = ConfessionModal(self.bot)
                await inter.response.send_modal(modal)

            confess_btn.callback = thread_confess_cb
            thread_view.add_item(confess_btn)

            await existing_thread.send(embed=reply_embed, view=thread_view)

            resp_view = LayoutView()
            resp_view.add_item(Container(
                TextDisplay(f"## {APPROVE} Reply Posted"),
                Separator(),
                TextDisplay("Your anonymous reply has been posted in the thread!"),
            ))
            await interaction.response.send_message(view=resp_view, ephemeral=True)

        except Exception as e:
            await _report_error(self.bot, e, interaction, "reply")
            err_view = LayoutView()
            err_view.add_item(Container(
                TextDisplay(f"## {DENY} Submission Error"),
                Separator(),
                TextDisplay(f"An error occurred: {e}"),
            ))
            if interaction.response.is_done():
                await interaction.followup.send(view=err_view, ephemeral=True)
            else:
                await interaction.response.send_message(view=err_view, ephemeral=True)


class ReplyReviewActionView(LayoutView):
    def __init__(
        self,
        bot,
        reply_num: int,
        content_text: str,
        original_message: discord.Message,
        confession_num: int,
        guild_id: int,
    ):
        super().__init__(timeout=None)
        self.bot = bot
        self.reply_num = reply_num
        self.content_text = content_text
        self.original_message = original_message
        self.confession_num = confession_num
        self.guild_id = guild_id

        self.approve_btn = Button(
            label="Approve",
            style=discord.ButtonStyle.secondary,
            emoji=APPROVE_EMOJI,
            custom_id=f"approve_reply_{confession_num}_{reply_num}",
        )
        self.approve_btn.callback = self.approve_callback

        self.reject_btn = Button(
            label="Reject",
            style=discord.ButtonStyle.secondary,
            emoji=DENY_EMOJI,
            custom_id=f"reject_reply_{confession_num}_{reply_num}",
        )
        self.reject_btn.callback = self.reject_callback

        button_row = discord.ui.ActionRow()
        button_row.add_item(self.approve_btn)
        button_row.add_item(self.reject_btn)

        container = Container(
            TextDisplay(f"## {TICKET} Review Pending Reply #{reply_num}\n\n{content_text}"),
            Separator(),
            TextDisplay(f"For confession **#{confession_num}**. Click Approve to post to thread or Reject to discard."),
        )
        container.add_item(button_row)
        self.add_item(container)

    async def _get_or_create_thread(self):
        # Refresh message in case thread was created since review started
        try:
            message = await self.original_message.channel.fetch_message(self.original_message.id)
        except Exception:
            message = self.original_message

        existing_thread = getattr(message, "thread", None)
        if existing_thread:
            return existing_thread
        thread_name = f"Confession #{self.confession_num} Replies"
        return await message.create_thread(name=thread_name)

    async def approve_callback(self, interaction: discord.Interaction):
        try:
            thread = await self._get_or_create_thread()

            reply_embed = discord.Embed(
                title=f"🕵️ Anonymous Reply #{self.reply_num}",
                description=self.content_text,
                color=discord.Color.blurple(),
            )

            thread_view = discord.ui.View(timeout=None)
            confess_btn = discord.ui.Button(
                label="Confess",
                style=discord.ButtonStyle.grey,
                custom_id=f"thread_confess_approved_{self.confession_num}_{self.reply_num}",
            )

            async def thread_confess_cb(inter: discord.Interaction):
                modal = ConfessionModal(self.bot)
                await inter.response.send_modal(modal)

            confess_btn.callback = thread_confess_cb
            thread_view.add_item(confess_btn)

            await thread.send(embed=reply_embed, view=thread_view)
            await self.bot.db.update_reply_status(
                self.guild_id, self.confession_num, self.reply_num, "approved"
            )

            rev_container = Container(
                TextDisplay(f"## {APPROVE} Approved Reply #{self.reply_num}\n\nApproved by {interaction.user.mention}"),
                Separator(),
                TextDisplay(f"{self.content_text}"),
            )
            rev_view = LayoutView()
            rev_view.add_item(rev_container)
            await interaction.response.edit_message(view=rev_view)
        except Exception as e:
            await _report_error(self.bot, e, interaction, "reply_approve")
            if not interaction.response.is_done():
                err_view = LayoutView()
                err_view.add_item(Container(TextDisplay(f"{DENY} Error approving reply: {e}")))
                await interaction.response.send_message(view=err_view, ephemeral=True)

    async def reject_callback(self, interaction: discord.Interaction):
        try:
            await self.bot.db.update_reply_status(
                self.guild_id, self.confession_num, self.reply_num, "rejected"
            )
            rev_container = Container(
                TextDisplay(f"## {DENY} Rejected Reply #{self.reply_num}\n\nRejected by {interaction.user.mention}"),
                Separator(),
                TextDisplay(f"{self.content_text}"),
            )
            rev_view = LayoutView()
            rev_view.add_item(rev_container)
            await interaction.response.edit_message(view=rev_view)
        except Exception as e:
            await _report_error(self.bot, e, interaction, "reply_reject")


class ConfessionButtonsView(discord.ui.View):
    def __init__(self, bot, confession_num: int, message=None):
        super().__init__(timeout=None)
        self.bot = bot
        self.confession_num = confession_num
        self.message = message

        confess_btn = discord.ui.Button(
            label="Confess",
            style=discord.ButtonStyle.grey,
            custom_id=f"confess_btn_{confession_num}",
        )
        confess_btn.callback = self.confess_callback

        reply_btn = discord.ui.Button(
            label="Reply",
            style=discord.ButtonStyle.grey,
            custom_id=f"reply_btn_{confession_num}",
        )
        reply_btn.callback = self.reply_callback

        report_btn = discord.ui.Button(
            label="Report",
            style=discord.ButtonStyle.grey,
            custom_id=f"report_btn_{confession_num}",
        )
        report_btn.callback = self.report_callback

        self.add_item(confess_btn)
        self.add_item(reply_btn)
        self.add_item(report_btn)

    async def confess_callback(self, interaction: discord.Interaction):
        modal = ConfessionModal(self.bot)
        await interaction.response.send_modal(modal)

    async def reply_callback(self, interaction: discord.Interaction):
        try:
            message = interaction.message
            modal = ReplyModal(self.bot, message, self.confession_num)
            await interaction.response.send_modal(modal)
        except Exception as e:
            await _report_error(self.bot, e, interaction, "reply_button")
            err_view = LayoutView()
            err_view.add_item(Container(TextDisplay(f"{DENY} Could not open reply form: {e}")))
            await interaction.response.send_message(view=err_view, ephemeral=True)

    async def report_callback(self, interaction: discord.Interaction):
        try:
            modal = ReportModal(self.bot, self.confession_num)
            await interaction.response.send_modal(modal)
        except Exception as e:
            await _report_error(self.bot, e, interaction, "report_button")
            err_view = LayoutView()
            err_view.add_item(Container(TextDisplay(f"{DENY} Could not open report form: {e}")))
            if not interaction.response.is_done():
                await interaction.response.send_message(view=err_view, ephemeral=True)


class ReviewActionView(LayoutView):
    def __init__(self, bot, confession_num: int, content_text: str, image_url: str | None = None):
        super().__init__(timeout=None)
        self.bot = bot
        self.confession_num = confession_num
        self.content_text = content_text
        self.image_url = image_url

        display_text = content_text
        if image_url:
            display_text += "\n\n-# An image will be shown below the confession when approved."

        self.approve_btn = Button(
            label="Approve",
            style=discord.ButtonStyle.secondary,
            emoji=APPROVE_EMOJI,
            custom_id=f"approve_conf_{confession_num}",
        )
        self.approve_btn.callback = self.approve_callback

        self.reject_btn = Button(
            label="Reject",
            style=discord.ButtonStyle.secondary,
            emoji=DENY_EMOJI,
            custom_id=f"reject_conf_{confession_num}",
        )
        self.reject_btn.callback = self.reject_callback

        button_row = discord.ui.ActionRow()
        button_row.add_item(self.approve_btn)
        button_row.add_item(self.reject_btn)

        container = Container(
            TextDisplay(
                f"## {TICKET} Review Pending Confession #{confession_num}\n\n"
                "-# Click Approve to post to confession channels or Reject to discard."
            ),
            Separator(),
            TextDisplay(display_text),
            button_row,
        )
        self.add_item(container)

    async def approve_callback(self, interaction: discord.Interaction):
        try:
            guild_id = interaction.guild_id

            settings = await self.bot.cache.get_guild_config(guild_id)
            if not settings:
                settings = await self.bot.db.get_guild_settings(guild_id)
                await self.bot.cache.set_guild_config(guild_id, settings)

            confession_channels = settings.get("confession_channels", [])
            if not confession_channels:
                err_view = LayoutView()
                err_view.add_item(Container(TextDisplay(f"{DENY} No confession channel configured.")))
                await interaction.response.send_message(view=err_view, ephemeral=True)
                return

            embed = build_confession_embed(
                self.confession_num, self.content_text, self.image_url
            )

            buttons_view = ConfessionButtonsView(self.bot, self.confession_num)

            for ch_id in confession_channels:
                channel = interaction.guild.get_channel(ch_id)
                if not channel:
                    try:
                        channel = await interaction.guild.fetch_channel(ch_id)
                    except Exception:
                        channel = None

                if channel:
                    try:
                        last_msg = await self.bot.db.get_latest_confession_message(guild_id, ch_id)
                        if last_msg:
                            try:
                                old_message = await channel.fetch_message(last_msg["message_id"])
                                await old_message.edit(view=None)
                            except Exception as e:
                                logger.error(f"Could not remove buttons from old message: {e}")

                        new_msg = await channel.send(embed=embed, view=buttons_view)
                        await self.bot.db.track_confession_message(
                            guild_id, ch_id, new_msg.id, self.confession_num
                        )
                    except Exception as e:
                        await _report_error(self.bot, e, interaction, f"post_channel_{ch_id}")

            await self.bot.db.update_confession_status(guild_id, self.confession_num, "approved")

            rev_container = Container(
                TextDisplay(f"## {APPROVE} Approved Confession #{self.confession_num}\n\nApproved by {interaction.user.mention}"),
                Separator(),
                TextDisplay(f"{self.content_text}"),
            )
            rev_view = LayoutView()
            rev_view.add_item(rev_container)
            await interaction.response.edit_message(view=rev_view)
        except Exception as e:
            await _report_error(self.bot, e, interaction, "approve")
            if not interaction.response.is_done():
                err_view = LayoutView()
                err_view.add_item(Container(TextDisplay(f"{DENY} Error approving confession: {e}")))
                await interaction.response.send_message(view=err_view, ephemeral=True)

    async def reject_callback(self, interaction: discord.Interaction):
        try:
            await self.bot.db.update_confession_status(
                interaction.guild_id, self.confession_num, "rejected"
            )
            rev_container = Container(
                TextDisplay(f"## {DENY} Rejected Confession #{self.confession_num}\n\nRejected by {interaction.user.mention}"),
                Separator(),
                TextDisplay(f"{self.content_text}"),
            )
            rev_view = LayoutView()
            rev_view.add_item(rev_container)
            await interaction.response.edit_message(view=rev_view)
        except Exception as e:
            await _report_error(self.bot, e, interaction, "reject")


class ConfessionModal(Modal, title="Submit Anonymous Confession"):
    confession_label = Label(
        text="Your Secret Confession",
        component=TextInput(
            custom_id="confession_text",
            style=discord.TextStyle.paragraph,
            placeholder="Type your confession here...",
            required=True,
            min_length=5,
            max_length=2000,
        ),
    )
    image_label = Label(
        text="Confession image (optional)",
        description="Upload an image to show below your confession",
        component=FileUpload(
            custom_id="confession_image",
            required=False,
            min_values=0,
            max_values=1,
        ),
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        if not guild_id:
            err_view = LayoutView()
            err_view.add_item(Container(TextDisplay("Confessions must be sent within a server.")))
            await interaction.response.send_message(view=err_view, ephemeral=True)
            return

        settings = await self.bot.cache.get_guild_config(guild_id)
        if not settings:
            settings = await self.bot.db.get_guild_settings(guild_id)
            await self.bot.cache.set_guild_config(guild_id, settings)

        confession_channels = settings.get("confession_channels", [])
        review_channel_id = settings.get("review_channel_id")
        filter_words = settings.get("filter_words", [])

        if not confession_channels:
            err_view = LayoutView()
            err_view.add_item(Container(
                TextDisplay(f"## {WARN} Bot Not Configured"),
                Separator(),
                TextDisplay(
                    "This server has not configured confession channels yet. "
                    "An Administrator must run `/setup` first."
                ),
            ))
            await interaction.response.send_message(view=err_view, ephemeral=True)
            return

        confession_text = self.confession_label.component.value
        image_url = None
        image_files = self.image_label.component.values
        if image_files:
            image_url = image_files[0].url

        for word in filter_words:
            if word.lower() in confession_text.lower():
                err_view = LayoutView()
                err_view.add_item(Container(
                    TextDisplay(f"## {WARN} Blocked Content"),
                    Separator(),
                    TextDisplay(
                        "Your confession contains prohibited words configured by the server administration."
                    ),
                ))
                await interaction.response.send_message(view=err_view, ephemeral=True)
                return

        await interaction.response.defer(ephemeral=True)

        confession_num = await self.bot.db.increment_confession_count(guild_id)
        author_id = interaction.user.id

        await self.bot.db.create_confession(
            guild_id,
            confession_num,
            confession_text,
            author_id,
            status="pending" if review_channel_id else "posted",
            image_url=image_url,
        )

        if review_channel_id:
            review_channel = interaction.guild.get_channel(review_channel_id)
            if not review_channel:
                try:
                    review_channel = await interaction.guild.fetch_channel(review_channel_id)
                except Exception:
                    review_channel = None

            if review_channel:
                review_view = ReviewActionView(
                    self.bot, confession_num, confession_text, image_url=image_url
                )
                await review_channel.send(view=review_view)

                resp_view = LayoutView()
                resp_view.add_item(Container(
                    TextDisplay(f"## {WARN} Sent for Review"),
                    Separator(),
                    TextDisplay(
                        f"Your anonymous confession **#{confession_num}** has been submitted "
                        "for moderator review. It will appear once approved!"
                    ),
                ))
                await interaction.followup.send(view=resp_view, ephemeral=True)
                return

        embed = build_confession_embed(confession_num, confession_text, image_url)

        buttons_view = ConfessionButtonsView(self.bot, confession_num)

        for ch_id in confession_channels:
            channel = interaction.guild.get_channel(ch_id)
            if not channel:
                try:
                    channel = await interaction.guild.fetch_channel(ch_id)
                except Exception:
                    channel = None

            if channel:
                try:
                    last_msg = await self.bot.db.get_latest_confession_message(guild_id, ch_id)
                    if last_msg:
                        try:
                            old_message = await channel.fetch_message(last_msg["message_id"])
                            await old_message.edit(view=None)
                        except Exception as e:
                            logger.error(f"Could not remove buttons from old message: {e}")

                    new_msg = await channel.send(embed=embed, view=buttons_view)
                    await self.bot.db.track_confession_message(
                        guild_id, ch_id, new_msg.id, confession_num
                    )
                except Exception as e:
                    await _report_error(self.bot, e, interaction, f"send_channel_{ch_id}")

        resp_view = LayoutView()
        resp_view.add_item(Container(
            TextDisplay(f"## {APPROVE} Confession Posted"),
            Separator(),
            TextDisplay(
                f"Your anonymous confession **#{confession_num}** has been successfully published!"
            ),
        ))
        await interaction.followup.send(view=resp_view, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await handle_interaction_error(self.bot, interaction, error, "confess")


class ConfessionsCog(commands.Cog, name="Confessions"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="confess", description="Submit an anonymous confession to the server")
    async def confess(self, interaction: discord.Interaction):
        if not self.bot.is_ready():
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "Bot is still starting — wait a moment and try again.",
                        ephemeral=True,
                    )
            except discord.HTTPException:
                pass
            return

        try:
            await interaction.response.send_modal(ConfessionModal(self.bot))
        except discord.NotFound as e:
            if is_unknown_interaction(e):
                logger.warning(
                    "Confess interaction expired (10062) — bot may have been restarting "
                    "or the connection was slow. Ask the user to run /confess again."
                )
                schedule_error_report(self.bot, e, interaction, "confess")
                return
            raise
        except Exception as e:
            if is_unknown_interaction(e):
                logger.warning("Confess failed with expired interaction (10062)")
                schedule_error_report(self.bot, e, interaction, "confess")
                return
            await _report_error(self.bot, e, interaction, "confess", notify_user=True)


async def setup(bot):
    await bot.add_cog(ConfessionsCog(bot))
