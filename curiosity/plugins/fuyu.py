from curious.commands import command
from curious.commands.context import Context
from curious.commands.plugin import Plugin

AUTHORIZATION_URL = "https://discordapp.com/api/v6/oauth2/authorize"


def has_admin(ctx: Context):
    return ctx.channel.permissions(ctx.author).administrator


class Fuyu(Plugin):
    """
    Commands for my server.
    """

    async def plugin_check(self, ctx: Context):
        return ctx.guild.id == 198101180180594688

    @command(aliases=["guildname"])
    async def servername(self, ctx: Context, *, server_name: str):
        """
        Changes the name of my guild.
        """
        await ctx.guild.modify_guild(name="Fuyu is {}".format(server_name))
        await ctx.channel.send(":heavy_check_mark: Changed guild name.")


