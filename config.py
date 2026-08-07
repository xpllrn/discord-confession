import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/confessions.db")
    SUPPORT_SERVER_URL: str = os.getenv("SUPPORT_SERVER_URL", "https://discord.gg/support")
