import asyncio
import logging

import discord

from config import Config
from emojis import WARN
from logutil import generate_error_code, send_error_report

logger = logging.getLogger(__name__)


def build_command_error_embed(command_name: str, user: discord.abc.User) -> discord.Embed:
    mention = user.mention if user else "User"
    support_url = Config.SUPPORT_SERVER_URL
    return discord.Embed(
        description=(
            f"{WARN} {mention}: Error occurred while performing command **{command_name}**. "
            f"Use the given error code to report it to the developers in the "
            f"[support server]({support_url})."
        ),
        color=0x392A38,
    )


async def respond_command_error(
    interaction: discord.Interaction,
    command_name: str,
    error_code: str,
):
    """Show the standard error code + embed to the user (fast, ephemeral)."""
    if not interaction.user:
        return
    try:
        embed = build_command_error_embed(command_name, interaction.user)
        content = f"`{error_code}`"
        if interaction.response.is_done():
            await interaction.followup.send(content=content, embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(content=content, embed=embed, ephemeral=True)
    except Exception as exc:
        logger.error(f"Failed to send command error response: {exc}")


async def report_error_async(
    bot,
    error,
    interaction=None,
    command_used: str = "unknown",
    error_code: str | None = None,
):
    logger.error(f"{command_used}: {error}", exc_info=error)
    try:
        await send_error_report(
            bot,
            error,
            user_id=interaction.user.id if interaction and interaction.user else None,
            guild_id=interaction.guild_id if interaction else None,
            command_used=command_used,
            channel_id=Config.ERROR_LOG_CHANNEL_ID,
            error_code=error_code,
        )
    except Exception:
        logger.exception("Failed to send error report to log channel")


def schedule_error_report(
    bot,
    error,
    interaction=None,
    command_used: str = "unknown",
    error_code: str | None = None,
):
    asyncio.create_task(
        report_error_async(bot, error, interaction, command_used, error_code)
    )


def is_unknown_interaction(error: BaseException) -> bool:
    return getattr(error, "code", None) == 10062 or "10062" in str(error)


async def handle_interaction_error(
    bot,
    interaction: discord.Interaction,
    error: BaseException,
    command_used: str,
):
    """Respond to the user immediately, then log to the staff error channel."""
    code = generate_error_code()
    if not is_unknown_interaction(error) and not interaction.response.is_done():
        await respond_command_error(interaction, command_used, code)
    schedule_error_report(bot, error, interaction, command_used, code)


async def respond_interaction_error(interaction, message: str):
    """Simple ephemeral text (permissions, validation — no error code)."""
    try:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
    except Exception as exc:
        logger.error(f"Failed to send interaction error response: {exc}")
