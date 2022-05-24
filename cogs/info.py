import time
import random
import discord
import psutil
import requests
import os
import json
import unicodedata

from datetime import datetime
from utils import pagenator, default
from discord.ext import commands
from discord.ui import Button, View


class Information(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.process = psutil.Process(os.getpid())

    def cleanup_code(self, content):
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])
        return content.strip("` \n")

    def get_bot_uptime(self, *, brief=False):
        now = datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        if not brief:
            if days:
                fmt = "{d} days, {h} hours, {m} minutes, and {s} seconds"
            else:
                fmt = "{h} hours, {m} minutes, and {s} seconds"
        else:
            fmt = "{h}h {m}m {s}s"
            if days:
                fmt = "{d}d " + fmt

        return fmt.format(d=days, h=hours, m=minutes, s=seconds)

    async def category_gen(self, ctx):
        categories = {}

        for command in set(ctx.bot.walk_commands()):
            try:
                if command.category not in categories:
                    categories.update({command.category: []})
            except AttributeError:
                cog = command.cog_name or "Bot"
                if command.cog_name not in categories:
                    categories.update({cog: []})

        for command in set(ctx.bot.walk_commands()):
            if not command.hidden:
                try:
                    if command.category:
                        categories[command.category].append(command)
                except AttributeError:
                    cog = command.cog_name or "Bot"
                    categories[cog].append(command)

        return categories

    async def commandMapper(self, ctx):
        pages = []

        for category, commands in (await self.category_gen(ctx)).items():
            if not commands:
                continue
            cog = ctx.bot.get_cog(category)
            if cog:
                category = f"**⚙️ {category}**"
            commands = ", ".join([c.qualified_name for c in commands])
            embed = (
                discord.Embed(
                    color=random.randint(0x000000, 0xFFFFFF),
                    title=f"{ctx.bot.user.display_name} Commands",
                    description=f"{category}",
                )
                .set_footer(
                    text=f"Type {ctx.prefix}help <command> for more help".replace(
                        ctx.me.mention, "@Pawbot "
                    ),
                    icon_url=ctx.author.avatar,
                )
                .add_field(name="**Commands:**", value=f"``{commands}``")
            )
            pages.append(embed)
        await pagenator.SimplePaginator(
            extras=sorted(pages, key=lambda d: d.description)
        ).paginate(ctx)

    async def cogMapper(self, ctx, entity, cogname: str):
        try:
            await ctx.send(
                embed=discord.Embed(
                    color=random.randint(0x000000, 0xFFFFFF),
                    title=f"{ctx.bot.user.display_name} Commands",
                    description=f"**⚙️ {cogname}**",
                )
                .add_field(
                    name="**Commands:**",
                    value=f"``{', '.join([c.qualified_name for c in set(ctx.bot.walk_commands()) if c.cog_name == cogname])}``",
                )
                .set_footer(
                    text=f"Type {ctx.prefix}help <command> for more help".replace(
                        ctx.me.mention, "@Pawbot "
                    ),
                    icon_url=ctx.author.avatar_url,
                )
            )
        except BaseException:
            await ctx.send(
                f":x: | **Command or category not found. Use {ctx.prefix}help**",
                delete_after=10,
            )

    @commands.command(aliases=["?"])
    async def help(self, ctx, *, command: str = None):
        """View Bot Help Menu"""
        if not command:
            await self.commandMapper(ctx)
        else:
            entity = self.bot.get_cog(command) or self.bot.get_command(command)
            if entity is None:
                return await ctx.send(
                    f":x: | **Command or category not found. Use {ctx.prefix}help**",
                    delete_after=10,
                )
            if isinstance(entity, commands.Command):
                await pagenator.SimplePaginator(
                    title=f"Command: {entity.name}",
                    entries=[
                        f"**:bulb: Command Help**\n```ini\n[{entity.help}]```",
                        f"**:video_game: Command Signature**\n```ini\n{entity.signature}```",
                    ],
                    length=1,
                    colour=random.randint(0x000000, 0xFFFFFF),
                ).paginate(ctx)
            else:
                await self.cogMapper(ctx, entity, command)

    @commands.command()
    async def ping(self, ctx):
        """ Pong! """
        before = time.monotonic()
        message = await ctx.send("Did you just ping me?!")
        ping = (time.monotonic() - before) * 1000
        await message.edit(
            content=f"`MSG :: {int(ping)}ms\nAPI :: {round(self.bot.latency * 1000)}ms`"
        )

    @commands.command()
    async def invite(self, ctx):
        """ Get an invite for me! """
        button = Button(label="Invite Me!", style=discord.ButtonStyle.link, url=f"https://discord.com/api/oauth2/authorize?client_id={self.bot.application_id}&permissions=8&scope=bot", emoji="<a:catdancerainbow:720036266183491756>")
        view = View()
        view.add_item(button)
        await ctx.send("To invite me, use the \"Add to Server\" button on my profile, or click below!", view=view)

    @commands.command()
    async def about(self, ctx):
        """Tells you information about the bot itself."""
        embed = discord.Embed()
        embed.colour = discord.Colour.blurple()

        botinfo = self.bot.get_user(926180613470425118)
        embed.set_author(name=str(botinfo), icon_url=botinfo.avatar)

        # statistics
        total_members = sum(1 for _ in self.bot.get_all_members())
        total_online = len(
            {
                m.id
                for m in self.bot.get_all_members()
                if m.status is not discord.Status.offline
            }
        )
        total_unique = len(self.bot.users)

        voice_channels = []
        text_channels = []
        for guild in self.bot.guilds:
            voice_channels.extend(guild.voice_channels)
            text_channels.extend(guild.text_channels)

        text = len(text_channels)
        voice = len(voice_channels)

        embed.add_field(
            name="Members",
            value=f"{total_members} total\n{total_unique} unique\n{total_online} unique online",
        )
        embed.add_field(
            name="Channels", value=f"{text + voice} total\n{text} text\n{voice} voice"
        )

        memory_usage = self.process.memory_full_info().uss / 1024 ** 2
        cpu_usage = self.process.cpu_percent() / psutil.cpu_count()
        embed.add_field(
            name="Process", value=f"{memory_usage:.2f} MiB\n{cpu_usage:.2f}% CPU"
        )

        embed.add_field(name="Guilds", value=len(self.bot.guilds))
        embed.add_field(name="Uptime", value=self.get_bot_uptime(brief=True))
        embed.add_field(name="Owner", value="Paws#7605")
        embed.set_footer(
            text="Made with Pycord", icon_url="http://i.imgur.com/5BFecvA.png"
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def joinedat(self, ctx, user: discord.Member = None):
        """ Check when a user joined the current server """

        if user is None:
            user = ctx.author

        embed = discord.Embed(colour=249_742)
        embed.set_thumbnail(url=user.avatar)
        embed.description = (
            f"**{user}** joined **{ctx.guild.name}**\n{default.date(user.joined_at)}"
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def server(self, ctx):
        """ Check info about current server """
        if ctx.invoked_subcommand is None:

            findbots = sum(1 for member in ctx.guild.members if member.bot)

            emojilist = "​"
            for Emoji in ctx.guild.emojis:
                emojilist += f"{Emoji} "
            if len(emojilist) > 1024:
                emojilist = "Too long!"

            embed = discord.Embed(colour=249_742)
            embed.set_thumbnail(url=ctx.guild.icon)
            embed.add_field(name="Server Name", value=ctx.guild.name, inline=True)
            embed.add_field(name="Server ID", value=ctx.guild.id, inline=True)
            embed.add_field(name="Members", value=ctx.guild.member_count, inline=True)
            embed.add_field(name="Bots", value=findbots, inline=True)
            embed.add_field(name="Owner", value=ctx.guild.owner, inline=True)
            embed.add_field(name="Emojis", value=emojilist, inline=False)
            embed.add_field(
                name="Created", value=default.date(ctx.guild.created_at), inline=False
            )
            await ctx.send(
                content=f"ℹ information about **{ctx.guild.name}**", embed=embed
            )

    @commands.command()
    @commands.guild_only()
    async def user(self, ctx, user: discord.Member = None):
        """ Get user information """
        if user is None:
            user = ctx.author

        embed = discord.Embed(colour=249_742)

        usrstatus = user.status

        if usrstatus == "online" or usrstatus == discord.Status.online:
            usrstatus = "<:online:514203909363859459> Online"
        elif usrstatus == "idle" or usrstatus == discord.Status.idle:
            usrstatus = "<:away:514203859057639444> Away"
        elif usrstatus == "dnd" or usrstatus == discord.Status.dnd:
            usrstatus = "<:dnd:514203823888138240> DnD"
        elif usrstatus == "offline" or usrstatus == discord.Status.offline:
            usrstatus = "<:offline:514203770452836359> Offline"
        else:
            usrstatus = "Broken"

        if user.nick:
            nick = user.nick
        else:
            nick = "No Nickname"

        if user.activity:
            usrgame = f"{user.activity.name}"
        else:
            usrgame = "No current game"

        usrroles = ""

        for Role in user.roles:
            if "@everyone" in Role.name:
                usrroles += "| @everyone | "
            else:
                usrroles += f"{Role.name} | "

        if len(usrroles) > 1024:
            usrroles = "Too many to count!"

        embed.set_thumbnail(url=user.avatar)
        embed.add_field(
            name="Name",
            value=f"{user.name}#{user.discriminator}\n{nick}\n({user.id})",
            inline=True,
        )
        embed.add_field(name="Status", value=usrstatus, inline=True)
        embed.add_field(name="Game", value=usrgame, inline=True)
        embed.add_field(name="Is bot?", value=user.bot, inline=True)
        embed.add_field(name="Roles", value=usrroles, inline=False)
        embed.add_field(
            name="Created On", value=default.date(user.created_at), inline=True
        )
        if hasattr(user, "joined_at"):
            embed.add_field(
                name="Joined this server",
                value=default.date(user.joined_at),
                inline=True,
            )
        await ctx.send(content=f"ℹ About **{user.name}**", embed=embed)

    @commands.command(name="eval")
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
    async def _eval(self, ctx, *, code: commands.clean_content):
        """ Runs a piece of python code """
        r = requests.post(
            "http://coliru.stacked-crooked.com/compile",
            data=json.dumps(
                {"cmd": "python3 main.cpp", "src": self.cleanup_code(code)}
            ),
        )
        emoji = self.bot.get_emoji(508_388_437_661_843_483)
        await ctx.message.add_reaction(emoji)
        await ctx.send(
            f"```py\n{r.text}\n```\n(This is **not** an open eval, everything is sandboxed)"
        )

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(rate=2, per=5.0, type=commands.BucketType.user)
    async def charinfo(self, ctx, *, characters: str):
        """ Shows you information about a number of characters. """

        def to_string(c):
            digit = f"{ord(c):x}"
            name = unicodedata.name(c, "Name not found.")
            return f"`\\U{digit:>08}`: {name} - {c} \N{EM DASH} <http://www.fileformat.info/info/unicode/char/{digit}>"

        msg = "\n".join(map(to_string, characters))
        if len(msg) > 2000:
            return await ctx.send("Output too long to display.")
        await ctx.send(msg)


async def setup(bot):
    await bot.add_cog(Information(bot))
