import datetime
import sys

import curio
import pyowm
from pyowm.exceptions.api_call_error import APICallError
from pyowm.exceptions.api_response_error import APIResponseError
from pyowm.exceptions.parse_response_error import ParseResponseError
from pyowm.webapi25.forecast import Forecast
from pyowm.webapi25.forecaster import Forecaster
from pyowm.webapi25.location import Location
from pyowm.webapi25.observation import Observation
from pyowm.webapi25.weather import Weather

import curious
from curiosity.bot import Curiosity
from curious.commands import command, group
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
        em.add_field(name="Heartbeats", value=ctx.bot._gateways[ctx.event_context.shard_id].heartbeats)

        em.set_footer(text="Curio is the future!")
        em.timestamp = datetime.datetime.now()

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
