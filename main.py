import os
import asyncio
import logging
import pathlib

import discord
from discord.ext import commands
from dotenv import load_dotenv

from utils.db import Database
from utils.embeds import Embeds
from utils.flags import FlagError

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

TOKEN = os.getenv("DISCORD_TOKEN")
DEFAULT_PREFIX = os.getenv("DEFAULT_PREFIX", ",")
BOT_NAME = os.getenv("BOT_NAME", "Pulse")
OWNER_IDS = {int(x) for x in os.getenv("OWNER_IDS", "").replace(" ", "").split(",") if x}
BASE = pathlib.Path(__file__).parent


async def get_prefix(bot: "Bot", message: discord.Message):
    if not message.guild:
        return commands.when_mentioned_or(DEFAULT_PREFIX)(bot, message)
    return commands.when_mentioned_or(await bot.guild_prefix(message.guild.id))(bot, message)


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=get_prefix,
            intents=discord.Intents.all(),
            help_command=None,
            case_insensitive=True,
            strip_after_prefix=True,
            owner_ids=OWNER_IDS or None,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, replied_user=False),
        )
        self.db = Database(os.getenv("DATABASE_PATH", str(BASE / "data" / "bot.db")))
        self.prefix_cache: dict[int, str] = {}
        self.fakeperm_cache: dict[int, dict[int, set[str]]] = {}
        self.raid_state: set[int] = set()  # guild ids currently in an antiraid "raid state"
        self.default_prefix = DEFAULT_PREFIX
        self.name = BOT_NAME
        self.embeds = Embeds()

    async def guild_prefix(self, guild_id: int) -> str:
        prefix = self.prefix_cache.get(guild_id)
        if prefix is None:
            prefix = await self.db.guild_setting(guild_id, "prefix") or DEFAULT_PREFIX
            self.prefix_cache[guild_id] = prefix
        return prefix

    async def setup_hook(self):
        await self.db.connect()
        for path in sorted((BASE / "cogs").glob("*.py")):
            if path.stem.startswith("_"):
                continue
            name = f"cogs.{path.stem}"
            try:
                await self.load_extension(name)
                logging.info("Loaded %s", name)
            except Exception:
                logging.exception("Failed to load %s", name)

    async def on_ready(self):
        logging.info("Logged in as %s (%s) in %d guilds", self.user, self.user.id, len(self.guilds))
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{DEFAULT_PREFIX}help"))

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.guild and message.content.strip() in (f"<@{self.user.id}>", f"<@!{self.user.id}>"):
            prefix = await self.guild_prefix(message.guild.id)
            await message.channel.send(embed=self.embeds.neutral(f"Guild prefix: `{prefix}`"))
            return
        # command aliases (,alias add shh timeout {0} 10m)
        aliases = self.get_cog("Aliases")
        if aliases and message.guild:
            new = await aliases.rewrite(message, await self.guild_prefix(message.guild.id))
            if new:
                message.content = new
        await self.process_commands(message)

    async def on_interaction(self, interaction: discord.Interaction):
        # buttons created by embed scripts have no handler — acknowledge them so they don't "fail"
        cid = (interaction.data or {}).get("custom_id", "") if interaction.type == discord.InteractionType.component else ""
        if cid.startswith("script:") and not interaction.response.is_done():
            try:
                await interaction.response.defer()
            except discord.HTTPException:
                pass

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if hasattr(ctx.command, "on_error") or (ctx.cog and ctx.cog.has_error_handler()):
            return
        error = getattr(error, "original", error)
        e = self.embeds
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingPermissions):
            perms = ", ".join(p.replace("_", " ") for p in error.missing_permissions)
            return await ctx.send(embed=e.warn(f"You're **missing** permission: `{perms}`", ctx.author))
        if isinstance(error, (commands.BotMissingPermissions,)):
            perms = ", ".join(p.replace("_", " ") for p in error.missing_permissions)
            return await ctx.send(embed=e.warn(f"I'm **missing** permission: `{perms}`", ctx.author))
        if isinstance(error, commands.MissingRequiredArgument):
            usage = f"{ctx.clean_prefix}{ctx.command.qualified_name} {ctx.command.signature}"
            return await ctx.send(embed=e.warn(f"Missing argument **{error.param.name}**\n```{usage}```", ctx.author))
        if isinstance(error, (commands.MemberNotFound, commands.UserNotFound)):
            return await ctx.send(embed=e.warn("I couldn't find that **member**", ctx.author))
        if isinstance(error, commands.RoleNotFound):
            return await ctx.send(embed=e.warn("I couldn't find that **role**", ctx.author))
        if isinstance(error, (commands.ChannelNotFound, commands.ChannelNotReadable)):
            return await ctx.send(embed=e.warn("I couldn't find that **channel**", ctx.author))
        if isinstance(error, commands.MessageNotFound):
            return await ctx.send(embed=e.warn("I couldn't find that **message**", ctx.author))
        if isinstance(error, commands.EmojiNotFound):
            return await ctx.send(embed=e.warn("I couldn't find that **emoji**", ctx.author))
        if isinstance(error, FlagError):
            return await ctx.send(embed=e.warn(str(error), ctx.author))
        if isinstance(error, (commands.BadArgument, commands.BadUnionArgument, commands.BadLiteralArgument)):
            return await ctx.send(embed=e.warn(str(error), ctx.author))
        if isinstance(error, commands.UserInputError):  # unclosed quotes, too many arguments, ...
            return await ctx.send(embed=e.warn(str(error), ctx.author))
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(embed=e.warn(f"Please wait **{error.retry_after:.1f}s** before using this again", ctx.author))
        if isinstance(error, commands.NoPrivateMessage):
            return await ctx.send(embed=e.warn("This command only works in servers"))
        if isinstance(error, commands.CheckFailure):
            return await ctx.send(embed=e.warn(str(error) or "You can't use this command", ctx.author))
        if isinstance(error, discord.Forbidden):
            return await ctx.send(embed=e.warn("I don't have permission to do that — check my **role position**", ctx.author))
        if isinstance(error, discord.HTTPException) and error.status == 400:
            return await ctx.send(embed=e.warn(f"Discord rejected that: `{error.text[:200]}`", ctx.author))
        logging.exception("Unhandled error in %s", ctx.command, exc_info=error)
        await ctx.send(embed=e.deny("Something went wrong running that command", ctx.author))

    async def close(self):
        await self.db.close()
        await super().close()


async def main():
    if not TOKEN:
        raise SystemExit("Set DISCORD_TOKEN in your .env file")
    bot = Bot()
    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
