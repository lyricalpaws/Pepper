# Paginator by EvieePy (https://github.com/EvieePy/)

import discord
import asyncio
import utils


async def pager(entries, chunk: int):
    for x in range(0, len(entries), chunk):
        yield entries[x: x + chunk]


class SimplePaginator:

    __slots__ = (
        "entries",
        "extras",
        "title",
        "description",
        "colour",
        "footer",
        "length",
        "prepend",
        "append",
        "fmt",
        "timeout",
        "ordered",
        "controls",
        "controller",
        "pages",
        "current",
        "previous",
        "eof",
        "base",
        "names",
    )

    def __init__(self, **kwargs):
        self.entries = kwargs.get("entries", None)
        self.extras = kwargs.get("extras", None)

        self.title = kwargs.get("title", None)
        self.description = kwargs.get("description", None)
        self.colour = kwargs.get("colour", 0xFFD4D4)
        self.footer = kwargs.get("footer", None)

        self.length = kwargs.get("length", 10)
        self.prepend = kwargs.get("prepend", "")
        self.append = kwargs.get("append", "")
        self.fmt = kwargs.get("fmt", "")
        self.timeout = kwargs.get("timeout", 90)
        self.ordered = kwargs.get("ordered", False)

        self.controller = None
        self.pages = []
        self.names = []
        self.base = None

        self.current = 0
        self.previous = 0
        self.eof = 0

        self.controls = {"⏮": 0.0, "◀": -1, "⏹": "stop", "▶": +1, "⏭": None}

    async def indexer(self, ctx, ctrl):
        if ctrl == "stop":
            ctx.bot.loop.create_task(self.stop_controller(self.base))

        elif isinstance(ctrl, int):
            self.current += ctrl
            if self.current > self.eof or self.current < 0:
                self.current -= ctrl
        else:
            self.current = int(ctrl)

    async def reaction_controller(self, ctx):
        bot = ctx.bot
        author = ctx.author

        self.base = await ctx.send(embed=self.pages[0])

        if len(self.pages) == 1:
            await self.base.add_reaction("⏹")
        else:
            for reaction in self.controls:
                try:
                    await self.base.add_reaction(reaction)
                except discord.HTTPException:
                    return

        def check(r, u):
            if str(r) not in self.controls.keys():
                return False
            if u.id == bot.user.id or r.message.id != self.base.id:
                return False
            if u.id != author.id:
                return False
            return True

        while True:
            try:
                react, user = await bot.wait_for(
                    "reaction_add", check=check, timeout=self.timeout
                )
            except asyncio.TimeoutError:
                return ctx.bot.loop.create_task(self.stop_controller(self.base))

            control = self.controls.get(str(react))

            try:
                await self.base.remove_reaction(react, user)
            except discord.HTTPException:
                pass

            self.previous = self.current
            await self.indexer(ctx, control)

            if self.previous == self.current:
                continue

            try:
                await self.base.edit(embed=self.pages[self.current])
            except KeyError:
                pass

    async def stop_controller(self, message):
        try:
            await message.clear_reactions()
        except discord.HTTPException:
            pass

        self.controller.cancel()

    def formmater(self, chunk):
        return "\n".join(
            f"{self.prepend}{self.fmt}{value}{self.fmt[::-1]}{self.append}"
            for value in chunk
        )

    async def paginate(self, ctx):
        if self.extras:
            self.pages = [p for p in self.extras if isinstance(p, discord.Embed)]

        if self.entries:
            chunks = [c async for c in pager(self.entries, self.length)]

            for index, chunk in enumerate(chunks):
                page = discord.Embed(
                    title=f"{self.title} - {index + 1}/{len(chunks)}", color=self.colour
                )
                page.description = self.formmater(chunk)

                if self.footer:
                    page.set_footer(text=self.footer)
                self.pages.append(page)

        if not self.pages:
            raise utils.EvieeBaseException(
                "There must be enough data to create at least 1 page for pagination."
            )

        self.eof = float(len(self.pages) - 1)
        self.controls["⏭"] = self.eof
        self.controller = ctx.bot.loop.create_task(self.reaction_controller(ctx))


class EmojiPaginator(SimplePaginator):

    __slots__ = ("chunks",)

    def __init__(self, **kwargs):
        self.chunks = kwargs.get("chunks")
        super().__init__(**kwargs)

    async def paginate(self, ctx):
        for index, chunk in enumerate(self.chunks):
            if index % 2 == 0:
                page = discord.Embed(color=self.colour)
                page.add_field(
                    name="\u200b",
                    value="\n".join(f"{e} | [{e.name}]({e.url})" for e in chunk),
                )
                self.pages.append(page)
            else:
                page.add_field(
                    name="\u200b",
                    value="\n".join(f"{e} | [{e.name}]({e.url})" for e in chunk),
                )

        for index, page in enumerate(self.pages, 1):
            page.title = f"{self.title} - {index}/{len(self.pages)}"

        self.eof = float(len(self.pages) - 1)
        self.controls["⏭"] = self.eof
        self.controller = ctx.bot.loop.create_task(self.reaction_controller(ctx))
