import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/confessions.db")

    SUPPORT_SERVER_URL: str = os.getenv(
        "SUPPORT_SERVER_URL", "https://discord.gg/CbM8AAUcua"
    )

    # Bot Discord user ID (from Developer Portal → OAuth2 / Bot tab)
    BOT_USER_ID: int = int(os.getenv("BOT_USER_ID", "1508460938255138981") or "0")

    # Staff / logging guild (where log channels live)
    STAFF_GUILD_ID: int = int(os.getenv("STAFF_GUILD_ID", "1534941712177168384") or "0")

    # Only this human user can use /lookup (set your Discord user ID, not the bot ID)
    BOT_OWNER_ID: int = int(os.getenv("BOT_OWNER_ID", "0") or "0")

    # Private log channels (in STAFF_GUILD_ID)
    ERROR_LOG_CHANNEL_ID: int = int(os.getenv("ERROR_LOG_CHANNEL_ID", "1536045899049078965"))
    GUILD_JOIN_LEAVE_CHANNEL_ID: int = int(
        os.getenv("GUILD_JOIN_LEAVE_CHANNEL_ID", "1536045678508118056")
    )
    GUILD_LOG_CHANNEL_ID: int = int(os.getenv("GUILD_LOG_CHANNEL_ID", "1536045911862411326"))
    REPORT_LOG_CHANNEL_ID: int = int(os.getenv("REPORT_LOG_CHANNEL_ID", "1536045946956415168"))
