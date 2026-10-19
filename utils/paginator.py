"""Shared paginator and confirmation prompt.

    await Paginator.send(ctx, lines, title="...")
    if await confirm(ctx, "Are you sure?"): ...
"""
import discord


class Paginator(discord.ui.View):
    def __init__(self, author_id: int, pages: list[discord.Embed]):
        super().__init__(timeout=120)
        self.author_id, self.pages, self.index = author_id, pages, 0
        self.message = None
        for i, p in enumerate(pages):
            p.set_footer(text=f"Page {i + 1}/{len(pages)} ({p.footer.text})" if p.footer.text else f"Page {i + 1}/{len(pages)}")

    async def interaction_check(self, interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This isn't your menu", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(view=None)
            except discord.HTTPException:
                pass

    @discord.ui.button(emoji="◀", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction, button):
        self.index = (self.index - 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.pages[self.index])

    @discord.ui.button(emoji="▶", style=discord.ButtonStyle.secondary)
    async def next(self, interaction, button):
        self.index = (self.index + 1) % len(self.pages)
        await interaction.response.edit_message(embed=self.pages[self.index])

    @discord.ui.button(emoji="✖", style=discord.ButtonStyle.danger)
    async def close(self, interaction, button):
        await interaction.response.defer()
        await interaction.delete_original_response()
        self.stop()

    @classmethod
    async def send(cls, ctx, lines: list[str], title: str, per_page: int = 10, color=None):
        pages = []
        for i in range(0, len(lines), per_page):
            e = ctx.bot.embeds.neutral("\n".join(lines[i:i + per_page]), title=title)
            pages.append(e)
        if len(pages) == 1:
            return await ctx.send(embed=pages[0])
        view = cls(ctx.author.id, pages)
        view.message = await ctx.send(embed=pages[0], view=view)
        return view.message


class Confirm(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=30)
        self.author_id = author_id
        self.value = None

    async def interaction_check(self, interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This isn't your prompt", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success)
    async def yes(self, interaction, button):
        self.value = True
        await interaction.response.edit_message(view=None)
        self.stop()

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def no(self, interaction, button):
        self.value = False
        await interaction.response.edit_message(view=None)
        self.stop()


async def confirm(ctx, text: str) -> bool:
    view = Confirm(ctx.author.id)
    msg = await ctx.send(embed=ctx.bot.embeds.neutral(text), view=view)
    await view.wait()
    if not view.value:
        try:
            await msg.edit(embed=ctx.bot.embeds.neutral("Cancelled"), view=None)
        except discord.HTTPException:
            pass
        return False
    try:
        await msg.delete()
    except discord.HTTPException:
        pass
    return True
