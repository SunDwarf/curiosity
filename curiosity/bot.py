import traceback

import logbook
from ruamel import yaml

from curious.commands.bot import CommandsBot
from curious.commands.context import Context
from curious.commands.exc import CheckFailureError, MissingArgumentError, ConversionFailedError
from curious.dataclasses import Game, Status, Message
from curious.event import EventContext
from curious.ext.paginator import ReactionsPaginator


class Curiosity(CommandsBot):
    def __init__(self):
        try:
            with open("config.yml") as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError as e:
            print("You need to make a config.yml.")
            raise SystemExit(1) from e

        token = self.config["bot_token"]
        super().__init__(token, command_prefix="c!")

        self.logger = logbook.Logger("curiosity")

    async def on_command_error(self, ctx: Context, exc: Exception):
        if isinstance(exc, (CheckFailureError, MissingArgumentError, ConversionFailedError)):
            await ctx.channel.send(":x: {}".format(str(exc)))
        else:
            fmtted = traceback.format_exception(None, exc.__cause__, exc.__cause__.__traceback__)
            final = "```{}```".format(''.join(fmtted))
            if len(final) < 1900:
                await ctx.channel.send(final)
            else:
                items = ["```{}```".format(i) for i in traceback.format_exception(None, exc.__cause__,
                                                                                  exc.__cause__.__traceback__)]
                p = ReactionsPaginator(channel=ctx.channel, content=items, respond_to=ctx.message.author.user)
                await p.paginate()

    async def on_connect(self, ctx):
        self.logger.info("Connected to Discord on shard {0}, "
                         "logged in as {1.name}#{1.discriminator}.".format(ctx.shard_id, self.user))
        self.logger.info("I am owned by {0.name}#{0.discriminator}.".format(self.application_info.owner))
        self.logger.info("Invite URL: {}".format(self.invite_url))

        await self.change_status(game=Game(name="curiosity loading..."), status=Status.DND, shard_id=ctx.shard_id)

    async def on_ready(self, ctx):
        await self.change_status(game=Game(
            name="[shard {}/{}] curio is the future!".format(ctx.shard_id + 1, self.shard_count)
        ), status=Status.ONLINE, shard_id=ctx.shard_id)

        if ctx.shard_id != 0:
            return

        plugins = self.config.get("plugins", [])
        for plugin in plugins:
            try:
                await self.load_plugins_from(plugin)
            except:
                self.logger.exception("Failed to load {}!".format(plugin))
            else:
                self.logger.info("Loaded plugin {}.".format(plugin))

    async def on_message_create(self, ctx: EventContext, message: Message):
        self.logger.info("Recieved message: {message.content} "
                         "from {message.author.name} ({message.author.user.name}){bot}"
                         .format(message=message, bot=" [BOT]" if message.author.user.bot else ""))
        self.logger.info(" On channel: #{message.channel.name}".format(message=message))
        if message.guild:
            self.logger.info(" On guild: {message.guild.name} ({message.guild.id})".format(message=message))
