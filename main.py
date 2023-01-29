from difflib import get_close_matches
from os import environ

import pymysql.cursors
import pyowm.commons.exceptions
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, User
from pyowm import OWM
from pyowm.utils.config import get_default_config

import expressions as ex

bot = Bot(environ["BOT_TOKEN"])
dp = Dispatcher(bot)
currentLanguage = ""


@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    markup = InlineKeyboardMarkup()
    en = InlineKeyboardButton(text="🇬🇧 English", callback_data="enId")
    ru = InlineKeyboardButton(text="🇷🇺 Русский", callback_data="ruId")
    markup.add(en)
    markup.add(ru)
    await bot.send_message(message.from_user.id, ex.startMessage.format(message.from_user.first_name,
                                                                        message.from_user.first_name),
                           reply_markup=markup)


@dp.message_handler(commands=["help"])
async def help_the_user(message: types.Message):
    await bot.send_message(message.from_user.id, ex.helpMessage)


@dp.callback_query_handler(lambda c: c.data == "enId")
async def to_query(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id, text=ex.welcomeMessageEn.format(bot.get(User.full_name)))
    global currentLanguage
    currentLanguage = "en"


@dp.callback_query_handler(lambda c: c.data == "ruId")
async def to_query2(call: types.callback_query):
    await bot.answer_callback_query(call.id)
    await bot.send_message(call.message.chat.id, text=ex.welcomeMessageRu.format(bot.get(User.full_name)))
    global currentLanguage
    currentLanguage = "ru"


countryListEn = []
cityListEn = []

connection = pymysql.connect(host='localhost', user='root', port=3306, database='countriesDB',
                             cursorclass=pymysql.cursors.DictCursor)


@dp.message_handler()
async def get_weather(message):
    try:
        currentWeatherInfo = ex.weatherInfoEn
        currentTemperatureExpressions = ex.temperatureExpressionsEn
        currentCloudExpressions = ex.cloudExpressionsEn
        currentWindExpressions = ex.windExpressionsEn
        currentMixedExpressions = ex.mixedExpressionsEn
        if currentLanguage == "ru":
            currentWeatherInfo = ex.weatherInfoRu
            currentTemperatureExpressions = ex.temperatureExpressionsRu
            currentCloudExpressions = ex.cloudExpressionsRu
            currentWindExpressions = ex.windExpressionsRu
            currentMixedExpressions = ex.mixedExpressionsRu

        location = message.text
        config_dict = get_default_config()
        config_dict['language'] = currentLanguage
        owm = OWM(environ["OWM_API"], config=config_dict)
        mgr = owm.weather_manager()
        observation = mgr.weather_at_place(location)
        w = observation.weather

        temperature = str(round(w.temperature("celsius")["temp"])) + "°C"
        windSpeed = str(w.wind()["speed"])
        status = w.detailed_status
        cloudiness = str(w.clouds) + "%"
        humidity = str(w.humidity) + "%"
        mph = str(round(w.wind()["speed"] * 2.237))
        fahrenheit = str(round((w.temperature("celsius")["temp"] * 9 / 5) + 32)) + "°F"
        t = w.temperature("celsius")["temp"]
        wind = w.wind()["speed"]
        cloud = w.clouds

        await bot.send_message(message.from_user.id, currentWeatherInfo.format(location, temperature, fahrenheit,
                                                                               status, cloudiness, windSpeed, mph,
                                                                               humidity))
        if t <= -10:
            await bot.send_message(message.from_user.id, currentTemperatureExpressions[0])
        elif -10 < t <= 0:
            await bot.send_message(message.from_user.id, currentTemperatureExpressions[1])
        elif 0 < t <= 14:
            await bot.send_message(message.from_user.id, currentTemperatureExpressions[2])
        elif 14 < t <= 30:
            await bot.send_message(message.from_user.id, currentTemperatureExpressions[3])
        elif 30 < t <= 39:
            await bot.send_message(message.from_user.id, currentTemperatureExpressions[4])
        else:
            await bot.send_message(message.from_user.id, currentTemperatureExpressions[5])
            if cloud < 50:
                await bot.send_message(message.from_user.id, currentCloudExpressions[0])
        if cloud >= 70:
            if t >= 0:
                await bot.send_message(message.from_user.id, currentCloudExpressions[1])
            else:
                await bot.send_message(message.from_user.id, currentCloudExpressions[2])
        if 55 <= cloud < 70:
            if t >= 0:
                await bot.send_message(message.from_user.id, currentCloudExpressions[3])
            else:
                await bot.send_message(message.from_user.id, currentCloudExpressions[4])
        if wind >= 8:
            await bot.send_message(message.from_user.id, currentWindExpressions[0])
            if t < -5:
                await bot.send_message(message.from_user.id, currentWindExpressions[1])
        else:
            if -10 < t <= 0:
                await bot.send_message(message.from_user.id, currentWindExpressions[2])
        if 14 < t <= 36 and wind < 8 and cloud < 55:
            await bot.send_message(message.from_user.id, currentMixedExpressions[0])
        if 14 < t < 39 and wind < 8 and cloud < 55:
            await bot.send_message(message.from_user.id, currentMixedExpressions[1])
    except pyowm.commons.exceptions.NotFoundError:
        try:
            with connection.cursor() as cursor:
                select = "SELECT * FROM countryTable"
                cursor.execute(select)
                rows = cursor.fetchall()
                for row in rows:
                    countryListEn.append(row['countryEn'])
                    cityListEn.append(row['cityEn'])

                if currentLanguage == "ru":
                    currentNotFound = ex.notfoundExpressionRu
                else:
                    currentNotFound = ex.notfoundExpressionEn

                matches = get_close_matches(message.text, cityListEn, n=1, cutoff=0.7)
                matches_str = "".join(map(str, matches))
                await bot.send_message(message.from_user.id, currentNotFound.format(matches_str, countryListEn[
                    cityListEn.index(matches_str)]))
        except ValueError:
            if currentLanguage == "ru":
                await bot.send_message(message.from_user.id, ex.errorMessageRu)
            else:
                await bot.send_message(message.from_user.id, ex.errorMessageEn)


executor.start_polling(dp)
connection.close()
