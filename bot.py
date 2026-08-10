import os
import sys
import logging
import asyncio
import discord
from discord.ext import commands
from discord.gateway import DiscordWebSocket
from config import Config
from database import DatabaseManager
from cache import CacheManager
from ui_helpers import handle_interaction_error, is_unknown_interaction


async def _identify_vr(self):
    payload = {
        "op": self.IDENTIFY,
        "d": {
            "token": self.token,
            "properties": {
                "os": "Discord VR",
                "browser": "Discord VR",
                "device": "Discord VR",
            },
            "compress": True,
            "large_threshold": 250,
        },
    }

    if self.shard_id is not None and self.shard_count is not None:
        payload["d"]["shard"] = [self.shard_id, self.shard_count]

    state = self._connection
    if state._activity is not None or state._status is not None:
        payload["d"]["presence"] = {
            "status": state._status,
            "game": state._activity,
            "since": 0,
            "afk": False,
        }

    if state._intents is not None:
        payload["d"]["intents"] = state._intents.value

    await self.send_as_json(payload)


DiscordWebSocket.identify = _identify_vr

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
        self._warmup_done = asyncio.Event()
        self._status_api_runner = None

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
            original = getattr(error, "original", error)
            command_name = interaction.command.name if interaction.command else "unknown"
            if is_unknown_interaction(original if isinstance(original, BaseException) else error):
                logger.warning(
                    f"Expired interaction for command '{command_name}' (10062), not responding"
                )
                return
            await handle_interaction_error(
                self,
                interaction,
                original if isinstance(original, BaseException) else error,
                command_name,
            )

        if Config.SYNC_COMMANDS_ON_START:
            logger.info("Syncing slash commands...")
            try:
                synced = await self.tree.sync()
                logger.info(f"Synced {len(synced)} slash commands globally.")
            except Exception as e:
                logger.error(f"Failed to sync slash commands: {e}")
        else:
            logger.info("Skipping slash command sync (SYNC_COMMANDS_ON_START=0).")

        try:
            from status_api import start_status_api
            self._status_api_runner = await start_status_api(self)
            if self._status_api_runner:
                logger.info("Status API started.")
        except Exception as e:
            logger.warning(f"Status API failed to start: {e}")
            self._status_api_runner = None

    async def on_connect(self):
        """Warm the HTTP session before users can invoke commands."""
        asyncio.create_task(self._warmup_http())

    async def _warmup_http(self):
        try:
            await self.application_info()
            logger.info("HTTP session warmed up.")
        except Exception as e:
            logger.warning(f"HTTP warmup failed: {e}")
        finally:
            self._warmup_done.set()

    async def _set_presence(self):
        try:
            await self.change_presence(
                status=discord.Status.online,
                activity=discord.CustomActivity(name=Config.BOT_STATUS),
            )
        except Exception as e:
            logger.warning(f"Failed to set presence: {e}")

    async def on_ready(self):
        asyncio.create_task(self._set_presence())
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Status set to {Config.BOT_STATUS}")
        logger.info("Bot is ready and active!")
        if not Config.BOT_OWNER_ID:
            logger.warning("BOT_OWNER_ID is not set, /lookup will deny everyone.")

    async def close(self):
        logger.info("Shutting down bot and closing database/cache connections...")
        try:
            from status_api import stop_status_api
            await stop_status_api(self._status_api_runner)
        except Exception:
            pass
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
