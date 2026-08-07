import os
import json
import logging
import aiosqlite
from typing import Optional, Dict, Any, List
from config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = Config.DATABASE_PATH):
        self.db_path = db_path

    async def init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    confession_channels TEXT DEFAULT '[]',
                    review_channel_id INTEGER DEFAULT NULL,
                    filter_words TEXT DEFAULT '[]',
                    confession_count INTEGER DEFAULT 0,
                    avatar_url TEXT DEFAULT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS confessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    confession_num INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    channel_id INTEGER,
                    message_id INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS confession_messages (
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    confession_num INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, channel_id, message_id)
                )
            """)
            await db.commit()
            logger.info("Database initialized successfully.")

    async def get_guild_settings(self, guild_id: int) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT confession_channels, review_channel_id, filter_words, confession_count, avatar_url FROM guild_settings WHERE guild_id = ?",
                (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    confession_channels = json.loads(row[0]) if row[0] else []
                    review_channel_id = row[1]
                    filter_words = json.loads(row[2]) if row[2] else []
                    confession_count = row[3] or 0
                    avatar_url = row[4]
                    return {
                        "confession_channels": confession_channels,
                        "review_channel_id": review_channel_id,
                        "filter_words": filter_words,
                        "confession_count": confession_count,
                        "avatar_url": avatar_url
                    }
                return {
                    "confession_channels": [],
                    "review_channel_id": None,
                    "filter_words": [],
                    "confession_count": 0,
                    "avatar_url": None
                }

    async def increment_confession_count(self, guild_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO guild_settings (guild_id, confession_count)
                VALUES (?, 1)
                ON CONFLICT(guild_id) DO UPDATE SET
                    confession_count = confession_count + 1,
                    updated_at = CURRENT_TIMESTAMP
            """, (guild_id,))
            await db.commit()

            async with db.execute(
                "SELECT confession_count FROM guild_settings WHERE guild_id = ?", (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 1

    async def set_confession_channels(self, guild_id: int, channel_ids: List[int]):
        channels_json = json.dumps(channel_ids)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO guild_settings (guild_id, confession_channels)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    confession_channels = excluded.confession_channels,
                    updated_at = CURRENT_TIMESTAMP
            """, (guild_id, channels_json))
            await db.commit()

    async def set_review_channel(self, guild_id: int, channel_id: Optional[int]):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO guild_settings (guild_id, review_channel_id)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    review_channel_id = excluded.review_channel_id,
                    updated_at = CURRENT_TIMESTAMP
            """, (guild_id, channel_id))
            await db.commit()

    async def set_filter_words(self, guild_id: int, words: List[str]):
        words_json = json.dumps(words)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO guild_settings (guild_id, filter_words)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    filter_words = excluded.filter_words,
                    updated_at = CURRENT_TIMESTAMP
            """, (guild_id, words_json))
            await db.commit()

    async def create_confession(self, guild_id: int, confession_num: int, content: str, status: str = 'pending') -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO confessions (guild_id, confession_num, content, status)
                VALUES (?, ?, ?, ?)
            """, (guild_id, confession_num, content, status))
            await db.commit()
            return cursor.lastrowid

    async def track_confession_message(self, guild_id: int, channel_id: int, message_id: int, confession_num: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO confession_messages (guild_id, channel_id, message_id, confession_num)
                VALUES (?, ?, ?, ?)
            """, (guild_id, channel_id, message_id, confession_num))
            await db.commit()

    async def get_latest_confession_message(self, guild_id: int, channel_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT message_id, confession_num FROM confession_messages
                WHERE guild_id = ? AND channel_id = ?
                ORDER BY created_at DESC LIMIT 1
            """, (guild_id, channel_id)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {"message_id": row[0], "confession_num": row[1]}
                return None

    async def set_guild_avatar(self, guild_id: int, avatar_url: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO guild_settings (guild_id, avatar_url)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    avatar_url = excluded.avatar_url,
                    updated_at = CURRENT_TIMESTAMP
            """, (guild_id, avatar_url))
            await db.commit()
