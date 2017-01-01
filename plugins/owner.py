import inspect
import traceback

from curious import commands
from curious.commands.context import Context
from curious.commands.plugin import Plugin


def is_owner(self, ctx: Context):
    return ctx.author.id == 141545699442425856 or ctx.message.author.id == ctx.bot.application_info.owner.id


class Owner(Plugin):
    """
    Owner-only commands.
    """
    plugin_check = is_owner

    @commands.command(name="eval")
    async def _eval(self, ctx: Context, *, eval_str: str):
        msg = await ctx.channel.send("Evaluating...")
        try:
            result = eval(eval_str)
            if inspect.isawaitable(result):
                result = await result

            result = str(result)
        except Exception as e:
            tb = ''.join(traceback.format_exc())
            result = tb

        fmtted = "```py\n{}\n```".format(result)
        await msg.edit(fmtted)

    @commands.command(name="load", invokation_checks=[is_owner])
    async def _load(self, ctx: Context, *, import_name: str):
        """
        Loads a plugin.
        """
        await self.bot.load_plugins_from(import_name)
        await ctx.message.channel.send(":heavy_check_mark: Loaded.")

    @commands.command(name="unload", invokation_checks=[is_owner])
    async def _unload(self, ctx: Context, *, import_name: str):
        """
        Unloads a plugin.
        """
        await self.bot.unload_plugins_from(import_name)
        await ctx.message.channel.send(":heavy_check_mark: Unloaded.")
