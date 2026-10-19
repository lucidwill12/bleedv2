"""Permission checks that respect bleed-style fake permissions.

Use `@has_perms(ban_members=True)` instead of `@commands.has_permissions(...)`.
A member passes if they are the guild owner, have the real permission (or
administrator), or one of their roles was given the permission (or
"administrator") with `,fakepermissions add`.
"""
import discord
from discord.ext import commands

VALID_PERMS = set(discord.Permissions.VALID_FLAGS)
# alias -> canonical name (manage_emojis -> manage_expressions, view_channel -> read_messages, ...)
PERM_ALIASES = {n: v.alias for n, v in vars(discord.Permissions).items() if hasattr(v, "alias")}


def _canon(perm: str) -> str:
    return PERM_ALIASES.get(perm, perm)


async def fake_perms_for(bot, member: discord.Member) -> set[str]:
    cache = bot.fakeperm_cache.get(member.guild.id)
    if cache is None:
        rows = await bot.db.fetchall("SELECT role_id, permission FROM fake_permissions WHERE guild_id = ?", member.guild.id)
        cache = {}
        for r in rows:
            cache.setdefault(r["role_id"], set()).add(r["permission"])
        bot.fakeperm_cache[member.guild.id] = cache
    perms = set()
    for role in member.roles:
        perms |= cache.get(role.id, set())
    return perms


async def member_has_perms(bot, member: discord.Member, **perms) -> list[str]:
    """Returns the list of missing permissions (empty = allowed)."""
    if member.guild.owner_id == member.id:
        return []
    real = member.guild_permissions
    if real.administrator:
        return []
    missing = [p for p, v in perms.items() if v and not getattr(real, p, False)]
    if not missing:
        return []
    fake = {_canon(p) for p in await fake_perms_for(bot, member)}
    if "administrator" in fake:
        return []
    return [p for p in missing if _canon(p) not in fake]


def has_perms(**perms):
    invalid = set(perms) - VALID_PERMS
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    async def predicate(ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage()
        missing = await member_has_perms(ctx.bot, ctx.author, **perms)
        if missing:
            raise commands.MissingPermissions(missing)
        return True

    predicate.required_perms = [p for p, v in perms.items() if v]  # read by ,help
    return commands.check(predicate)


def guild_owner():
    async def predicate(ctx):
        if ctx.guild and ctx.author.id == ctx.guild.owner_id:
            return True
        raise commands.CheckFailure("Only the **server owner** can use this command")
    predicate.required_perms = ["server owner"]
    return commands.check(predicate)


async def staff_role_ids(bot, guild_id: int) -> set[int]:
    rows = await bot.db.fetchall("SELECT role_id FROM staff_roles WHERE guild_id = ?", guild_id)
    return {r["role_id"] for r in rows}


async def is_staff(bot, member: discord.Member) -> bool:
    if member.guild_permissions.administrator or member.id == member.guild.owner_id:
        return True
    ids = await staff_role_ids(bot, member.guild.id)
    return any(r.id in ids for r in member.roles)


def hierarchy_error(ctx, target: discord.Member) -> str | None:
    """Returns a reason string if the author/bot can't act on target, else None."""
    if target == ctx.author:
        return "You can't do that to yourself"
    if target.id == ctx.guild.owner_id:
        return "You can't do that to the server owner"
    if target == ctx.guild.me:
        return "You can't do that to me"
    if ctx.author.id != ctx.guild.owner_id and target.top_role >= ctx.author.top_role:
        return "You can't do that to someone with a higher or equal role"
    if target.top_role >= ctx.guild.me.top_role:
        return "I can't do that to someone above my highest role"
    return None
