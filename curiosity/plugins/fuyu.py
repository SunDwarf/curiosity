import curio

from curious.commands import command
from curious.commands.context import Context
from curious.commands.plugin import Plugin
from curious.dataclasses import Member


def has_admin(ctx: Context):
    return ctx.channel.permissions(ctx.author).administrator


class Fuyu(Plugin):
    """
    Commands for my server.
    """

    async def plugin_check(self, ctx: Context):
        return ctx.guild.id == 198101180180594688

    @command(aliases=["shouting"], invokation_checks=[has_admin])
    async def screaming(self, ctx: Context):
        """
        Makes the server screaming.
        """
        coros = []
        for member in ctx.guild.members:
            coros.append(await curio.spawn(member.change_nickname(member.user.name.upper())))

        async with ctx.channel.typing:
            results = await curio.gather(coros, return_exceptions=True)
        exc = sum(1 for x in results if isinstance(x, Exception))

        await ctx.channel.send("AAAAAAAAAAAAAAAA (`{}` changed, `{}` failed)".format(len(results) - exc, exc))

    @command(aliases=["librarian"], invokation_checks=[has_admin])
    async def whispering(self, ctx: Context):
        """
        Makes the server quiet.
        """
        coros = []
        for member in ctx.guild.members:
            coros.append(await curio.spawn(member.change_nickname(member.user.name.lower())))

        async with ctx.channel.typing:
            results = await curio.gather(coros, return_exceptions=True)

        exc = sum(1 for x in results if isinstance(x, Exception))

        await ctx.channel.send(":zzz: (`{}` changed, `{}` failed)".format(len(results) - exc, exc))

    @command(invokation_checks=[has_admin])
    async def massnick(self, ctx: Context, prefix: str="", suffix: str=""):
        """
        Mass-nicks the server.
        """
        coros = []
        for member in ctx.guild.members:
            coros.append(await curio.spawn(member.change_nickname("{}{}{}".format(prefix, member.user.name, suffix))))

        async with ctx.channel.typing:
            results = await curio.gather(coros, return_exceptions=True)

        exc = sum(1 for x in results if isinstance(x, Exception))

        await ctx.channel.send(":100: (`{}` changed, `{}` failed)".format(len(results) - exc, exc))

    @command(aliases=["mute"], invokation_checks=[has_admin])
    async def parental_control(self, ctx: Context, victim: Member, timeout: int):
        """
        Mutes a member. Mention somebody and give a timeout in seconds.
        """
        role = ctx.guild.get_role(248525039400517632)
        if not role:
            await ctx.channel.send("<@133139430495092737>")
            return

        await ctx.guild.add_roles(victim, role)
        await ctx.channel.send("{} needs to sit out".format(victim.user.mention))
        await curio.sleep(timeout)
        await ctx.channel.send("{} is back in the arena".format(victim.user.mention))
        await ctx.guild.remove_roles(victim, role)

