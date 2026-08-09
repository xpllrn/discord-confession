import io
import traceback
import secrets
import string
from datetime import datetime, timezone
from typing import Optional

import discord


def generate_error_code(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def ansi_id(value, color: str = "red") -> str:
    """Format an ID with ANSI color codes for Discord code blocks."""
    colors = {
        "red": "\u001b[2;31m",
        "green": "\u001b[2;32m",
        "cyan": "\u001b[2;36m",
        "blue": "\u001b[2;34m",
    }
    c = colors.get(color, colors["red"])
    reset = "\u001b[0m"
    return f"```ansi\n{c} {value}{reset}\n```"


def relative_created(created_at: datetime) -> str:
    """Discord relative timestamp for guild created_at."""
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return f"<t:{int(created_at.timestamp())}:R>"


async def get_log_channel(bot: discord.Client, channel_id: int) -> Optional[discord.TextChannel]:
    if not channel_id:
        return None
    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except Exception:
            return None
    return channel if isinstance(channel, discord.abc.Messageable) else None


async def send_error_report(
    bot: discord.Client,
    error: BaseException,
    *,
    user_id: Optional[int] = None,
    guild_id: Optional[int] = None,
    command_used: str = "unknown",
    channel_id: int,
) -> Optional[str]:
    """Send an error embed + traceback file to the error log channel. Returns error code."""
    from config import Config

    code = generate_error_code()
    channel = await get_log_channel(bot, channel_id or Config.ERROR_LOG_CHANNEL_ID)
    if not channel:
        return code

    tb_text = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    error_summary = str(error) or type(error).__name__

    embed = discord.Embed(
        title="CONFESSION ERROR REPORT!",
        description=(
            f"**Error code: `{code}`**\n"
            f"```diff\n- {error_summary}\n```"
        ),
        color=0x392A38,
    )
    if user_id is not None:
        embed.add_field(name="User ID", value=ansi_id(user_id, "red"), inline=True)
    if guild_id is not None:
        embed.add_field(name="Guild ID", value=ansi_id(guild_id, "red"), inline=True)
    embed.set_footer(text=f"Command Used: {command_used}")

    file = discord.File(
        io.BytesIO(tb_text.encode("utf-8")),
        filename=f"traceback-{code}.txt",
    )

    try:
        await channel.send(embed=embed, file=file)
    except Exception:
        pass
    return code


async def send_guild_join_log(
    bot: discord.Client,
    guild: discord.Guild,
    *,
    channel_id: int,
    invitor_id: Optional[int] = None,
):
    from config import Config

    channel = await get_log_channel(bot, channel_id or Config.GUILD_JOIN_LEAVE_CHANNEL_ID)
    if not channel:
        return

    bot_name = bot.user.name if bot.user else "Bot"
    member_count = f"{guild.member_count:,}" if guild.member_count is not None else "unknown"
    owner_id = guild.owner_id or "unknown"
    invitor = invitor_id if invitor_id is not None else "unknown"

    embed = discord.Embed(
        title=f"{bot_name} added in {guild.name} !",
        description=(
            f"-# Created on {relative_created(guild.created_at)}\n"
            f"```diff\n+ New Guild with {member_count} members\n```"
        ),
        color=0x438C53,
    )
    embed.add_field(name="Owner ID", value=ansi_id(owner_id, "green"), inline=True)
    embed.add_field(name="Invitor ID", value=ansi_id(invitor, "green"), inline=True)
    embed.set_footer(text=f"Guild ID: {guild.id}")
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    try:
        await channel.send(embed=embed)
    except Exception:
        pass


async def send_guild_leave_log(
    bot: discord.Client,
    guild: discord.Guild,
    *,
    channel_id: int,
    remover_id: Optional[int] = None,
    member_count: Optional[int] = None,
):
    from config import Config

    channel = await get_log_channel(bot, channel_id or Config.GUILD_JOIN_LEAVE_CHANNEL_ID)
    if not channel:
        return

    bot_name = bot.user.name if bot.user else "Bot"
    count = member_count if member_count is not None else guild.member_count
    count_str = f"{count:,}" if count is not None else "unknown"
    owner_id = guild.owner_id or "unknown"
    remover = remover_id if remover_id is not None else "unknown"

    embed = discord.Embed(
        title=f"{bot_name} removed from {guild.name} !",
        description=(
            f"-# Created on {relative_created(guild.created_at)}\n"
            f"```diff\n- Guild left with {count_str} members\n```"
        ),
        color=0xCD514F,
    )
    embed.add_field(name="Owner ID", value=ansi_id(owner_id, "red"), inline=True)
    embed.add_field(name="Remover ID", value=ansi_id(remover, "red"), inline=True)
    embed.set_footer(text=f"Guild ID: {guild.id}")
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    try:
        await channel.send(embed=embed)
    except Exception:
        pass


async def send_guild_activity_log(
    bot: discord.Client,
    *,
    channel_id: int,
    title: str,
    description: str,
    guild: Optional[discord.Guild] = None,
    guild_id: Optional[int] = None,
    fields: Optional[list] = None,
    color: int = 0xF6DBD3,
):
    from config import Config

    channel = await get_log_channel(bot, channel_id or Config.GUILD_LOG_CHANNEL_ID)
    if not channel:
        return

    embed = discord.Embed(title=title, description=description, color=color)
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    gid = guild.id if guild else guild_id
    if gid:
        embed.set_footer(text=f"Guild ID: {gid}")
    if guild and guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    try:
        await channel.send(embed=embed)
    except Exception:
        pass


async def send_report_log(
    bot: discord.Client,
    *,
    channel_id: int,
    confession_num: int,
    confession_content: str,
    author_id: int,
    author_name: str,
    reporter: discord.abc.User,
    reason: str,
    guild: discord.Guild,
):
    from config import Config

    channel = await get_log_channel(bot, channel_id or Config.REPORT_LOG_CHANNEL_ID)
    if not channel:
        return

    snippet = confession_content[:200] + ("…" if len(confession_content) > 200 else "")
    embed = discord.Embed(
        color=0xF6DBD3,
        description=f"```diff\n- Confession #{confession_num} has been reported\n```\n> {snippet}",
    )
    embed.set_author(
        name="confession reported",
        icon_url="https://cdn.discordapp.com/emojis/1536027827894358057.png",
    )
    embed.add_field(
        name="Reported",
        value=(
            f"> **Confession**: #{confession_num}\n"
            f"> **User ID**: {author_id}\n"
            f"> **Username**: {author_name}"
        ),
        inline=True,
    )
    embed.add_field(
        name="Reporter",
        value=(
            f"> **Tag**: {reporter}\n"
            f"> **User ID**: {reporter.id}\n"
            f"> **Username**: {reporter.name}"
        ),
        inline=True,
    )
    embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
    embed.set_footer(text=f"Guild: {guild.name} ({guild.id})")

    try:
        await channel.send(embed=embed)
    except Exception:
        pass
