import logging
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay, Separator

from config import Config

logger = logging.getLogger(__name__)


def is_bot_owner():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not Config.BOT_OWNER_ID or interaction.user.id != Config.BOT_OWNER_ID:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ This command is restricted to the bot owner.",
                    ephemeral=True,
                )
            return False
        return True

    return app_commands.check(predicate)


class OwnerCog(commands.Cog, name="Owner"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="lookup",
        description="[Owner only] Look up who submitted a confession by guild + confession ID",
    )
    @app_commands.describe(
        guild_id="The Discord server (guild) ID",
        confession_id="The confession number shown on the post",
        reply_id="Optional reply number to look up a reply author instead",
    )
    @is_bot_owner()
    async def lookup(
        self,
        interaction: discord.Interaction,
        guild_id: str,
        confession_id: int,
        reply_id: int = None,
    ):
        try:
            gid = int(guild_id.strip())
        except ValueError:
            err_view = LayoutView()
            err_view.add_item(Container(TextDisplay("❌ Invalid guild ID.")))
            await interaction.response.send_message(view=err_view, ephemeral=True)
            return

        if reply_id is not None:
            record = await self.bot.db.get_reply(gid, confession_id, reply_id)
            if not record:
                err_view = LayoutView()
                err_view.add_item(Container(
                    TextDisplay(
                        f"❌ No reply **#{reply_id}** found for confession "
                        f"**#{confession_id}** in guild `{gid}`."
                    )
                ))
                await interaction.response.send_message(view=err_view, ephemeral=True)
                return

            author_id = record.get("author_id")
            user_line = await self._format_user(author_id)
            content = record.get("content", "")
            snippet = content if len(content) <= 800 else content[:800] + "…"

            view = LayoutView()
            view.add_item(Container(
                TextDisplay(f"# 🔍 Reply Lookup"),
                Separator(),
                TextDisplay(
                    f"**Guild ID:** `{gid}`\n"
                    f"**Confession ID:** `{confession_id}`\n"
                    f"**Reply ID:** `{reply_id}`\n"
                    f"**Status:** `{record.get('status')}`\n"
                    f"**Created:** `{record.get('created_at')}`\n\n"
                    f"**Author:** {user_line}\n\n"
                    f"**Content:**\n>>> {snippet}"
                ),
            ))
            await interaction.response.send_message(view=view, ephemeral=True)
            logger.info(
                f"Owner {interaction.user.id} looked up reply guild={gid} "
                f"confession={confession_id} reply={reply_id} author={author_id}"
            )
            return

        record = await self.bot.db.get_confession(gid, confession_id)
        if not record:
            err_view = LayoutView()
            err_view.add_item(Container(
                TextDisplay(
                    f"❌ No confession **#{confession_id}** found in guild `{gid}`."
                )
            ))
            await interaction.response.send_message(view=err_view, ephemeral=True)
            return

        author_id = record.get("author_id")
        user_line = await self._format_user(author_id)
        content = record.get("content", "")
        snippet = content if len(content) <= 800 else content[:800] + "…"

        view = LayoutView()
        view.add_item(Container(
            TextDisplay("# 🔍 Confession Lookup"),
            Separator(),
            TextDisplay(
                f"**Guild ID:** `{gid}`\n"
                f"**Confession ID:** `{confession_id}`\n"
                f"**Status:** `{record.get('status')}`\n"
                f"**Created:** `{record.get('created_at')}`\n\n"
                f"**Author:** {user_line}\n\n"
                f"**Content:**\n>>> {snippet}"
            ),
        ))
        await interaction.response.send_message(view=view, ephemeral=True)
        logger.info(
            f"Owner {interaction.user.id} looked up confession guild={gid} "
            f"confession={confession_id} author={author_id}"
        )

    async def _format_user(self, author_id):
        if not author_id:
            return "`unknown` (not stored)"
        user = self.bot.get_user(author_id)
        if user is None:
            try:
                user = await self.bot.fetch_user(author_id)
            except Exception:
                return f"<@{author_id}> (`{author_id}`) — could not fetch user"
        return f"{user.mention} — `{user}` (`{user.id}`)"


async def setup(bot):
    await bot.add_cog(OwnerCog(bot))
