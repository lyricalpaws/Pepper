import discord
import requests
import io
import random

from random import randint
from art import text2art
from discord.ext import commands
from utils import default, lists, http, pagenator


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = default.get("config.json")

    @commands.command()
    async def jumbo(self, ctx, emoji: discord.PartialEmoji):
        """ Makes your emoji  B I G """
        def url_to_bytes(url):
            data = requests.get(url)
            content = io.BytesIO(data.content)
            tempurl = str(url)
            filename = tempurl.rsplit("/", 1)[-1]
            return {"content": content, "filename": filename}

        file = url_to_bytes(emoji.url)
        await ctx.send(file=discord.File(file["content"], file["filename"]))

    @commands.command()
    @commands.cooldown(rate=1, per=2.0, type=commands.BucketType.user)
    async def nitro(self, ctx, *, emoji: commands.clean_content):
        """ Allows you to use nitro emojis """
        nitromote = discord.utils.find(
            lambda e: e.name.lower() == emoji.lower(), self.bot.emojis
        )
        if nitromote is None:
            return await ctx.send(
                f":warning: | **Sorry, no matches found for `{emoji.lower()}`**"
            )
        await ctx.send(f"{nitromote}")

    @commands.command(aliases=["8ball"])
    @commands.guild_only()
    async def eightball(self, ctx, *, question: commands.clean_content):
        """ Consult 8ball to receive an answer """
        answer = random.choice(lists.ballresponse)
        await ctx.send(f"🎱 **Question:** {question}\n**Answer:** {answer}")

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def reverse(self, ctx, *, text: str):
        """ !poow ,ffuts esreveR """
        t_rev = text[::-1].replace("@", "@\u200B").replace("&", "&\u200B")
        await ctx.send(f"🔁 {t_rev}")

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def rate(self, ctx, *, thing: commands.clean_content):
        """ Rates what you desire """
        numbers = random.randint(0, 100)
        decimals = random.randint(0, 9)

        if numbers == 100:
            decimals = 0

        await ctx.send(f"I'd rate {thing} a **{numbers}.{decimals} / 100**")

    @commands.command(aliases=["howhot", "hot"])
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def hotcalc(self, ctx, user: discord.Member = None):
        """ Returns a random percent for how hot is a discord user """
        if user is None:
            user = ctx.author

        random.seed(user.id)
        r = random.randint(1, 100)
        hot = r / 1.17

        emoji = "💔"
        if hot > 25:
            emoji = "❤"
        if hot > 50:
            emoji = "💖"
        if hot > 75:
            emoji = "💞"

        await ctx.send(f"**{user.name}** is **{hot:.2f}%** hot {emoji}")

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def yell(self, ctx, *, text: str):
        """ AAAAAAAAA! """
        t_upper = text.upper().replace("@", "@\u200B").replace("&", "&\u200B")
        await ctx.send(f"⬆️ {t_upper}")

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def whisper(self, ctx, *, text: str):
        """ Shh Be quiet.. """
        t_lower = text.lower().replace("@", "@\u200B").replace("&", "&\u200B")
        await ctx.send(f"⬇️ {t_lower}")

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def ship(self, ctx, user: discord.User, *, user2: discord.User = None):
        """Checks the shiprate for 2 users"""
        author = ctx.message.author
        if not user2:
            user2 = author
        if not user:
            await ctx.send("can't ship nothing y'know..")
        elif user.id == user2.id:
            await ctx.send("i-i can't ship the same person..")
        elif user.id == author.id and user2.id == author.id:
            await ctx.send(f"wow, you're in love with yourself, huh {ctx.author.name}?")
        elif (user == self.bot.user and user2 == author or user2 == self.bot.user and user == author):
            blushes = ["m-me..? 0////0", "m-me..? >////<"]
            return await ctx.send(random.choice(blushes))

        else:
            n = randint(1, 100)
            if n == 100:
                bar = "██████████"
                heart = "💞"
            elif n >= 90:
                bar = "█████████."
                heart = "💕"
            elif n >= 80:
                bar = "████████.."
                heart = "😍"
            elif n >= 70:
                bar = "███████..."
                heart = "💗"
            elif n >= 60:
                bar = "██████...."
                heart = "❤"
            elif n >= 50:
                bar = "█████....."
                heart = "❤"
            elif n >= 40:
                bar = "████......"
                heart = "💔"
            elif n >= 30:
                bar = "███......."
                heart = "💔"
            elif n >= 20:
                bar = "██........"
                heart = "💔"
            elif n >= 10:
                bar = "█........."
                heart = "💔"
            elif n < 10:
                bar = ".........."
                heart = "🖤"
            else:
                bar = ".........."
                heart = "🖤"
            name1 = user.name.replace(" ", "")
            name1 = name1[: int(len(name1) / 2):]
            name2 = user2.name.replace(" ", "")
            name2 = name2[int(len(name2) / 2)::]
            ship = discord.Embed(
                description=f"**{n}%** **`{bar}`** {heart}", color=ctx.me.colour
            )
            ship.title = f"{user.name} x {user2.name}"
            ship.set_footer(text=f"Shipname: {str(name1 + name2).lower()}")
            await ctx.send(embed=ship)

    @commands.command(aliases=["👏"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def emojify(self, ctx, emote, *, text_to_clap: str):
        """ 👏bottom👏text👏 """
        clapped_text = (
            text_to_clap.replace("@everyone", f"{emote}everyone")
            .replace("@here", f"{emote}here")
            .replace(" ", f"{emote}")
        )
        clapped_text = f"{emote}{clapped_text}{emote}"
        await ctx.send(clapped_text)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def owo(self, ctx):
        """Sends a random owo face"""
        owo = random.choice(lists.owos)
        await ctx.send(f"{owo} whats this~?")

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def choose(self, ctx, *args):
        """Choose one of a lot (Split with |) """
        args = " ".join(args)
        args = str(args)
        choices = args.split("|")
        if len(choices) < 2:
            return await ctx.send("You need to send at least 2 choices!")
        await ctx.send(random.choice(choices))

    @commands.command(aliases=["ascii"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def asciify(self, ctx, *, text: str):
        """ Turns any text given into ascii """
        Art = text2art(text)
        asciiart = f"```\n{Art}\n```"
        if len(asciiart) > 2000:
            return await ctx.send("That art is too big")
        await ctx.send(asciiart)

    @commands.command()
    @commands.guild_only()
    async def markov(self, ctx):
        """Generates a Markov Chain"""
        await ctx.send(
            " ".join(
                random.sample(
                    [
                        m.clean_content
                        for m in await ctx.channel.history(limit=150).flatten()
                        if not m.author.bot
                    ],
                    10,
                )
            )
        )

    @commands.command(aliases=["inspire"])
    @commands.guild_only()
    @commands.cooldown(rate=2, per=5.0, type=commands.BucketType.user)
    async def inspireme(self, ctx):
        """ Fetch a random "inspirational message" from the bot. """
        page = await http.get(
            "http://inspirobot.me/api?generate=true", res_method="text", no_cache=True
        )
        embed = discord.Embed(colour=249_742)
        embed.set_image(url=page)
        await ctx.send(embed=embed)

    @commands.command(name="emojis", alisases=["emojis"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def _emojis(self, ctx, *, name: str = None):
        """ Display all emojis I can see in a paginated embed. """
        if name:
            emojis = [e for e in self.bot.emojis if name in e.name]
            if not emojis:
                return await ctx.send(
                    f"Could not find any emojis with search term: `{name}`"
                )

            chunks = [
                e
                async for e in pagenator.pager(sorted(emojis, key=lambda _: _.name), 8)
            ]
        else:
            chunks = [
                e
                async for e in pagenator.pager(
                    sorted(self.bot.emojis, key=lambda _: _.name), 8
                )
            ]

        pagey = pagenator.EmojiPaginator(title="Emojis", chunks=chunks)
        self.bot.loop.create_task(pagey.paginate(ctx))

    @commands.command()
    @commands.guild_only()
    async def randhex(self, ctx):
        randomHex = random.randint(0, 16777215)
        hexString = str(hex(randomHex))
        hexNumber = hexString[2:]
        embed = discord.Embed(title=f"#{hexNumber}", url=f"https://www.color-hex.com/color/{hexNumber}", colour=randomHex)
        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Misc(bot))
