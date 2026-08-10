import logging
from typing import Optional

import discord
from discord.ext import commands

from config import Config
from logutil import send_guild_join_log, send_guild_leave_log

logger = logging.getLogger(__name__)


class EventsCog(commands.Cog, name="Events"):
    def __init__(self, bot):
        self.bot = bot
        self._guild_meta: dict[int, dict] = {}
        self._pending_removers: dict[int, int] = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            self._guild_meta[guild.id] = {
                "name": guild.name,
                "member_count": guild.member_count,
                "owner_id": guild.owner_id,
                "created_at": guild.created_at,
                "icon_url": guild.icon.url if guild.icon else None,
            }

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        """Capture who removed the bot before on_guild_remove fires."""
        if not self.bot.user or not entry.target:
            return
        if entry.target.id != self.bot.user.id:
            return
        if entry.action in (
            discord.AuditLogAction.kick,
            discord.AuditLogAction.ban,
            discord.AuditLogAction.bot_add,
        ):
            if entry.action != discord.AuditLogAction.bot_add and entry.user:
                self._pending_removers[entry.guild.id] = entry.user.id

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        self._guild_meta[guild.id] = {
            "name": guild.name,
            "member_count": guild.member_count,
            "owner_id": guild.owner_id,
            "created_at": guild.created_at,
            "icon_url": guild.icon.url if guild.icon else None,
        }

        invitor_id = await self._find_invitor(guild)
        logger.info(f"Joined guild {guild.name} ({guild.id}) invitor={invitor_id}")

        await send_guild_join_log(
            self.bot,
            guild,
            channel_id=Config.GUILD_JOIN_LEAVE_CHANNEL_ID,
            invitor_id=invitor_id,
        )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        meta = self._guild_meta.pop(guild.id, {})
        remover_id = self._pending_removers.pop(guild.id, None)
        logger.info(f"Left guild {guild.name} ({guild.id}) remover={remover_id}")

        member_count = meta.get("member_count", guild.member_count)

        await send_guild_leave_log(
            self.bot,
            guild,
            channel_id=Config.GUILD_JOIN_LEAVE_CHANNEL_ID,
            remover_id=remover_id,
            member_count=member_count,
        )

    async def _find_invitor(self, guild: discord.Guild) -> Optional[int]:
        try:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.bot_add):
                if entry.target and entry.target.id == self.bot.user.id:
                    return entry.user.id if entry.user else None
        except Exception as e:
            logger.warning(f"Could not read audit log for invitor in {guild.id}: {e}")
        return None


async def setup(bot):
    await bot.add_cog(EventsCog(bot))
