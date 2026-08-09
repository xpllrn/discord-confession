import os
import sys
import logging
import asyncio
import discord
from discord.ext import commands
from config import Config
from database import DatabaseManager
from cache import CacheManager
from logutil import send_error_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ConfessionBot")

class ConfessionBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        self.db = DatabaseManager(Config.DATABASE_PATH)
        self.cache = CacheManager()

    async def setup_hook(self):
        logger.info("Initializing Database and Redis Cache...")
        await self.db.init_db()
        await self.cache.connect()

        logger.info("Loading Cogs...")
        initial_extensions = [
            "cogs.setup",
            "cogs.panel",
            "cogs.confessions",
            "cogs.help",
            "cogs.events",
            "cogs.owner",
        ]

        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")

        @self.tree.error
        async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
            # Unwrap CommandInvokeError
            original = getattr(error, "original", error)
            command_name = interaction.command.name if interaction.command else "unknown"

            # Unknown interaction (10062) — too late to respond; still log it
            is_unknown = getattr(original, "code", None) == 10062 or "10062" in str(original)

            logger.error(
                f"App command error in command '{command_name}': {error}",
                exc_info=error,
            )
            await send_error_report(
                self,
                original if isinstance(original, BaseException) else error,
                user_id=interaction.user.id if interaction.user else None,
                guild_id=interaction.guild_id,
                command_used=command_name,
                channel_id=Config.ERROR_LOG_CHANNEL_ID,
            )

            if is_unknown or interaction.response.is_done():
                return

            try:
                from discord.ui import LayoutView, Container, TextDisplay
                err_view = LayoutView()
                err_view.add_item(Container(TextDisplay(f"❌ An error occurred: {original}")))
                await interaction.response.send_message(view=err_view, ephemeral=True)
            except Exception as send_err:
                logger.error(f"Failed to send error response: {send_err}")
                try:
                    await send_error_report(
                        self,
                        send_err,
                        user_id=interaction.user.id if interaction.user else None,
                        guild_id=interaction.guild_id,
                        command_used=f"{command_name}_error_response",
                        channel_id=Config.ERROR_LOG_CHANNEL_ID,
                    )
                except Exception:
                    pass

        logger.info("Syncing slash commands...")
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands globally.")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info("Bot is ready and active!")
        if not Config.BOT_OWNER_ID:
            logger.warning("BOT_OWNER_ID is not set — /lookup will deny everyone.")

    async def close(self):
        logger.info("Shutting down bot and closing database/cache connections...")
        await self.cache.close()
        await super().close()

async def main():
    if not Config.DISCORD_TOKEN or Config.DISCORD_TOKEN == "your_discord_bot_token_here":
        logger.warning("DISCORD_TOKEN is not set in .env file or environment.")
        logger.warning("Please configure DISCORD_TOKEN in .env file to start the bot.")

    bot = ConfessionBot()
    try:
        await bot.start(Config.DISCORD_TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid DISCORD_TOKEN provided. Please update .env with a valid token.")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot execution stopped by user.")
