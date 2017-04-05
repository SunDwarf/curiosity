import logging

import curio
import functools

from curious.util import attrdict

from curious.dataclasses.embed import Embed

from curious.commands.context import Context

from curious.commands import command, group
from fuzzywuzzy.fuzz import UWRatio, UQRatio
from sphinx.ext import intersphinx
from fuzzywuzzy import process

from curious.commands.plugin import Plugin

logger = logging.getLogger("curious.pydocs")


class MockSphinxApp:
    """
    Mock app used for downloading objects.inv.
    """

    def __init__(self, logger):
        self.config = attrdict({
            "intersphinx_timeout": None,
            "tls_verify": True
        })
        self.logger = logger

    def info(self, msg):
        self.logger.info(msg)

    def warn(self, msg):
        self.logger.warn(msg)


class Pydoc(Plugin):
    """
    Miscellaneous commands.
    """

    def __init__(self, bot):
        super().__init__(bot)

        # create the mock sphinx app
        self._app = MockSphinxApp(logger=logger)

        # items and invdata
        self._item_lengths = {}
        self.invdata = {}

    async def load(self):
        await curio.spawn(self._setup_pydocs(), daemon=True)

    async def _setup_pydocs(self):
        """
        Download objects.inv.
        """
        invdata = {}
        for name, obb in self.bot.config.get("docs", {}).items():
            logger.info("Fetching pydocs for {}...".format(name))
            # run inside a thread
            _data = await curio.abide(functools.partial(intersphinx.fetch_inventory, self._app,
                                                        '', obb))

            if _data is None:
                logger.error("Failed to download Pydoc source {}".format(obb))
                continue

            # Set the invdata of the current pydoc library
            invdata[name] = {}

            self._item_lengths[name] = 0
            logger.info("Downloaded pydocs for {}, processing items...".format(name))
            for kx, value in _data.items():
                if kx.startswith("std"):
                    # Ignore these, they're sphinx directives.
                    continue
                for key, subvals in value.items():
                    self._item_lengths[name] += 1
                    invdata[name][key] = subvals

            logger.info("Fetched {} keys.".format(self._item_lengths[name]))

        logger.info("Fetched all pydocs, with {} keys.".format(sum(self._item_lengths.values())))

        self.invdata = invdata

    @group()
    async def pydoc(self, ctx: Context, *, search: str):
        """
        Searches the current inventory data for pydocs.
        """
        # generator to prevent creating a massive fuck-off sublist
        def _get_items():
            for v in self.invdata.values():
                for subv in v:
                    yield subv

        # create a partial to use fuzzywuzzy to search
        # only extract 10
        f = functools.partial(process.extractBests, search, _get_items(), limit=10,
                              scorer=UQRatio)

        async with ctx.channel.typing:
            item = await curio.abide(f)

        if not item:
            await ctx.channel.send(":x: No results found.")
            return

        em = Embed(title="PyDoc search results")

        desc = "**Results for `{}`:**\n\n".format(search)
        for result in item:
            # get the key returned, and the score
            key, score = result

            # locate the key in any of the sources
            # this will scan each source and check it
            for name, v in self.invdata.items():
                try:
                    data = v[key]
                except KeyError:
                    continue
                else:
                    break
            else:
                # item was not found (wait, what?)
                # so we continue to the next item
                continue

            # get the source, lib version, and the URL
            doc, ver, url = data[0:3]

            # re-build the url because Sphinx
            base = self.bot.config["docs"][name]
            # remove the `objects.inv` from the end
            base = "/".join(base.split("/")[:-1]) + "/"
            # recombine
            url = base + url

            desc += "[`{}` from {} {}]({}) - score {}\n".format(key, doc, ver, url, score)

        em.description = desc
        await ctx.channel.send(embed=em)

    @pydoc.command()
    async def sources(self, ctx: Context):
        """
        Shows the sources that PyDoc is fetching.
        """
        em = Embed(title="PyDoc")
        em.description = "Scanned {} items total.".format(sum(self._item_lengths.values()))

        for name, source in self.invdata.items():
            # name is only used to look up the count
            count = self._item_lengths[name]

            # get a random value and get the doc and ver
            try:
                doc, ver, _ = next(iter(source.values()))[0:3]
            except StopIteration:
                continue

            em.add_field(name="{} - v{}".format(doc, ver), value="{} items".format(count))

        await ctx.channel.send(embed=em)
