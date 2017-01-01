"""
Main bot file for Curiosity.
"""
import inspect
import sys
import logging
import traceback

from logbook.compat import redirect_logging
from ruamel import yaml
from curious.commands.bot import CommandsBot
import logbook

from curious.commands.context import Context
from curious.dataclasses import Game
from curious.dataclasses import Message
from curious.dataclasses import Status
from curious.event import EventContext

redirect_logging()

logbook.StreamHandler(sys.stderr).push_application()

logging.getLogger().setLevel(level=logging.INFO)


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
        await self.load_plugins_from("plugins.owner")

    async def on_message_create(self, ctx: EventContext, message: Message):
        self.logger.info("Recieved message: {message.content} "
                         "from {message.author.name} ({message.author.user.name}){bot}"
                         .format(message=message, bot=" [BOT]" if message.author.user.bot else ""))
        self.logger.info(" On channel: #{message.channel.name}".format(message=message))
        if message.guild:
            self.logger.info(" On guild: {message.guild.name} ({message.guild.id})".format(message=message))


if __name__ == "__main__":
    bot = Curiosity()
    bot.run(shards=1)
