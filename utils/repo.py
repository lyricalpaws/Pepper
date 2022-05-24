from utils import default

version = "v1.0.0"
invite = ""
owners = default.get("config.json").owners
contributors = default.get("config.json").contributors


def is_owner(ctx):
    return ctx.author.id in owners


def is_contributor(ctx):
    return ctx.author.id in contributors


def has_userid(ctx, userid):
    return ctx.author.id in userid


def has_guildid(ctx, guildid):
    return ctx.guild.id in guildid


def has_channelid(ctx, channelid):
    return ctx.channel.id in channelid
