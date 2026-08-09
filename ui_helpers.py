import asyncio
import logging

from config import Config

logger = logging.getLogger(__name__)


async def report_error_async(bot, error, interaction=None, command_used: str = "unknown"):
    """Send error report to staff channel (may be slow — call via schedule_error_report)."""
    from logutil import send_error_report

    logger.error(f"{command_used}: {error}", exc_info=error)
    try:
        await send_error_report(
            bot,
            error,
            user_id=interaction.user.id if interaction and interaction.user else None,
            guild_id=interaction.guild_id if interaction else None,
            command_used=command_used,
            channel_id=Config.ERROR_LOG_CHANNEL_ID,
        )
    except Exception:
        logger.exception("Failed to send error report to log channel")


def schedule_error_report(bot, error, interaction=None, command_used: str = "unknown"):
    asyncio.create_task(report_error_async(bot, error, interaction, command_used))


async def respond_interaction_error(interaction, message: str):
    """Reply to an interaction with a simple ephemeral message (always fast)."""
    try:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
    except Exception as exc:
        logger.error(f"Failed to send interaction error response: {exc}")
