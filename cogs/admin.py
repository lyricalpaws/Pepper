import discord
import time
import aiohttp
import traceback
import io
import textwrap
import gc
import json

from dhooks import Webhook
from contextlib import redirect_stdout
from discord.ext import commands
from utils import default, repo, http, dataIO
from copy import copy
from typing import Union


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = default.get("config.json")
        self._last_result = None

    @staticmethod
    def cleanup_code(content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])

        # remove `foo`
        return content.strip("` \n")

    @staticmethod
    def get_syntax_error(e):
        if e.text is None:
            return f"```py\n{e.__class__.__name__}: {e}\n```"
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    async def say_permissions(self, ctx, member, channel):
        permissions = channel.permissions_for(member)
        e = discord.Embed(colour=member.colour)
        allowed, denied = [], []
        for name, value in permissions:
            name = name.replace("_", " ").replace("guild", "server").title()
            if value:
                allowed.append(name)
            else:
                denied.append(name)

        e.add_field(name="Allowed", value="\n".join(allowed))
        e.add_field(name="Denied", value="\n".join(denied))
        await ctx.send(embed=e)

    @commands.command(hidden=True)
    @commands.check(repo.is_owner)
    async def cogs(self, ctx):
        """ Gives all loaded cogs """
        mod = ", ".join(list(self.bot.cogs))
        await ctx.send(f"The current modules are:\n```\n{mod}\n```")

    @commands.command(aliases=["re"], hidden=True)
    @commands.check(repo.is_owner)
    async def reload(self, ctx, name: str):
        """ Reloads an extension. """
        await ctx.message.add_reaction("a:loading:528744937794043934")
        try:
            self.bot.unload_extension(f"cogs.{name}")
            self.bot.load_extension(f"cogs.{name}")
        except ModuleNotFoundError:
            await ctx.message.remove_reaction(
                "a:loading:528744937794043934", member=ctx.me
            )
            return await ctx.message.add_reaction(":notdone:528747883571445801")
        except SyntaxError:
            await ctx.message.remove_reaction(
                "a:loading:528744937794043934", member=ctx.me
            )
            return await ctx.message.add_reaction(":notdone:528747883571445801")
        await ctx.message.remove_reaction("a:loading:528744937794043934", member=ctx.me)
        await ctx.message.add_reaction(":done:513831607262511124")

    @commands.command(hidden=True)
    @commands.check(repo.is_owner)
    async def reboot(self, ctx):
        """ Reboot the bot """
        await ctx.send("Rebooting now...")
        time.sleep(1)
        await self.bot.logout()

    @commands.command(hidden=True)
    @commands.check(repo.is_owner)
    async def load(self, ctx, name: str):
        """ Loads an extension. """
        await ctx.message.add_reaction("a:loading:528744937794043934")
        try:
            self.bot.load_extension(f"cogs.{name}")
        except ModuleNotFoundError:
            await ctx.message.remove_reaction(
                "a:loading:528744937794043934", member=ctx.me
            )
            return await ctx.message.add_reaction(":notdone:528747883571445801")
        except SyntaxError:
            await ctx.message.remove_reaction(
                "a:loading:528744937794043934", member=ctx.me
            )
            return await ctx.message.add_reaction(":notdone:528747883571445801")
        await ctx.message.remove_reaction("a:loading:528744937794043934", member=ctx.me)
        await ctx.message.add_reaction(":done:513831607262511124")

    @commands.command(hidden=True)
    @commands.check(repo.is_owner)
    async def unload(self, ctx, name: str):
        """ Unloads an extension. """
        await ctx.message.add_reaction("a:loading:528744937794043934")
        try:
            self.bot.unload_extension(f"cogs.{name}")
        except ModuleNotFoundError:
            await ctx.message.remove_reaction(
                "a:loading:528744937794043934", member=ctx.me
            )
            return await ctx.message.add_reaction(":notdone:528747883571445801")
        except SyntaxError:
            await ctx.message.remove_reaction(
                "a:loading:528744937794043934", member=ctx.me
            )
            return await ctx.message.add_reaction(":notdone:528747883571445801")
        await ctx.message.remove_reaction("a:loading:528744937794043934", member=ctx.me)
        await ctx.message.add_reaction(":done:513831607262511124")

    @commands.group(hidden=True)
    @commands.check(repo.is_owner)
    async def change(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Syntax:```{ctx.prefix}change <playing|username|nickname|avatar>```")

    @change.command(name="playing", hidden=True)
    @commands.check(repo.is_owner)
    async def change_playing(self, ctx, *, playing: str):
        """ Change playing status. """
        try:
            await self.bot.change_presence(
                activity=discord.Game(type=0, name=playing),
                status=discord.Status.online,
            )
            dataIO.change_value("config.json", "playing", playing)
            await ctx.send(f"Successfully changed playing status to **{playing}**")
        except discord.InvalidArgument as err:
            await ctx.send(err)
        except Exception as e:
            await ctx.send(e)

    @change.command(name="username", hidden=True)
    @commands.check(repo.is_owner)
    async def change_username(self, ctx, *, name: str):
        """ Change username. """
        try:
            await self.bot.user.edit(username=name)
            await ctx.send(f"Successfully changed username to **{name}**")
        except discord.HTTPException as err:
            await ctx.send(err)

    @change.command(name="nickname", hidden=True)
    @commands.check(repo.is_owner)
    async def change_nickname(self, ctx, *, name: str = None):
        """ Change nickname. """
        try:
            await ctx.guild.me.edit(nick=name)
            if name:
                await ctx.send(f"Successfully changed nickname to **{name}**")
            else:
                await ctx.send("Successfully removed nickname")
        except Exception as err:
            await ctx.send(err)

    @change.command(name="avatar", hidden=True)
    @commands.check(repo.is_owner)
    async def change_avatar(self, ctx, url: str = None):
        """ Change avatar. """
        if url is None and len(ctx.message.attachments) == 1:
            url = ctx.message.attachments[0].url
        else:
            url = url.strip("<>")

        try:
            bio = await http.get(url, res_method="read")
            await self.bot.user.edit(avatar=bio)
            await ctx.send(f"Successfully changed the avatar. Currently using:\n{url}")
        except aiohttp.InvalidURL:
            await ctx.send("The URL is invalid...")
        except discord.InvalidArgument:
            await ctx.send("This URL does not contain a usable image")
        except discord.HTTPException as err:
            await ctx.send(err)

    @commands.command(pass_context=True, name="compile", hidden=True)
    @commands.check(repo.is_owner)
    async def _compile(self, ctx, *, body: str):
        """ Compiles some code """
        env = {
            "bot": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "_": self._last_result,
        }

        if "bot.http.token" in body:
            return await ctx.send(f"You can't take my token {ctx.author.name}")
        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            start = time.perf_counter()
            exec(to_compile, env)
        except EnvironmentError as e:
            return await ctx.send(f"```py\n{e.__class__.__name__}: {e}\n```")

        func = env["func"]
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            value = stdout.getvalue()
            await ctx.send(f"```py\n{value}{traceback.format_exc()}\n```")
        else:
            try:
                value = stdout.getvalue()
                reactiontosend = self.bot.get_emoji(508_388_437_661_843_483)
                await ctx.message.add_reaction(reactiontosend)
                dt = (time.perf_counter() - start) * 1000.0
            except discord.Forbidden:
                return await ctx.send("I couldn't react...")

            if ret is None:
                if value:
                    await ctx.send(f"```py\n{value}\n```")
            else:
                if self.config.token in ret:
                    ret = self.config.realtoken
                self._last_result = ret
                await ctx.send(
                    f"Inputted code:\n```py\n{body}\n```\n\nOutputted Code:\n```py\n{value}{ret}\n```\n*Compiled in {dt:.2f}ms*"
                )

    @commands.group(aliases=["as"], hidden=True)
    @commands.check(repo.is_owner)
    async def sudo(self, ctx):
        """ Run a cmd under an altered context """
        if ctx.invoked_subcommand is None:
            await ctx.send("...")

    @sudo.command(aliases=["user"], hidden=True)
    @commands.check(repo.is_owner)
    async def sudo_user(
        self, ctx, who: Union[discord.Member, discord.User], *, command: str
    ):
        """ Run a cmd under someone else's name """
        msg = copy(ctx.message)
        msg.author = who
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg)
        await self.bot.invoke(new_ctx)
        await ctx.message.add_reaction(":done:513831607262511124")

    @sudo.command(aliases=["channel"], hidden=True)
    @commands.check(repo.is_owner)
    async def sudo_channel(self, ctx, chid: int, *, command: str):
        """ Run a command in a different channel. """
        cmd = copy(ctx.message)
        cmd.channel = self.bot.get_channel(chid)
        cmd.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(cmd)
        await self.bot.invoke(new_ctx)
        await ctx.message.add_reaction(":done:513831607262511124")

    @commands.command(aliases=["gsi"], hidden=True)
    @commands.check(repo.is_owner)
    async def getserverinfo(self, ctx, *, guild_id: int):
        """ Makes me get the information from a guild id """
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return await ctx.send("Hmph.. I got nothing..")
        members = set(guild.members)
        bots = filter(lambda m: m.bot, members)
        bots = set(bots)
        members = len(members) - len(bots)
        roles = ", ".join([x.name for x in guild.roles if x.name != guild.default_role])

        info = discord.Embed(
            title="Guild info",
            description=f"» Name: {guild.name}\n» Members/Bots: `{members}:{len(bots)}\n» Owner: {guild.owner}\n» Created at: {guild.created_at}",
            color=discord.Color.blue())
        info.set_thumbnail(url=guild.icon)
        roles = discord.Embed(title="Guild roles", description=f"» Roles: {roles}", color=discord.Color.blue())
        await ctx.send(embed=info)
        await ctx.send(embed=roles)

    @commands.command(aliases=["webhooktest"], hidden=True)
    @commands.check(repo.is_owner)
    async def whtest(self, ctx, whlink: str, *, texttosend):
        """ Messages a webhook """
        await ctx.message.add_reaction("a:loading:528744937794043934")
        try:
            hook = Webhook(whlink, is_async=True)
            await hook.send(texttosend)
            await hook.close()
            await ctx.message.remove_reaction(
                "a:loading:528744937794043934", member=ctx.me
            )
            await ctx.message.add_reaction(":done:513831607262511124")
        except ValueError:
            await ctx.message.remove_reaction(
                "a:loading:528744937794043934", member=ctx.me
            )
            await ctx.message.add_reaction(":notdone:528747883571445801")

    @commands.command(hidden=True, aliases=["botperms"])
    @commands.guild_only()
    @commands.check(repo.is_owner)
    async def botpermissions(self, ctx, *, channel: discord.TextChannel = None):
        """ Shows the bot's permissions in a specific channel. """
        channel = channel or ctx.channel
        member = ctx.guild.me
        await self.say_permissions(ctx, member, channel)

    @commands.command(hidden=True)
    @commands.guild_only()
    @commands.check(repo.is_owner)
    async def speedup(self, ctx):
        await ctx.message.add_reaction("a:loading:528744937794043934")
        gc.collect()
        del gc.garbage[:]
        await ctx.message.remove_reaction("a:loading:528744937794043934", member=ctx.me)
        await ctx.message.add_reaction(":done:513831607262511124")

    @commands.command(hidden=True)
    @commands.guild_only()
    @commands.check(repo.is_owner)
    async def guildlist(self, ctx):
        guildlist = []
        out_filename = "death.json"
        for guild in self.bot.guilds:
            guildlist.append(f"{guild.id} Owner: {guild.owner.name}#{guild.owner.discriminator} ID {guild.owner_id}")
        with open(out_filename, 'w') as outf:
            json.dump(guildlist, outf)
        await ctx.message.delete()

    @commands.command(aliases=["say"], hidden=True)
    @commands.guild_only()
    @commands.check(repo.is_owner)
    async def echo(self, ctx, *, text: str):
        """ Says what you want """
        await ctx.send(text)
        await ctx.message.delete()


async def setup(bot):
    await bot.add_cog(Admin(bot))
