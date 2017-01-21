import datetime
import sys

import curio

import curious
from curious.commands import command
from curious.commands.context import Context
from curious.commands.plugin import Plugin
from curious.dataclasses.embed import Embed


class Misc(Plugin):
    """
    Miscellaneous commands.
    """
    @command()
    async def info(self, ctx: Context):
        """
        Shows info about the bot.
        """
        em = Embed(title=ctx.guild.me.user.name, description="The official bot for the curious library")
        em.add_field(name="Curious version", value=curious.__version__)
        em.add_field(name="Curio version", value=curio.__version__)
        em.add_field(name="CPython version", value="{}.{}.{}".format(*sys.version_info[0:3]))
        # bot stats
        em.add_field(name="Shard ID", value=ctx.event_context.shard_id)
        em.add_field(name="Shard count", value=ctx.event_context.shard_count)
        em.add_field(name="Heartbeats", value=ctx.bot._gateways[ctx.event_context.shard_id].heartbeats)

        em.set_footer(text="Curio is the future!")
        em.timestamp = datetime.datetime.now()

        await ctx.channel.send(embed=em)

