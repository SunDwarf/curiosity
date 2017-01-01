import inspect
import traceback

from curious import commands
from curious.commands.context import Context
from curious.commands.plugin import Plugin


class Owner(Plugin):
    """
    Owner-only commands.
    """
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
