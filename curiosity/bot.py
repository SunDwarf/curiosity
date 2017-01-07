import traceback

import logbook
from ruamel import yaml

from curious.commands.bot import CommandsBot
from curious.commands.context import Context
from curious.commands.exc import CheckFailureError, MissingArgumentError
from curious.dataclasses import Game, Status, Message
from curious.event import EventContext


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
        if isinstance(exc, (CheckFailureError, MissingArgumentError)):
            await ctx.channel.send(":x: {}".format(str(exc)))
        else:
            fmtted = traceback.format_exception(None, exc, exc.__traceback__)
            await ctx.channel.send("```{}```".format(''.join(fmtted)))

    async def on_connect(self, ctx):
        self.logger.info("Connected to Discord on shard {0}, "
                         "logged in as {1.name}#{1.discriminator}.".format(ctx.shard_id, self.user))
        self.logger.info("I am owned by {0.name}#{0.discriminator}.".format(self.application_info.owner))
        self.logger.info("Invite URL: {}".format(self.invite_url))

        await self.change_status(game=Game(
            name="[shard {}/{}] curio is the future!".format(ctx.shard_id + 1, self.shard_count)
        ), status=Status.DND, shard_id=ctx.shard_id)

    async def on_ready(self, ctx):
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
