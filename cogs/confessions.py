import logging
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay, Separator, Button, Modal, TextInput

logger = logging.getLogger(__name__)

class ReplyModal(Modal, title="Reply to Confession"):
    confession_input = TextInput(
        label="Your Reply Confession",
        style=discord.TextStyle.paragraph,
        placeholder="Type your anonymous reply here...",
        required=True,
        min_length=5,
        max_length=2000
    )

    def __init__(self, bot, original_message, confession_num: int):
        super().__init__()
        self.bot = bot
        self.original_message = original_message
        self.confession_num = confession_num

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        confession_text = self.confession_input.value

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
                    TextDisplay("# 🚫 Blocked Content"),
                    Separator(),
                    TextDisplay("Your confession contains prohibited words configured by the server administration.")
                ))
                await interaction.response.send_message(view=err_view, ephemeral=True)
                return

        try:
            # Check if thread already exists
            existing_thread = None
            
            # Try to get existing thread from the message
            if hasattr(self.original_message, 'thread'):
                existing_thread = self.original_message.thread
            
            # If no thread yet, create one
            if not existing_thread:
                thread_name = f"Confession #{self.confession_num} Replies"
                existing_thread = await self.original_message.create_thread(name=thread_name)

            # Get a unique reply number for this specific reply
            reply_count = len([msg async for msg in existing_thread.history(limit=100)]) + 1
            
            # If review is enabled, send to review channel
            if review_channel_id:
                review_channel = interaction.guild.get_channel(review_channel_id)
                if not review_channel:
                    try:
                        review_channel = await interaction.guild.fetch_channel(review_channel_id)
                    except Exception:
                        review_channel = None

                if review_channel:
                    # Create a custom review view for replies
                    review_view = ReplyReviewActionView(self.bot, reply_count, confession_text, existing_thread)
                    await review_channel.send(view=review_view)

                    resp_view = LayoutView()
                    resp_view.add_item(Container(
                        TextDisplay("# 📥 Reply Sent for Review"),
                        Separator(),
                        TextDisplay(f"Your anonymous reply has been submitted for moderator review. It will appear in the thread once approved!")
                    ))
                    await interaction.response.send_message(view=resp_view, ephemeral=True)
                    return
            
            # Create embed for reply in thread
            reply_embed = discord.Embed(
                description=confession_text,
                color=discord.Color.blurple()
            )
            reply_embed.set_author(name=f"🕵️ Anonymous Reply #{reply_count}")
            
            # Create view with only confess button
            thread_view = discord.ui.View(timeout=None)
            confess_btn = discord.ui.Button(
                label="Confess",
                style=discord.ButtonStyle.grey,
                custom_id=f"thread_confess_btn_{self.confession_num}_{reply_count}"
            )
            
            async def thread_confess_cb(inter: discord.Interaction):
                modal = ConfessionModal(self.bot)
                await inter.response.send_modal(modal)
            
            confess_btn.callback = thread_confess_cb
            thread_view.add_item(confess_btn)
            
            await existing_thread.send(embed=reply_embed, view=thread_view)

            resp_view = LayoutView()
            resp_view.add_item(Container(
                TextDisplay("# ✅ Reply Posted"),
                Separator(),
                TextDisplay(f"Your anonymous reply has been posted in the thread!")
            ))
            await interaction.response.send_message(view=resp_view, ephemeral=True)

        except Exception as e:
            logger.error(f"Error in reply submission: {e}", exc_info=e)
            err_view = LayoutView()
            err_view.add_item(Container(
                TextDisplay(f"# ❌ Submission Error"),
                Separator(),
                TextDisplay(f"An error occurred: {e}")
            ))
            if interaction.response.is_done():
                await interaction.followup.send(view=err_view, ephemeral=True)
            else:
                await interaction.response.send_message(view=err_view, ephemeral=True)

class ReplyReviewActionView(LayoutView):
    def __init__(self, bot, reply_num: int, content_text: str, thread):
        super().__init__(timeout=None)
        self.bot = bot
        self.reply_num = reply_num
        self.content_text = content_text
        self.thread = thread

        self.approve_btn = Button(
            label="Approve",
            style=discord.ButtonStyle.secondary,
            custom_id=f"approve_reply_{reply_num}"
        )
        self.approve_btn.callback = self.approve_callback

        self.reject_btn = Button(
            label="Reject",
            style=discord.ButtonStyle.secondary,
            custom_id=f"reject_reply_{reply_num}"
        )
        self.reject_btn.callback = self.reject_callback

        # Buttons must be wrapped in ActionRow for Components V2
        button_row = discord.ui.ActionRow()
        button_row.add_item(self.approve_btn)
        button_row.add_item(self.reject_btn)

        container = Container(
            TextDisplay(f"# 📜 Review Pending Reply #{reply_num}\n\n{content_text}"),
            Separator(),
            TextDisplay("Click Approve to post to thread or Reject to discard.")
        )
        container.add_item(button_row)
        self.add_item(container)

    async def approve_callback(self, interaction: discord.Interaction):
        try:
            # Create embed for reply
            reply_embed = discord.Embed(
                description=self.content_text,
                color=discord.Color.blurple()
            )
            reply_embed.set_author(name=f"🕵️ Anonymous Reply #{self.reply_num}")
            
            # Create view with only confess button
            thread_view = discord.ui.View(timeout=None)
            confess_btn = discord.ui.Button(
                label="Confess",
                style=discord.ButtonStyle.grey,
                custom_id=f"thread_confess_approved_{self.reply_num}"
            )
            
            async def thread_confess_cb(inter: discord.Interaction):
                modal = ConfessionModal(self.bot)
                await inter.response.send_modal(modal)
            
            confess_btn.callback = thread_confess_cb
            thread_view.add_item(confess_btn)
            
            await self.thread.send(embed=reply_embed, view=thread_view)

            rev_container = Container(
                TextDisplay(f"# ✅ Approved Reply #{self.reply_num}\n\n{self.content_text}"),
                Separator(),
                TextDisplay(f"Approved by {interaction.user.mention}")
            )
            rev_view = LayoutView()
            rev_view.add_item(rev_container)
            await interaction.response.edit_message(view=rev_view)
        except Exception as e:
            logger.error(f"Error in reply approve_callback: {e}", exc_info=e)
            if not interaction.response.is_done():
                err_view = LayoutView()
                err_view.add_item(Container(TextDisplay(f"❌ Error approving reply: {e}")))
                await interaction.response.send_message(view=err_view, ephemeral=True)

    async def reject_callback(self, interaction: discord.Interaction):
        try:
            rev_container = Container(
                TextDisplay(f"# ❌ Rejected Reply #{self.reply_num}\n\n{self.content_text}"),
                Separator(),
                TextDisplay(f"Rejected by {interaction.user.mention}")
            )
            rev_view = LayoutView()
            rev_view.add_item(rev_container)
            await interaction.response.edit_message(view=rev_view)
        except Exception as e:
            logger.error(f"Error in reply reject_callback: {e}", exc_info=e)

class ConfessionButtonsView(discord.ui.View):
    def __init__(self, bot, confession_num: int, message=None):
        super().__init__(timeout=None)
        self.bot = bot
        self.confession_num = confession_num
        self.message = message

        confess_btn = discord.ui.Button(
            label="Confess",
            style=discord.ButtonStyle.grey,
            custom_id=f"confess_btn_{confession_num}"
        )
        confess_btn.callback = self.confess_callback

        reply_btn = discord.ui.Button(
            label="Reply",
            style=discord.ButtonStyle.grey,
            custom_id=f"reply_btn_{confession_num}"
        )
        reply_btn.callback = self.reply_callback

        self.add_item(confess_btn)
        self.add_item(reply_btn)

    async def confess_callback(self, interaction: discord.Interaction):
        modal = ConfessionModal(self.bot)
        await interaction.response.send_modal(modal)

    async def reply_callback(self, interaction: discord.Interaction):
        try:
            # Get the message this view is attached to
            message = interaction.message
            modal = ReplyModal(self.bot, message, self.confession_num)
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            logger.error(f"Error in reply callback: {e}", exc_info=e)
            err_view = LayoutView()
            err_view.add_item(Container(TextDisplay(f"❌ Could not open reply form: {e}")))
            await interaction.response.send_message(view=err_view, ephemeral=True)

class ReviewActionView(LayoutView):
    def __init__(self, bot, confession_num: int, content_text: str):
        super().__init__(timeout=None)
        self.bot = bot
        self.confession_num = confession_num
        self.content_text = content_text

        self.approve_btn = Button(
            label="Approve",
            style=discord.ButtonStyle.secondary,
            custom_id=f"approve_conf_{confession_num}"
        )
        self.approve_btn.callback = self.approve_callback

        self.reject_btn = Button(
            label="Reject",
            style=discord.ButtonStyle.secondary,
            custom_id=f"reject_conf_{confession_num}"
        )
        self.reject_btn.callback = self.reject_callback

        # Buttons must be wrapped in ActionRow for Components V2
        button_row = discord.ui.ActionRow()
        button_row.add_item(self.approve_btn)
        button_row.add_item(self.reject_btn)

        container = Container(
            TextDisplay(f"# 📜 Review Pending Confession #{confession_num}\n\n{content_text}"),
            Separator(),
            TextDisplay("Click Approve to post to confession channels or Reject to discard."),
            button_row
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
                err_view.add_item(Container(TextDisplay("❌ No confession channel configured.")))
                await interaction.response.send_message(view=err_view, ephemeral=True)
                return

            pub_container = Container(
                TextDisplay(f"# 🕵️ Anonymous Confession #{self.confession_num}\n\n{self.content_text}")
            )
            pub_view = LayoutView()
            pub_view.add_item(pub_container)

            # Create embed for approved confession
            embed = discord.Embed(
                description=self.content_text,
                color=discord.Color.blurple()
            )
            embed.set_author(name=f"🕵️ Anonymous Confession #{self.confession_num}")
            
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
                        # Remove buttons from last confession
                        last_msg = await self.bot.db.get_latest_confession_message(guild_id, ch_id)
                        if last_msg:
                            try:
                                old_message = await channel.fetch_message(last_msg["message_id"])
                                # Just remove buttons
                                await old_message.edit(view=None)
                            except Exception as e:
                                logger.error(f"Could not remove buttons from old message: {e}")
                        
                        # Post new confession embed with buttons in same message
                        new_msg = await channel.send(embed=embed, view=buttons_view)
                        await self.bot.db.track_confession_message(guild_id, ch_id, new_msg.id, self.confession_num)
                    except Exception as e:
                        logger.error(f"Failed to post confession to channel {ch_id}: {e}")

            rev_container = Container(
                TextDisplay(f"# ✅ Approved Confession #{self.confession_num}\n\n{self.content_text}"),
                Separator(),
                TextDisplay(f"Approved by {interaction.user.mention}")
            )
            rev_view = LayoutView()
            rev_view.add_item(rev_container)
            await interaction.response.edit_message(view=rev_view)
        except Exception as e:
            logger.error(f"Error in approve_callback: {e}", exc_info=e)
            if not interaction.response.is_done():
                err_view = LayoutView()
                err_view.add_item(Container(TextDisplay(f"❌ Error approving confession: {e}")))
                await interaction.response.send_message(view=err_view, ephemeral=True)

    async def reject_callback(self, interaction: discord.Interaction):
        try:
            rev_container = Container(
                TextDisplay(f"# ❌ Rejected Confession #{self.confession_num}\n\n{self.content_text}"),
                Separator(),
                TextDisplay(f"Rejected by {interaction.user.mention}")
            )
            rev_view = LayoutView()
            rev_view.add_item(rev_container)
            await interaction.response.edit_message(view=rev_view)
        except Exception as e:
            logger.error(f"Error in reject_callback: {e}", exc_info=e)

class ConfessionModal(Modal, title="Submit Anonymous Confession"):
    confession_input = TextInput(
        label="Your Secret Confession",
        style=discord.TextStyle.paragraph,
        placeholder="Type your confession here...",
        required=True,
        min_length=5,
        max_length=2000
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
                TextDisplay("# ⚠️ Bot Not Configured"),
                Separator(),
                TextDisplay("This server has not configured confession channels yet. An Administrator must run `/setup` first.")
            ))
            await interaction.response.send_message(view=err_view, ephemeral=True)
            return

        confession_text = self.confession_input.value

        for word in filter_words:
            if word.lower() in confession_text.lower():
                err_view = LayoutView()
                err_view.add_item(Container(
                    TextDisplay("# 🚫 Blocked Content"),
                    Separator(),
                    TextDisplay("Your confession contains prohibited words configured by the server administration.")
                ))
                await interaction.response.send_message(view=err_view, ephemeral=True)
                return

        confession_num = await self.bot.db.increment_confession_count(guild_id)
        
        # Store confession text in bot memory for button access
        if not hasattr(self.bot, 'confession_texts'):
            self.bot.confession_texts = {}
        self.bot.confession_texts[confession_num] = confession_text

        if review_channel_id:
            review_channel = interaction.guild.get_channel(review_channel_id)
            if not review_channel:
                try:
                    review_channel = await interaction.guild.fetch_channel(review_channel_id)
                except Exception:
                    review_channel = None

            if review_channel:
                review_view = ReviewActionView(self.bot, confession_num, confession_text)
                await review_channel.send(view=review_view)

                resp_view = LayoutView()
                resp_view.add_item(Container(
                    TextDisplay("# 📥 Sent for Review"),
                    Separator(),
                    TextDisplay(f"Your anonymous confession **#{confession_num}** has been submitted for moderator review. It will appear once approved!")
                ))
                await interaction.response.send_message(view=resp_view, ephemeral=True)
                return

        # Create embed for confession
        embed = discord.Embed(
            description=confession_text,
            color=discord.Color.blurple()
        )
        embed.set_author(name=f"🕵️ Anonymous Confession #{confession_num}")
        
        buttons_view = ConfessionButtonsView(self.bot, confession_num)

        # Remove buttons from previous confession in each channel
        for ch_id in confession_channels:
            channel = interaction.guild.get_channel(ch_id)
            if not channel:
                try:
                    channel = await interaction.guild.fetch_channel(ch_id)
                except Exception:
                    channel = None

            if channel:
                try:
                    # Remove buttons from last confession
                    last_msg = await self.bot.db.get_latest_confession_message(guild_id, ch_id)
                    if last_msg:
                        try:
                            old_message = await channel.fetch_message(last_msg["message_id"])
                            # Just edit to remove buttons, keep the embed
                            await old_message.edit(view=None)
                        except Exception as e:
                            logger.error(f"Could not remove buttons from old message: {e}")
                    
                    # Post new confession embed with buttons in same message
                    new_msg = await channel.send(embed=embed, view=buttons_view)
                    await self.bot.db.track_confession_message(guild_id, ch_id, new_msg.id, confession_num)
                except Exception as e:
                    logger.error(f"Failed to send confession to channel {ch_id}: {e}")

        resp_view = LayoutView()
        resp_view.add_item(Container(
            TextDisplay("# ✅ Confession Posted"),
            Separator(),
            TextDisplay(f"Your anonymous confession **#{confession_num}** has been successfully published!")
        ))
        await interaction.response.send_message(view=resp_view, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        logger.error(f"Error in ConfessionModal submission: {error}", exc_info=error)
        err_view = LayoutView()
        err_view.add_item(Container(
            TextDisplay("# ❌ Submission Error"),
            Separator(),
            TextDisplay("An unexpected error occurred while processing your confession. Please try again.")
        ))
        if interaction.response.is_done():
            await interaction.followup.send(view=err_view, ephemeral=True)
        else:
            await interaction.response.send_message(view=err_view, ephemeral=True)

class ConfessionsCog(commands.Cog, name="Confessions"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="confess", description="Submit an anonymous confession to the server")
    async def confess(self, interaction: discord.Interaction):
        try:
            modal = ConfessionModal(self.bot)
            await interaction.response.send_modal(modal)
        except Exception as e:
            logger.error(f"Error sending confession modal: {e}", exc_info=e)
            if not interaction.response.is_done():
                err_view = LayoutView()
                err_view.add_item(Container(TextDisplay("❌ Could not open confession form. Please try again.")))
                await interaction.response.send_message(view=err_view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ConfessionsCog(bot))
