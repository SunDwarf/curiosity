"""
Generic mod plugin etc
"""
from curious import commands
from curious.commands.context import Context
from curious.commands.plugin import Plugin


class Moderation(Plugin):
    @commands.command(aliases=["eanup"])
    async def cleanup(self, ctx: Context):
        """
        Cleans up the bot's messages.
        """
        removed = await ctx.channel.purge(limit=100, author=ctx.guild.me, fallback_from_bulk=True)
        await ctx.channel.send("Removed `{}` messages.".format(removed))
