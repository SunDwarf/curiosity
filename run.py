"""
Main bot file for Curiosity.
"""
import logging
import sys

import logbook
from logbook.compat import redirect_logging

from curiosity.bot import Curiosity
from curious.core.client import AUTOSHARD

redirect_logging()

logbook.StreamHandler(sys.stderr).push_application()

logging.getLogger().setLevel(level=logging.INFO)

if __name__ == "__main__":
    bot = Curiosity()
    bot.run(shards=AUTOSHARD)
