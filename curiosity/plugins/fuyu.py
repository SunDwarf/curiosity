from curious.commands import command
from curious.commands.context import Context
from curious.commands.plugin import Plugin
from curious.http.curio_http import ClientSession

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

    @command()
    async def addbot(self, ctx: Context, bot_id: int):
        """
        Adds your bot to my server.

        Your bot must not be private. You will not get any permissions.
        """
        payload = {
            "guild_id": ctx.guild.id,
            "authorize": True,
            "permissions": 0
        }

        headers = {
            "Authorization": ctx.bot.config.get("bot_add_token"),
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2950.4 Safari/537.36",
            "Content-Type": "application/json"
        }

        async with ClientSession() as sess:
            response = await sess.post(AUTHORIZATION_URL,
                                       params={
                                           "client_id": str(bot_id),
                                           "scope": "bot"
                                       },
                                       headers=headers,
                                       json=payload)

            js = await response.json()
            if response.status_code != 200:
                await ctx.channel.send("\N{NO ENTRY SIGN} Failed to add bot to server! "
                                       "Error `{}`".format(js))
            else:
                if 'location' in js and 'invalid_request' in js['location']:
                    await ctx.channel.send("\N{NO ENTRY SIGN} Invalid client ID.")
                else:
                    await ctx.channel.send("\N{THUMBS UP SIGN} Added new bot.")
