"""Case logging and customizable punishment responses/DMs (bleed's ,invoke).

    await punishment_dm(ctx, "ban", member, reason, duration=None)   # before the action
    ...do the action...
    await punishment_response(ctx, "ban", member, reason, duration=None)   # replies 👍 or the custom message
    await log_case(bot, guild, "ban", member, ctx.author, reason)       # posts to the mod log channel
"""
import time

import discord

from utils.script import send_script

INVOKE_COMMANDS = ["jail", "unjail", "kick", "ban", "unban", "tempban", "softban", "hardban", "timeout",
                   "untimeout", "warn", "mute", "unmute", "imute", "iunmute", "rmute", "runmute"]

ACTION_COLORS = {
    "ban": 0xFF6464, "hardban": 0xB00020, "tempban": 0xFF6464, "softban": 0xFF8C64, "kick": 0xFFA94D,
    "timeout": 0xFFD04A, "jail": 0xFFD04A, "warn": 0xFFE08A, "mute": 0xFFD04A,
}


def _extra(reason, duration):
    return {"reason": reason or "No reason provided", "duration": duration or "N/A"}


async def _invoke(bot, guild_id, command, kind):
    return await bot.db.fetchval(
        "SELECT message FROM invoke_messages WHERE guild_id = ? AND command = ? AND kind = ?", guild_id, command, kind)


async def punishment_dm(ctx, command: str, target, reason: str | None, duration: str | None = None, invite_url: str | None = None):
    """DM the target the custom message for this command, if one is set. Never raises."""
    text = await _invoke(ctx.bot, ctx.guild.id, command, "dm")
    if not text:
        return
    extra = _extra(reason, duration)
    extra["invite_url"] = invite_url or "N/A"
    try:
        await send_script(target, text, member=target, channel=ctx.channel, guild=ctx.guild, moderator=ctx.author, extra=extra)
    except discord.HTTPException:
        pass


async def punishment_response(ctx, command: str, target, reason: str | None, duration: str | None = None, default: str = "👍"):
    """Reply in channel with the custom response for this command, or the default (👍)."""
    text = await _invoke(ctx.bot, ctx.guild.id, command, "message")
    if text:
        try:
            return await send_script(ctx.channel, text, member=target, channel=ctx.channel, guild=ctx.guild,
                                     moderator=ctx.author, extra=_extra(reason, duration))
        except discord.HTTPException:
            pass
    return await ctx.send(default)


async def log_case(bot, guild: discord.Guild, action: str, target, moderator, reason: str | None = None,
                   duration: str | None = None) -> int:
    """Store a case and post it to the mod log channel (,settings modlog or #jail-log). Returns the case number."""
    # number the case inside the INSERT itself so concurrent calls (honeypot/antiraid bursts) can't collide
    cur = await bot.db.execute(
        "INSERT INTO mod_cases SELECT ?, COALESCE(MAX(case_id), 0) + 1, ?, ?, ?, ?, ? FROM mod_cases WHERE guild_id = ?",
        guild.id, action, getattr(target, "id", 0), getattr(moderator, "id", 0), reason, int(time.time()), guild.id)
    case_id = await bot.db.fetchval("SELECT case_id FROM mod_cases WHERE rowid = ?", cur.lastrowid)
    channel_id = await bot.db.guild_setting(guild.id, "mod_log") or await bot.db.guild_setting(guild.id, "jail_log")
    channel = guild.get_channel(channel_id) if channel_id else None
    if channel:
        e = discord.Embed(color=ACTION_COLORS.get(action.split()[0], 0x2B2D31), timestamp=discord.utils.utcnow())
        e.set_author(name=f"Case #{case_id} • {action.title()}")
        if target is not None:
            e.add_field(name="User", value=f"{target} (`{target.id}`)", inline=True)
        if moderator is not None:
            e.add_field(name="Moderator", value=f"{moderator} (`{moderator.id}`)", inline=True)
        if duration:
            e.add_field(name="Duration", value=duration, inline=True)
        e.add_field(name="Reason", value=(reason or "No reason provided")[:1024], inline=False)
        try:
            await channel.send(embed=e)
        except discord.HTTPException:
            pass
    return case_id
