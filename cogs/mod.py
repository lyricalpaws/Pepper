import discord
import re

from io import BytesIO
from discord.ext import commands
from utils import permissions, default


class MemberID(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            m = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                return int(argument, base=10)
            except ValueError:
                raise commands.BadArgument(
                    f"{argument} is not a valid member or member ID."
                ) from None
        else:
            can_execute = (ctx.author.id == ctx.bot.owner_id or ctx.author == ctx.guild.owner or ctx.author.top_role > m.top_role)

            if not can_execute:
                raise commands.BadArgument(
                    "You cannot do this action on this user due to role hierarchy."
                )
            return m.id


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = default.get("config.json")

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(kick_members=True)
    @commands.cooldown(rate=1, per=3.5, type=commands.BucketType.user)
    async def kick(self, ctx, member: discord.Member):
        """ Kicks a user from the current server. """
        try:
            await member.kick()
            await ctx.message.add_reaction("🔨")
        except discord.Forbidden as e:
            await ctx.send(e)

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(ban_members=True)
    @commands.cooldown(rate=1, per=3.5, type=commands.BucketType.user)
    async def ban(self, ctx, member: discord.Member):
        """ Bans a user from the current server. """
        try:
            await ctx.guild.ban(member)
            await ctx.message.add_reaction("🔨")
        except discord.Forbidden as e:
            await ctx.send(e)

    @commands.command(aliases=["hackban"])
    @commands.guild_only()
    @permissions.has_permissions(ban_members=True)
    @commands.cooldown(rate=1, per=3.5, type=commands.BucketType.user)
    async def idban(self, ctx, banmember: int):
        """ Bans a user id from the current server. """
        try:
            await ctx.guild.ban(discord.Object(id=banmember))
            await ctx.message.add_reaction("🔨")
        except discord.Forbidden as e:
            await ctx.send(e)

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(ban_members=True)
    @commands.cooldown(rate=1, per=3.5, type=commands.BucketType.user)
    async def unban(self, ctx, banmember: int, *, reason: str = None):
        """ Unbans a user from the current server. """
        try:
            await ctx.guild.unban(discord.Object(id=banmember))
            await ctx.message.add_reaction("🔨")
        except discord.Forbidden as e:
            await ctx.send(e)

    @commands.group(aliases=["purge"])
    @commands.guild_only()
    @permissions.has_permissions(manage_messages=True)
    @commands.cooldown(rate=1, per=3.5, type=commands.BucketType.user)
    async def prune(self, ctx):
        """ Removes messages from the current server. """

        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    async def do_removal(
        self, ctx, limit, predicate, *, before=None, after=None, message=True
    ):
        if limit > 2000:
            return await ctx.send(
                f"Too many messages to search given ({limit}/2000)"
            )

        if before is None:
            before = ctx.message
        else:
            before = discord.Object(id=before)

        if after is not None:
            after = discord.Object(id=after)

        try:
            deleted = await ctx.channel.purge(
                limit=limit, before=before, after=after, check=predicate
            )
        except discord.Forbidden:
            return await ctx.send("I do not have permissions to delete messages.")
        except discord.HTTPException as e:
            return await ctx.send(f"Error: {e} (try a smaller search?)")

        deleted = len(deleted)
        if message is True:
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass
            await ctx.send(
                f'🚮 Successfully removed {deleted} message{"" if deleted == 1 else "s"}.',
                delete_after=5,
            )
        else:
            if limit > 2000:
                return await ctx.send(
                    f"Too many messages to search given ({limit}/2000)"
                )

            if before is None:
                before = ctx.message
            else:
                before = discord.Object(id=before)

            if after is not None:
                after = discord.Object(id=after)

            try:
                deleted = await ctx.channel.purge(
                    limit=limit, before=before, after=after, check=predicate
                )
            except discord.Forbidden:
                return await ctx.send("I do not have permissions to delete messages.")
            except discord.HTTPException as e:
                return await ctx.send(f"Error: {e} (try a smaller search?)")

            deleted = len(deleted)
            if message is True:
                try:
                    await ctx.message.delete()
                except discord.Forbidden:
                    pass
                await ctx.send(
                    f'🚮 Successfully removed {deleted} message{"" if deleted == 1 else "s"}.',
                    delete_after=5,
                )

    @prune.command()
    async def embeds(self, ctx, search: int):
        """Removes messages that have embeds in them."""

        await self.do_removal(ctx, search, lambda e: len(e.embeds))

    @prune.command()
    async def files(self, ctx, search: int):
        """Removes messages that have attachments in them."""
        await self.do_removal(ctx, search, lambda e: len(e.attachments))

    @prune.command()
    async def images(self, ctx, search: int):
        """Removes messages that have embeds or attachments."""
        await self.do_removal(
            ctx, search, lambda e: len(e.embeds) or len(e.attachments)
        )

    @prune.command(name="all")
    async def _remove_all(self, ctx, search: int):
        """Removes all messages."""
        await self.do_removal(ctx, search, lambda e: True)

    @prune.command()
    async def user(self, ctx, member: discord.Member, search: int):
        """Removes all messages by the member."""
        await self.do_removal(ctx, search, lambda e: e.author == member)

    @prune.command()
    async def contains(self, ctx, *, substr: str):
        """Removes all messages containing a substring.
        The substring must be at least 3 characters long.
        """
        if len(substr) < 3:
            await ctx.send("The substring length must be at least 3 characters.")
        else:
            await self.do_removal(ctx, 100, lambda e: substr in e.content)

    @prune.command(name="bots")
    async def _bots(self, ctx, search: int):
        """Removes a bot user's messages and messages with their optional prefix."""

        def predicate(m):
            return m.author.bot

        await self.do_removal(ctx, search, predicate)

    @prune.command(name="users")
    async def _users(self, ctx, search: int):
        """Removes only user messages. """

        def predicate(m):
            return m.author.bot is False

        await self.do_removal(ctx, search, predicate)

    @prune.command(name="emoji")
    async def _emoji(self, ctx, search: int):
        """Removes all messages containing custom emoji."""
        custom_emoji = re.compile(r"<:(\w+):(\d+)>")

        def predicate(m):
            return custom_emoji.search(m.content)

        await self.do_removal(ctx, search, predicate)

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    @commands.cooldown(rate=2, per=3.5, type=commands.BucketType.user)
    async def ra(self, ctx, member: discord.Member, *, rolename: str = None):
        """ Gives the role to the user. """
        role = discord.utils.get(ctx.guild.roles, name=rolename)
        try:
            await member.add_roles(role)
        except discord.Forbidden:
            return await ctx.reply("I don't have perms ;w;")
        await ctx.reply(f"👌 I have given **{member.name}** the **{role.name}** role!")

    @commands.command()
    @commands.guild_only()
    @permissions.has_permissions(manage_roles=True)
    @commands.cooldown(rate=2, per=3.5, type=commands.BucketType.user)
    async def rr(self, ctx, member: discord.Member, *, rolename: str = None):
        """ Removes the role from a user. """
        role = discord.utils.get(ctx.guild.roles, name=rolename)
        try:
            await member.remove_roles(role)
        except discord.Forbidden:
            return await ctx.reply("I don't have perms ;w;")
        await ctx.reply(
            f"👌 I have removed **{member.name}** from the **{role.name}** role!"
        )

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(rate=2, per=3.5, type=commands.BucketType.user)
    async def move(self, ctx, msgid: int, channel: discord.TextChannel):
        """ Moves a message id to another channel. """
        msgtodel = await ctx.channel.fetch_message(msgid)
        if msgtodel.attachments:
            iobytes = BytesIO()
            await msgtodel.attachments[0].save(iobytes)
        await msgtodel.delete()
        await ctx.message.delete()
        if msgtodel.attachments:
            return await channel.send(
                f"```\n{msgtodel.author}: {msgtodel.content}\n```",
                file=discord.File(iobytes, "attachment.png"),
            )
        await channel.send(f"```\n{msgtodel.author}: {msgtodel.content}\n```")

    @commands.command(aliases=["channeltopic"])
    @commands.guild_only()
    @permissions.has_permissions(manage_channels=True)
    @commands.cooldown(rate=2, per=3.5, type=commands.BucketType.user)
    async def st(self, ctx, *, channeltopic=""):
        """ Sets channel topic. """
        await ctx.channel.edit(topic=channeltopic)
        await ctx.message.delete()


async def setup(bot):
    await bot.add_cog(Moderation(bot))
