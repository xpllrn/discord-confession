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
                    author_id INTEGER,
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
            await db.execute("""
                CREATE TABLE IF NOT EXISTS replies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    confession_num INTEGER NOT NULL,
                    reply_num INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    author_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Migrations for older databases
            async with db.execute("PRAGMA table_info(confessions)") as cursor:
                confession_columns = {row[1] for row in await cursor.fetchall()}
            if "author_id" not in confession_columns:
                await db.execute("ALTER TABLE confessions ADD COLUMN author_id INTEGER")
            if "image_url" not in confession_columns:
                await db.execute("ALTER TABLE confessions ADD COLUMN image_url TEXT")

            async with db.execute("PRAGMA table_info(guild_settings)") as cursor:
                guild_columns = {row[1] for row in await cursor.fetchall()}
            if "bot_nick" not in guild_columns:
                await db.execute("ALTER TABLE guild_settings ADD COLUMN bot_nick TEXT")
            if "banner_url" not in guild_columns:
                await db.execute("ALTER TABLE guild_settings ADD COLUMN banner_url TEXT")
            if "bot_bio" not in guild_columns:
                await db.execute("ALTER TABLE guild_settings ADD COLUMN bot_bio TEXT")

            await db.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_confessions_guild_num "
                "ON confessions(guild_id, confession_num)"
            )

            await db.commit()
            logger.info("Database initialized successfully.")

    async def get_guild_settings(self, guild_id: int) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT confession_channels, review_channel_id, filter_words, confession_count,
                       avatar_url, bot_nick, banner_url, bot_bio
                FROM guild_settings WHERE guild_id = ?
                """,
                (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    confession_channels = json.loads(row[0]) if row[0] else []
                    review_channel_id = row[1]
                    filter_words = json.loads(row[2]) if row[2] else []
                    confession_count = row[3] or 0
                    return {
                        "confession_channels": confession_channels,
                        "review_channel_id": review_channel_id,
                        "filter_words": filter_words,
                        "confession_count": confession_count,
                        "avatar_url": row[4],
                        "bot_nick": row[5],
                        "banner_url": row[6],
                        "bot_bio": row[7],
                    }
                return {
                    "confession_channels": [],
                    "review_channel_id": None,
                    "filter_words": [],
                    "confession_count": 0,
                    "avatar_url": None,
                    "bot_nick": None,
                    "banner_url": None,
                    "bot_bio": None,
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

    async def create_confession(
        self,
        guild_id: int,
        confession_num: int,
        content: str,
        author_id: int,
        status: str = "pending",
        image_url: Optional[str] = None,
    ) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO confessions (guild_id, confession_num, content, author_id, status, image_url)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(guild_id, confession_num) DO UPDATE SET
                    content = excluded.content,
                    author_id = excluded.author_id,
                    status = excluded.status,
                    image_url = excluded.image_url
            """, (guild_id, confession_num, content, author_id, status, image_url))
            await db.commit()
            return cursor.lastrowid

    async def update_confession_status(self, guild_id: int, confession_num: int, status: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE confessions SET status = ? WHERE guild_id = ? AND confession_num = ?",
                (status, guild_id, confession_num),
            )
            await db.commit()

    async def get_confession(self, guild_id: int, confession_num: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT confession_num, content, author_id, status, created_at, image_url
                FROM confessions
                WHERE guild_id = ? AND confession_num = ?
            """, (guild_id, confession_num)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                return {
                    "confession_num": row[0],
                    "content": row[1],
                    "author_id": row[2],
                    "status": row[3],
                    "created_at": row[4],
                    "image_url": row[5],
                    "guild_id": guild_id,
                }

    async def list_confessions(self, guild_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        limit = max(1, min(limit, 50))
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT confession_num, content, author_id, status, created_at
                FROM confessions
                WHERE guild_id = ?
                ORDER BY confession_num DESC
                LIMIT ?
            """, (guild_id, limit)) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "confession_num": row[0],
                        "content": row[1],
                        "author_id": row[2],
                        "status": row[3],
                        "created_at": row[4],
                        "guild_id": guild_id,
                    }
                    for row in rows
                ]

    async def next_reply_num(self, guild_id: int, confession_num: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT COALESCE(MAX(reply_num), 0) + 1 FROM replies
                WHERE guild_id = ? AND confession_num = ?
            """, (guild_id, confession_num)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 1

    async def create_reply(
        self,
        guild_id: int,
        confession_num: int,
        reply_num: int,
        content: str,
        author_id: int,
        status: str = "pending",
    ) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO replies (guild_id, confession_num, reply_num, content, author_id, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (guild_id, confession_num, reply_num, content, author_id, status))
            await db.commit()
            return cursor.lastrowid

    async def update_reply_status(
        self, guild_id: int, confession_num: int, reply_num: int, status: str
    ):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE replies SET status = ?
                   WHERE guild_id = ? AND confession_num = ? AND reply_num = ?""",
                (status, guild_id, confession_num, reply_num),
            )
            await db.commit()

    async def get_reply(
        self, guild_id: int, confession_num: int, reply_num: int
    ) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT reply_num, content, author_id, status, created_at
                FROM replies
                WHERE guild_id = ? AND confession_num = ? AND reply_num = ?
            """, (guild_id, confession_num, reply_num)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                return {
                    "reply_num": row[0],
                    "content": row[1],
                    "author_id": row[2],
                    "status": row[3],
                    "created_at": row[4],
                    "guild_id": guild_id,
                    "confession_num": confession_num,
                }

    async def list_replies(
        self,
        guild_id: int,
        confession_num: Optional[int] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        limit = max(1, min(limit, 50))
        async with aiosqlite.connect(self.db_path) as db:
            if confession_num is not None:
                query = """
                    SELECT confession_num, reply_num, content, author_id, status, created_at
                    FROM replies
                    WHERE guild_id = ? AND confession_num = ?
                    ORDER BY reply_num DESC
                    LIMIT ?
                """
                params = (guild_id, confession_num, limit)
            else:
                query = """
                    SELECT confession_num, reply_num, content, author_id, status, created_at
                    FROM replies
                    WHERE guild_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """
                params = (guild_id, limit)

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "confession_num": row[0],
                        "reply_num": row[1],
                        "content": row[2],
                        "author_id": row[3],
                        "status": row[4],
                        "created_at": row[5],
                        "guild_id": guild_id,
                    }
                    for row in rows
                ]

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

    async def set_guild_customization(
        self,
        guild_id: int,
        bot_nick: Optional[str] = None,
        avatar_url: Optional[str] = None,
        banner_url: Optional[str] = None,
        bot_bio: Optional[str] = None,
    ):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO guild_settings (guild_id, bot_nick, avatar_url, banner_url, bot_bio)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    bot_nick = excluded.bot_nick,
                    avatar_url = excluded.avatar_url,
                    banner_url = excluded.banner_url,
                    bot_bio = excluded.bot_bio,
                    updated_at = CURRENT_TIMESTAMP
            """, (guild_id, bot_nick, avatar_url, banner_url, bot_bio))
            await db.commit()

    async def set_guild_avatar(self, guild_id: int, avatar_url: str):
        await self.set_guild_customization(guild_id, avatar_url=avatar_url)
