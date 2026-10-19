"""SQLite wrapper. Core tables live here; each cog creates its own tables in cog_load
via `await bot.db.executescript(SCHEMA)` using CREATE TABLE IF NOT EXISTS."""
import os

import aiosqlite

CORE_SCHEMA = """
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id INTEGER PRIMARY KEY,
    prefix TEXT,
    jail_role INTEGER,
    jail_channel INTEGER,
    mod_log INTEGER,
    autorole INTEGER
);
CREATE TABLE IF NOT EXISTS fake_permissions (
    guild_id INTEGER, role_id INTEGER, permission TEXT,
    PRIMARY KEY (guild_id, role_id, permission)
);
CREATE TABLE IF NOT EXISTS staff_roles (
    guild_id INTEGER, role_id INTEGER, PRIMARY KEY (guild_id, role_id)
);
CREATE TABLE IF NOT EXISTS mod_cases (
    guild_id INTEGER, case_id INTEGER, action TEXT, target_id INTEGER, moderator_id INTEGER,
    reason TEXT, created_at INTEGER, PRIMARY KEY (guild_id, case_id)
);
CREATE TABLE IF NOT EXISTS invoke_messages (
    guild_id INTEGER, command TEXT, kind TEXT, message TEXT,
    PRIMARY KEY (guild_id, command, kind)
);
CREATE TABLE IF NOT EXISTS warnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER, user_id INTEGER, mod_id INTEGER, reason TEXT, created_at INTEGER
);
CREATE TABLE IF NOT EXISTS jailed (
    guild_id INTEGER, user_id INTEGER, roles TEXT,
    PRIMARY KEY (guild_id, user_id)
);
CREATE TABLE IF NOT EXISTS afk (
    guild_id INTEGER, user_id INTEGER, reason TEXT, since INTEGER,
    PRIMARY KEY (guild_id, user_id)
);
"""

# columns added to older databases automatically
MIGRATIONS = {
    "guild_settings": {
        "mute_role": "INTEGER", "imute_role": "INTEGER", "rmute_role": "INTEGER",
        "jail_log": "INTEGER",
    },
}


class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.execute("PRAGMA journal_mode=WAL")
        await self.conn.executescript(CORE_SCHEMA)
        for table, cols in MIGRATIONS.items():
            await self.add_columns(table, cols)
        await self.conn.commit()

    async def add_columns(self, table: str, cols: dict[str, str]):
        """Add any missing columns to an existing table (safe to call every start)."""
        async with self.conn.execute(f"PRAGMA table_info({table})") as cur:
            have = {r["name"] for r in await cur.fetchall()}
        for name, typ in cols.items():
            if name not in have:
                await self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {typ}")
        await self.conn.commit()

    async def close(self):
        if self.conn:
            await self.conn.close()

    async def executescript(self, sql: str):
        await self.conn.executescript(sql)
        await self.conn.commit()

    async def execute(self, sql: str, *args):
        cur = await self.conn.execute(sql, args)
        await self.conn.commit()
        return cur

    async def executemany(self, sql: str, rows):
        await self.conn.executemany(sql, rows)
        await self.conn.commit()

    async def fetchone(self, sql: str, *args):
        async with self.conn.execute(sql, args) as cur:
            return await cur.fetchone()

    async def fetchall(self, sql: str, *args):
        async with self.conn.execute(sql, args) as cur:
            return await cur.fetchall()

    async def fetchval(self, sql: str, *args):
        row = await self.fetchone(sql, *args)
        return row[0] if row else None

    async def ensure_guild(self, guild_id: int):
        await self.execute("INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)", guild_id)

    async def guild_setting(self, guild_id: int, column: str):
        return await self.fetchval(f"SELECT {column} FROM guild_settings WHERE guild_id = ?", guild_id)

    async def set_guild_setting(self, guild_id: int, column: str, value):
        await self.ensure_guild(guild_id)
        await self.execute(f"UPDATE guild_settings SET {column} = ? WHERE guild_id = ?", value, guild_id)
