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
        "SUPPORT_SERVER_URL", "https://discord.gg/PNDPCfJPFe"
    )

    # Bot Discord user ID (from Developer Portal → OAuth2 / Bot tab)
    BOT_USER_ID: int = int(os.getenv("BOT_USER_ID", "1508460938255138981") or "0")

    # Staff / logging guild (where log channels live)
    STAFF_GUILD_ID: int = int(os.getenv("STAFF_GUILD_ID", "1535882987986489384") or "0")

    # Only these human users can use /lookup (not the bot ID)
    BOT_OWNER_IDS: set[int] = {
        int(x.strip())
        for x in (os.getenv("BOT_OWNER_ID", "") or "1509046532756869141,1488123223945121853").replace(",", " ").split()
        if x.strip().isdigit()
    }
    BOT_OWNER_ID: int = next(iter(BOT_OWNER_IDS), 0)

    # Private log channels (in STAFF_GUILD_ID)
    ERROR_LOG_CHANNEL_ID: int = int(os.getenv("ERROR_LOG_CHANNEL_ID", "1536045899049078965"))
    GUILD_JOIN_LEAVE_CHANNEL_ID: int = int(
        os.getenv("GUILD_JOIN_LEAVE_CHANNEL_ID", "1536045911862411326")
    )
    REPORT_LOG_CHANNEL_ID: int = int(os.getenv("REPORT_LOG_CHANNEL_ID", "1536045946956415168"))

    # Shown as the bot's custom status in Discord
    BOT_STATUS: str = os.getenv("BOT_STATUS", "🔗 confess.adore.rest")

    # Set to 0 to skip global slash sync on every boot (commands already registered)
    SYNC_COMMANDS_ON_START: bool = os.getenv("SYNC_COMMANDS_ON_START", "1") not in ("0", "false", "False")
