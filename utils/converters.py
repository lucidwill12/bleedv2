import re

import discord
from discord.ext import commands

from utils.time import parse_duration

EXTRA_COLORS = {
    "pink": 0xFFC0CB, "hotpink": 0xFF69B4, "black": 0x000001, "white": 0xFFFFFF, "cyan": 0x00FFFF,
    "aqua": 0x00FFFF, "lime": 0x00FF00, "navy": 0x000080, "maroon": 0x800000, "olive": 0x808000,
    "silver": 0xC0C0C0, "brown": 0xA52A2A, "violet": 0xEE82EE, "indigo": 0x4B0082, "gold": 0xFFD700,
    "crimson": 0xDC143C, "coral": 0xFF7F50, "salmon": 0xFA8072, "turquoise": 0x40E0D0, "beige": 0xF5F5DC,
}


def parse_color(value: str) -> discord.Color | None:
    if value is None:
        return None
    v = value.strip().lower().replace(" ", "_")
    m = re.fullmatch(r"#?([0-9a-f]{6}|[0-9a-f]{3})", v)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return discord.Color(int(h, 16))
    if v in EXTRA_COLORS:
        return discord.Color(EXTRA_COLORS[v])
    factory = getattr(discord.Color, v, None)
    if callable(factory) and v not in ("from_rgb", "from_hsv", "from_str", "random"):
        try:
            c = factory()
            if isinstance(c, discord.Color):
                return c
        except TypeError:
            pass
    if v == "random":
        return discord.Color.random()
    return None


class ColorConverter(commands.Converter):
    async def convert(self, ctx, argument):
        c = parse_color(argument)
        if c is None:
            raise commands.BadArgument(f"`{argument}` isn't a valid colour — use a hex code like `#ff0000` or a name like `red`")
        return c


class Duration(commands.Converter):
    """Converts '2d3h' to seconds (int)."""

    async def convert(self, ctx, argument):
        s = parse_duration(argument)
        if s is None:
            raise commands.BadArgument(f"`{argument}` isn't a valid duration — use e.g. `10m`, `2h`, `1d`, `2d3h`")
        return s


def on_off(value: str) -> bool:
    v = value.lower()
    if v in ("on", "true", "yes", "enable", "enabled"):
        return True
    if v in ("off", "false", "no", "disable", "disabled"):
        return False
    raise commands.BadArgument("Use `on` or `off`")
