import inspect
import traceback
import sys

from curious.http.curio_http import ClientSession
from curious import commands
from curious.commands.context import Context
from curious.commands.plugin import Plugin


def is_owner(self, ctx: Context):
    return ctx.author.id == 214796473689178133 or ctx.message.author.id == ctx.bot.application_info.owner.id


class Owner(Plugin):
    """
    Owner-only commands.
    """
    plugin_check = is_owner

    @commands.command(name="eval")
    async def _eval(self, ctx: Context, *, eval_str: str):
        """
        [Eval](https://docs.python.org/3.6/library/functions.html#eval)uates a command.
        """
        msg = await ctx.channel.send("Evaluating...")
        try:
            result = eval(eval_str, {**sys.modules, **globals()}, locals())
            if inspect.isawaitable(result):
                result = await result

            result = str(result)
        except Exception as e:
            tb = ''.join(traceback.format_exc())
            result = tb

        fmtted = "```py\n{}\n```".format(result)
        await msg.edit(fmtted)

    @commands.command(name="name")
    async def _change_name(self, ctx: Context, *, new_name: str):
        """
        Changes the name of the bot.
        """
        await self.bot.edit_profile(username=new_name)
        await ctx.channel.send(":heavy_check_mark: Changed username.")

    @commands.command(name="avatar")
    async def _change_avatar(self, ctx: Context, *, avatar_url: str):
        """
        Changes the avatar of the bot.
        """
        sess = ClientSession()
        async with sess:
            req = await sess.get(avatar_url)
            if req.status_code != 200:
                await ctx.channel.send(":x: Could not download avatar.")
                return

            body = await req.binary()
            await self.bot.edit_profile(avatar=body)

    @commands.command(name="reload")
    async def _reload(self, ctx: Context, *, import_name: str):
        """
        Reloads a plugin.
        """
        await self.bot.unload_plugins_from(import_name)
        await self.bot.load_plugins_from(import_name)
        await ctx.channel.send(":heavy_check_mark: Reloaded.")

    @commands.command(name="load")
    async def _load(self, ctx: Context, *, import_name: str):
        """
        Loads a plugin.
        """
        await self.bot.load_plugins_from(import_name)
        await ctx.message.channel.send(":heavy_check_mark: Loaded.")

    @commands.command(name="unload")
    async def _unload(self, ctx: Context, *, import_name: str):
        """
        Unloads a plugin.
        """
        await self.bot.unload_plugins_from(import_name)
        await ctx.message.channel.send(":heavy_check_mark: Unloaded.")

    @commands.command(aliases=["harakiri", "sudoku"])
    async def seppeku(self, ctx: Context):
        """
        Please don't do this to me.
        """
        import ctypes
        await ctx.channel.send(":skull_and_crossbones:")
        ctypes.string_at(1)
