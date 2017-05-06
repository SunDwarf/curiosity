import base64
import datetime
import inspect
import struct
import sys
import time

import binascii
import curio
import pyowm
from io import BytesIO
from pyowm.exceptions.api_call_error import APICallError
from pyowm.exceptions.api_response_error import APIResponseError
from pyowm.exceptions.parse_response_error import ParseResponseError
from pyowm.webapi25.forecast import Forecast
from pyowm.webapi25.forecaster import Forecaster
from pyowm.webapi25.location import Location
from pyowm.webapi25.observation import Observation
from pyowm.webapi25.weather import Weather
import psutil

import curious
from curiosity.bot import Curiosity
from curious.commands import command, group, Command
from curious.commands.context import Context
from curious.commands.plugin import Plugin
from curious.dataclasses.embed import Embed


class Misc(Plugin):
    """
    Miscellaneous commands.
    """

    def __init__(self, bot: Curiosity):
        super().__init__(bot)

        key = self.bot.config.get("owm_api_key")
        if not key:
            raise RuntimeError("No API key provided for OpenWeatherMap")

        self._owm = pyowm.OWM(API_key=key)

    @command()
    async def unpackdb(self, ctx: Context, *, b64: str):
        """
        Unpacks a dabBot track info string.
        """
        b64 += '=' * (-len(b64) % 4)
        try:
            unpacked = base64.b64decode(b64.encode())
        except binascii.Error:
            await ctx.channel.send("Unable to unpack track info")
            return

        # transform into a stream
        stream = BytesIO(unpacked)
        # skip the java header
        stream.read(4)
        # track info version
        i_ver = struct.unpack(">H", stream.read(2))
        # length-prefixed track name
        length = struct.unpack(">b", stream.read(1))[0]
        title = stream.read(length).decode()
        # null terminated?
        assert stream.read(1) == b"\x00"

        # length-prefixed author
        length = struct.unpack(">b", stream.read(1))[0]
        author = stream.read(length).decode()
        # null-terminated
        assert stream.read(1) == b"\x00"

        # i haven't been able to read the length properly
        # so skip 8 bytes
        stream.read(8)

        # read ident
        length = struct.unpack(">b", stream.read(1))[0]
        ident = stream.read(length).decode()
        assert stream.read(1) == b"\x00"

        # skip two for boolean?
        stream.read(2)
        length = struct.unpack(">b", stream.read(1))[0]
        url = stream.read(length).decode()

        em = Embed(title="Processed music")
        em.url = url
        em.add_field(name="Title", value=title, inline=False)
        em.add_field(name="Author", value=author)

        await ctx.channel.send(embed=em)

    @command()
    async def ping(self, ctx: Context):
        """
        Pings the bot.
        """
        before = time.monotonic()
        base = await ctx.channel.send("Pong!")
        after = time.monotonic()

        taken = round((after - before) * 1000, 2)
        gw_time = ctx.event_context.gateway.hb_stats.gw_time
        gw_time = round(gw_time * 1000, 2)
        await base.edit("Pong! | **HTTP latency: {}ms** | **Gateway latency: {}ms**".format(taken, gw_time))

    @command()
    async def source(self, ctx: Context, *, command: str):
        """
        Gets the source for a command.
        """
        parts = command.split(" ")

        command_obb = None  # type: Command

        for part in parts:
            command_obb = ctx.bot.get_command(part)

            if not command_obb:
                await ctx.channel.send(":x: No such command: `{}`".format(command))
                return

        # extract the source from the code object
        lines, firstlineno = inspect.getsourcelines(command_obb.callable.__code__)
        module = command_obb.callable.__module__.replace('.', '/') + '.py'
        url = '<https://github.com/SunDwarf/curiosity/blob/master/{}#L{}-L{}>'.format(module, firstlineno,
                                                                                      firstlineno + len(lines) - 1)

        await ctx.channel.send(url)

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
        em.add_field(name="Heartbeats", value=ctx.bot._gateways[ctx.event_context.shard_id].hb_stats.heartbeats)
        # general stats
        us = psutil.Process()
        used_memory = us.memory_info().rss
        used_memory = round(used_memory / 1024 / 1024, 2)
        cpu = us.cpu_percent()

        # get uptime
        start = us.create_time()
        uptime = time.time() - start
        m, s = divmod(uptime, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)

        em.add_field(name="Memory", value="{}MiB".format(used_memory))
        em.add_field(name="CPU", value="{}%".format(cpu))
        em.add_field(name="Uptime", value="{}d {}h {}m {}s".format(int(d), int(h), int(m), int(s)))

        em.set_footer(text="Curio is the future!")
        em.timestamp = datetime.datetime.now()
        em.colour = ctx.author.colour

        await ctx.channel.send(embed=em)

    # region weather

    @group()
    async def weather(self, ctx: Context, *, place: str):
        """
        Shows the current weather for the specified place.
        """
        async with ctx.channel.typing:
            try:
                result = await curio.abide(self._owm.weather_at_place, place)  # type: Observation
            except APICallError as e:
                await ctx.channel.send(":x: Error fetching results. Does this place exist?")
                return

            if not result:
                await ctx.channel.send(":x: No weather for `{}`.".format(place))
                return

            location = result.get_location()  # type: Location
            loc_name = location.get_name()
            loc_country = location.get_country()

            fmtted = "{}, {}".format(loc_name, loc_country)

            weather = result.get_weather()  # type: Weather

            status = weather.get_detailed_status().capitalize()

            # OWM api is awful.
            temperature = weather.get_temperature("celsius")
            rain = weather.get_rain()
            if rain:
                # bullshit API parsing
                rain_amount = rain.get("3h", rain.get("all", 0))

            pressure = weather.get_pressure()
            humidity = weather.get_humidity()
            snow = weather.get_snow()
            if snow:
                # bullshit API parsing
                snow_amount = snow.get("3h", snow.get("all", 0))

            status = weather.get_status()

            if 'rain' in status.lower():
                emoji = ":cloud_rain:"
            elif 'clear' in status.lower():
                emoji = ":sunny:"
            else:
                emoji = ":cloud:"

            wind = weather.get_wind().get("speed", 0)
            clouds = weather.get_clouds()

            embed = Embed(title="{} Weather for {}".format(emoji, fmtted), description=status)
            embed.add_field(name="Temperature", value="{} °C".format(temperature["temp"]))
            embed.add_field(name="Pressure", value="{} hPa".format(pressure['press']))
            embed.add_field(name="Humidity", value="{}%".format(humidity))

            if not rain:
                embed.add_field(name="Rain (last 3 hours)", value="No rain")
            else:
                embed.add_field(name="Rain (last 3 hours)", value="{}mm".format(rain_amount))

            if not snow:
                # yeah, we don't care.
                embed.add_field(name="Cloudiness", value="{}%".format(clouds))
            else:
                embed.add_field(name="Snow (last 3 hours)", value="{}mm".format(snow_amount))

            embed.add_field(name="Wind speed", value="{}mph".format(wind))
            embed.set_footer(text="Data provided by OpenWeatherMap")
            embed.timestamp = datetime.datetime.now()

        await ctx.channel.send(embed=embed)

    @weather.command()
    async def forecast(self, ctx: Context, *, place: str):
        """
        Shows the 3 hour weather forecast for the specified place.
        """
        async with ctx.channel.typing:
            try:
                result = await curio.abide(self._owm.daily_forecast, place, 1)  # type: Forecaster
            except (APICallError, APIResponseError) as e:
                await ctx.channel.send(":x: Error fetching results. Does this place exist?")
                return
            except ParseResponseError as e:
                await ctx.channel.send(":x: OWM is being stupid, please retry your request.")
                return

            forecast = result.get_forecast()  # type: Forecast
            location = forecast.get_location()  # type: Location

            fmtted = "{}, {}".format(location.get_name(), location.get_country())

            weather = forecast.get_weathers()[0]  # type: Weather

            status = weather.get_detailed_status().capitalize()

            # COPY PASTE O CLOCK
            temperature = weather.get_temperature("celsius")
            rain = weather.get_rain()
            if rain:
                rain_amount = rain.get("all", 0)

            pressure = weather.get_pressure()
            humidity = weather.get_humidity()
            snow = weather.get_snow()
            if snow:
                snow_amount = snow.get("3h", snow.get("all", 0))

            status = weather.get_status()

            if 'rain' in status.lower():
                emoji = ":cloud_rain:"
            elif 'clear' in status.lower():
                emoji = ":sunny:"
            else:
                emoji = ":cloud:"

            wind = weather.get_wind().get("speed", 0)
            clouds = weather.get_clouds()

            embed = Embed(title="{} Weather forecast for {}".format(emoji, fmtted), description=status)
            embed.add_field(name="Temperature (day)", value="{} °C".format(temperature["day"]))
            embed.add_field(name="Pressure", value="{} hPa".format(pressure['press']))
            embed.add_field(name="Humidity", value="{}%".format(humidity))

            if rain:
                embed.add_field(name="Rain", value="{}mm".format(rain_amount))
            else:
                embed.add_field(name="Rain", value="No rain forecast")

            embed.add_field(name="Cloudiness", value="{}%".format(clouds))
            embed.add_field(name="Wind speed", value="{}mph".format(wind))

            embed.set_footer(text="Data provided by OpenWeatherMap")
            embed.timestamp = weather.get_reference_time("date")

        await ctx.channel.send(embed=embed)

    # endregion
