import discord

# Colour scheme matching the popular multipurpose-bot style
APPROVE = 0xA4EB78
WARN = 0xFFD04A
DENY = 0xFF6464
NEUTRAL = 0x2B2D31

E_APPROVE = "✅"
E_WARN = "⚠️"
E_DENY = "❌"


class Embeds:
    def approve(self, text: str, author: discord.abc.User | None = None) -> discord.Embed:
        return discord.Embed(color=APPROVE, description=f"{E_APPROVE} {self._m(author)}{text}")

    def warn(self, text: str, author: discord.abc.User | None = None) -> discord.Embed:
        return discord.Embed(color=WARN, description=f"{E_WARN} {self._m(author)}{text}")

    def deny(self, text: str, author: discord.abc.User | None = None) -> discord.Embed:
        return discord.Embed(color=DENY, description=f"{E_DENY} {self._m(author)}{text}")

    def neutral(self, text: str = "", title: str | None = None) -> discord.Embed:
        return discord.Embed(color=NEUTRAL, description=text, title=title)

    @staticmethod
    def _m(author):
        return f"{author.mention}: " if author else ""
