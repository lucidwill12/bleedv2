"""bleed-style embed scripting.

    {embed}$v{title: hi {user}}$v{description: welcome}$v{color: #ff0000}$v{message: {user.mention}}

Keys: message (alias content), title, description, color, url, image, thumbnail,
timestamp, author (name && icon && url), field (name && value && inline) — repeatable,
footer (text && icon), button (type && label && url-or-emoji && enabled|disabled) — repeatable.

Use:
    script = Script.build(text, member=..., channel=..., extra={...})
    msg = await script.send(channel)            # or script.kwargs() for .send/.edit/webhook.send
Plain text (no script keys) becomes a normal message with variables replaced.
"""
import datetime
import re
import uuid

import discord

from utils.converters import parse_color
from utils.variables import format_vars

KEYS = {"message", "content", "title", "description", "color", "colour", "url", "image", "thumbnail",
        "timestamp", "author", "field", "footer", "button"}
KEY_START = re.compile(r"^\s*(\{embed\}|\{(" + "|".join(KEYS) + r")\s*:)", re.I)
BUTTON_STYLES = {
    "link": discord.ButtonStyle.link, "blurple": discord.ButtonStyle.primary, "primary": discord.ButtonStyle.primary,
    "green": discord.ButtonStyle.success, "success": discord.ButtonStyle.success,
    "grey": discord.ButtonStyle.secondary, "gray": discord.ButtonStyle.secondary, "secondary": discord.ButtonStyle.secondary,
    "red": discord.ButtonStyle.danger, "danger": discord.ButtonStyle.danger,
}


def is_script(text: str) -> bool:
    return bool(text and KEY_START.match(text))


def _split_parts(text: str) -> list[str]:
    return [p for p in re.split(r"\$v", text) if p.strip()]


class Script:
    def __init__(self, content=None, embed=None, view=None, raw=""):
        self.content: str | None = content
        self.embed: discord.Embed | None = embed
        self.view: discord.ui.View | None = view
        self.raw = raw

    # ---------- construction ----------
    @classmethod
    def build(cls, text: str, member=None, channel=None, guild=None, moderator=None, extra=None) -> "Script":
        text = format_vars(text or "", member=member, channel=channel, guild=guild, moderator=moderator, extra=extra)
        return cls.parse(text)

    @classmethod
    def parse(cls, text: str) -> "Script":
        text = (text or "").strip()
        if not is_script(text):
            return cls(content=text[:2000] or None, raw=text)
        if text.lower().startswith("{embed}"):
            text = text[len("{embed}"):]
        content = None
        embed = discord.Embed()
        has_embed = False
        view = None
        for part in _split_parts(text):
            part = part.strip()
            if part.startswith("{") and part.endswith("}"):
                part = part[1:-1]
            key, _, value = part.partition(":")
            key = key.strip().lower()
            value = value.strip()
            args = [a.strip() for a in value.split("&&")]
            if key in ("message", "content"):
                content = value[:2000]
            elif key == "title":
                embed.title = value[:256]; has_embed = True
            elif key == "description":
                embed.description = value[:4096]; has_embed = True
            elif key in ("color", "colour"):
                c = parse_color(value)
                if c:
                    embed.color = c
            elif key == "url":
                if value.startswith("http"):
                    embed.url = value
            elif key == "image":
                if value.startswith("http"):
                    embed.set_image(url=value); has_embed = True
            elif key == "thumbnail":
                if value.startswith("http"):
                    embed.set_thumbnail(url=value); has_embed = True
            elif key == "timestamp":
                embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            elif key == "author":
                icon = args[1] if len(args) > 1 and args[1].startswith("http") else None
                url = args[2] if len(args) > 2 and args[2].startswith("http") else None
                embed.set_author(name=args[0][:256] or "​", icon_url=icon, url=url); has_embed = True
            elif key == "field":
                if len(embed.fields) < 25:
                    inline = len(args) > 2 and args[2].lower() == "inline"
                    embed.add_field(name=args[0][:256] or "​", value=(args[1] if len(args) > 1 else "​")[:1024] or "​", inline=inline)
                    has_embed = True
            elif key == "footer":
                icon = args[1] if len(args) > 1 and args[1].startswith("http") else None
                embed.set_footer(text=args[0][:2048], icon_url=icon); has_embed = True
            elif key == "button":
                view = view or discord.ui.View(timeout=None)
                cls._add_button(view, args)
        return cls(content=content, embed=embed if has_embed else None, view=view, raw=text)

    @staticmethod
    def _add_button(view: discord.ui.View, args: list[str]):
        if len(view.children) >= 25:
            return
        style = BUTTON_STYLES.get(args[0].lower()) if args else None
        if style is None:  # bleed allows {button: url && label}
            if args and args[0].startswith("http"):
                args = ["link", args[1] if len(args) > 1 else "link", args[0]]
                style = discord.ButtonStyle.link
            else:
                style = discord.ButtonStyle.secondary
                args = ["grey"] + args
        label = args[1][:80] if len(args) > 1 and args[1] else None
        third = args[2] if len(args) > 2 else None
        disabled = len(args) > 3 and args[3].lower() == "disabled"
        if style is discord.ButtonStyle.link:
            if not third or not third.startswith("http"):
                return
            view.add_item(discord.ui.Button(style=style, label=label or "link", url=third, disabled=disabled))
        else:
            emoji = third if third and not third.startswith("http") else None
            if len(args) == 3 and third and third.lower() in ("enabled", "disabled"):
                emoji, disabled = None, third.lower() == "disabled"
            try:
                view.add_item(discord.ui.Button(style=style, label=label, emoji=emoji, disabled=disabled,
                                                custom_id=f"script:{uuid.uuid4().hex[:16]}"))
            except (TypeError, ValueError):
                view.add_item(discord.ui.Button(style=style, label=label or "​", disabled=disabled,
                                                custom_id=f"script:{uuid.uuid4().hex[:16]}"))

    # ---------- output ----------
    @property
    def empty(self) -> bool:
        return not self.content and not self.embed

    def kwargs(self, include_view=True) -> dict:
        kw = {"content": self.content, "embed": self.embed}
        if include_view and self.view is not None:
            kw["view"] = self.view
        return kw

    async def send(self, destination, allowed_mentions=None, **extra) -> discord.Message | None:
        if self.empty:
            return None
        kw = self.kwargs()
        kw.update(extra)
        if allowed_mentions is not None:
            kw["allowed_mentions"] = allowed_mentions
        if kw.get("embed") is None:
            kw.pop("embed")
        if kw.get("content") is None:
            kw.pop("content")
        return await destination.send(**kw)


async def send_script(destination, text, member=None, channel=None, guild=None, moderator=None, extra=None,
                      allowed_mentions=None, **kw) -> discord.Message | None:
    """One-liner: build and send. Mentions of users are allowed by default."""
    if allowed_mentions is None:
        allowed_mentions = discord.AllowedMentions(users=True, roles=False, everyone=False)
    s = Script.build(text, member=member, channel=channel or (destination if hasattr(destination, "guild") else None),
                     guild=guild, moderator=moderator, extra=extra)
    return await s.send(destination, allowed_mentions=allowed_mentions, **kw)
