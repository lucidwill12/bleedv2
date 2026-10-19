"""bleed-style {variables} for messages and embed scripts.

    text = format_vars(text, member, channel=..., extra={"reason": "spam"})

`member` may be a Member or User (or None). `extra` keys are plain names
without braces, e.g. {"level.new_rank": 5}. Unknown {things} are left as-is.
"""
import datetime
import re

import discord

try:
    from zoneinfo import ZoneInfo
    PST = ZoneInfo("America/Los_Angeles")
except Exception:  # pragma: no cover
    PST = datetime.timezone(datetime.timedelta(hours=-8))

VAR_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_.]*(?:\([a-zA-Z0-9_.]+\))?)\}")


def _na(v):
    return "N/A" if v in (None, "", []) else str(v)


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def _ts(dt):
    return str(int(dt.timestamp())) if dt else "N/A"


def user_vars(user, prefix="user") -> dict:
    if user is None:
        return {}
    p = prefix
    d = {
        p: str(user),
        f"{p}.id": user.id,
        f"{p}.mention": user.mention,
        f"{p}.name": user.name,
        f"{p}.tag": getattr(user, "discriminator", "0"),
        f"{p}.avatar": user.avatar.url if user.avatar else user.default_avatar.url,
        f"{p}.display_avatar": user.display_avatar.url,
        f"{p}.display_name": user.display_name,
        f"{p}.created_at": user.created_at.strftime("%b %d, %Y %I:%M %p UTC"),
        f"{p}.created_at_timestamp": _ts(user.created_at),
        f"{p}.bot": "Yes" if user.bot else "No",
    }
    flags = [f.name.replace("_", " ").title() for f in user.public_flags.all()] if getattr(user, "public_flags", None) else []
    d[f"{p}.badges"] = _na(", ".join(flags))
    d[f"{p}.badges_icons"] = _na("")
    if isinstance(user, discord.Member):
        roles = [r for r in reversed(user.roles) if not r.is_default()]
        d.update({
            f"{p}.guild_avatar": user.guild_avatar.url if user.guild_avatar else d[f"{p}.avatar"],
            f"{p}.joined_at": user.joined_at.strftime("%b %d, %Y %I:%M %p UTC") if user.joined_at else "N/A",
            f"{p}.joined_at_timestamp": _ts(user.joined_at),
            f"{p}.boost": "Yes" if user.premium_since else "No",
            f"{p}.boost_since": user.premium_since.strftime("%b %d, %Y") if user.premium_since else "N/A",
            f"{p}.boost_since_timestamp": _ts(user.premium_since),
            f"{p}.color": str(user.color),
            f"{p}.top_role": user.top_role.name if not user.top_role.is_default() else "N/A",
            f"{p}.role_list": _na(", ".join(r.mention for r in roles)),
            f"{p}.role_text_list": _na(", ".join(r.name for r in roles)),
        })
        if user.joined_at and user.guild:
            pos = sum(1 for m in user.guild.members if m.joined_at and m.joined_at < user.joined_at) + 1
            d[f"{p}.join_position"] = pos
            d[f"{p}.join_position_suffix"] = _ordinal(pos)
    return d


def guild_vars(g: discord.Guild) -> dict:
    if g is None:
        return {}
    return {
        "guild.name": g.name,
        "guild.id": g.id,
        "guild.count": g.member_count,
        "guild.region": "N/A",
        "guild.shard": g.shard_id or 0,
        "guild.owner_id": g.owner_id,
        "guild.created_at": g.created_at.strftime("%b %d, %Y %I:%M %p UTC"),
        "guild.created_at_timestamp": _ts(g.created_at),
        "guild.emoji_count": len(g.emojis),
        "guild.role_count": len(g.roles),
        "guild.boost_count": g.premium_subscription_count,
        "guild.boost_tier": f"Level {g.premium_tier}" if g.premium_tier else "No Level",
        "guild.preferred_locale": str(g.preferred_locale),
        "guild.key_features": _na(", ".join(f.replace("_", " ").title() for f in g.features)),
        "guild.icon": g.icon.url if g.icon else "N/A",
        "guild.banner": g.banner.url if g.banner else "N/A",
        "guild.splash": g.splash.url if g.splash else "N/A",
        "guild.discovery": g.discovery_splash.url if g.discovery_splash else "N/A",
        "guild.max_presences": _na(g.max_presences),
        "guild.max_members": _na(g.max_members),
        "guild.max_video_channel_users": _na(g.max_video_channel_users),
        "guild.afk_timeout": g.afk_timeout,
        "guild.afk_channel": g.afk_channel.name if g.afk_channel else "N/A",
        "guild.channels": _na(", ".join(c.name for c in g.channels)),
        "guild.channels_count": len(g.channels),
        "guild.text_channels": _na(", ".join(c.name for c in g.text_channels)),
        "guild.text_channels_count": len(g.text_channels),
        "guild.voice_channels": _na(", ".join(c.name for c in g.voice_channels)),
        "guild.voice_channels_count": len(g.voice_channels),
        "guild.category_channels": _na(", ".join(c.name for c in g.categories)),
        "guild.category_channels_count": len(g.categories),
        "guild.vanity": _na(g.vanity_url_code),
    }


def channel_vars(c) -> dict:
    if c is None or not hasattr(c, "name"):
        return {}
    return {
        "channel.name": c.name,
        "channel.id": c.id,
        "channel.mention": c.mention,
        "channel.topic": _na(getattr(c, "topic", None)),
        "channel.type": str(c.type),
        "channel.category_id": _na(c.category_id) if hasattr(c, "category_id") else "N/A",
        "channel.category_name": c.category.name if getattr(c, "category", None) else "N/A",
        "channel.position": getattr(c, "position", 0),
        "channel.slowmode_delay": getattr(c, "slowmode_delay", 0) or 0,
    }


def date_vars() -> dict:
    now = datetime.datetime.now(PST)
    utc = datetime.datetime.now(datetime.timezone.utc)
    return {
        "date.now": now.strftime("%B %d, %Y"),
        "date.utc_timestamp": int(utc.timestamp()),
        "date.now_proper": now.strftime("%A, %B %d, %Y"),
        "date.now_short": now.strftime("%b %d, %Y"),
        "date.now_shorter": now.strftime("%m/%d/%Y"),
        "time.now": now.strftime("%I:%M %p"),
        "time.now_military": now.strftime("%H:%M"),
        "date.utc_now": utc.strftime("%B %d, %Y"),
        "date.utc_now_proper": utc.strftime("%A, %B %d, %Y"),
        "date.utc_now_short": utc.strftime("%b %d, %Y"),
        "date.utc_now_shorter": utc.strftime("%m/%d/%Y"),
        "time.utc_now": utc.strftime("%I:%M %p"),
        "time.utc_now_military": utc.strftime("%H:%M"),
    }


def build_vars(member=None, channel=None, guild=None, moderator=None, extra: dict | None = None) -> dict:
    guild = guild or getattr(member, "guild", None) or getattr(channel, "guild", None)
    d = {}
    d.update(date_vars())
    d.update(guild_vars(guild))
    d.update(channel_vars(channel))
    d.update(user_vars(member, "user"))
    if moderator is not None:
        d.update(user_vars(moderator, "moderator"))
        d["moderator"] = str(moderator)
    if extra:
        d.update(extra)
    return {k: str(v) for k, v in d.items()}


def format_vars(text: str, member=None, channel=None, guild=None, moderator=None, extra: dict | None = None) -> str:
    if not text or "{" not in text:
        return text
    values = build_vars(member, channel, guild, moderator, extra)

    def repl(m):
        key = m.group(1)
        fn = re.fullmatch(r"(lower|upper|proper)\(([^)]+)\)", key)
        if fn:
            v = values.get(fn.group(2))
            if v is None:
                return m.group(0)
            if fn.group(1) == "lower":
                return v.lower()
            if fn.group(1) == "upper":
                return v.upper()
            try:
                return f"{int(float(v)):,}"
            except ValueError:
                return v
        return values.get(key, m.group(0))

    return VAR_RE.sub(repl, text)
