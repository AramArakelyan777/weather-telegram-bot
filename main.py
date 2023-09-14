from os import environ

import psycopg2.pool
from psycopg2 import sql
import pyowm.commons.exceptions
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyowm import OWM
from pyowm.utils.config import get_default_config

import expressions as ex

bot = Bot(environ["BOT_TOKEN"])
dispatcher = Dispatcher(bot)

connection_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=50,
    dbname=environ["DB_NAME"],
    user="postgres",
    password=environ["PASSWORD"]
)


def insert_user_data(connection, connection_cursor, first_name, last_name, current_language, telegram_id):
    connection_cursor.execute("SELECT id FROM users WHERE tg_id = %s", (telegram_id,))
    existing_user_id = connection_cursor.fetchone()
    if not existing_user_id:
        connection_cursor.execute(
            "INSERT INTO users (fname, lname, language, tg_id) VALUES (%s, %s, %s, %s)",
            (first_name, last_name, current_language, telegram_id)
        )
        connection.commit()


@dispatcher.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    conn = connection_pool.getconn()
    cursor = conn.cursor()
    try:
        markup = InlineKeyboardMarkup()
        english_button = InlineKeyboardButton(text="🇬🇧 English", callback_data="enId")
        russian_button = InlineKeyboardButton(text="🇷🇺 Русский", callback_data="ruId")
        markup.add(english_button)
        markup.add(russian_button)

        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        telegram_id = message.from_user.id

        insert_user_data(connection=conn, connection_cursor=cursor, first_name=first_name, last_name=last_name,
                         current_language="", telegram_id=telegram_id)

        await bot.send_message(telegram_id, ex.start_message.format(first_name, first_name), reply_markup=markup)
    finally:
        cursor.close()
        conn.commit()
        connection_pool.putconn(conn)


@dispatcher.message_handler(commands=["help"])
async def help_the_user(message: types.Message):
    await bot.send_message(message.from_user.id, ex.help_message)


@dispatcher.callback_query_handler(lambda c: c.data in ["enId", "ruId"])
async def to_query_language(call: types.callback_query):
    user_id = call.message.chat.id
    chosen_language = "en" if call.data == "enId" else "ru"

    try:
        connection = connection_pool.getconn()
        cursor = connection.cursor()
        update_query = "UPDATE users SET language = %s WHERE tg_id = %s"
        cursor.execute(update_query, (chosen_language, user_id))

        connection.commit()
        cursor.close()
        connection_pool.putconn(connection)

        if chosen_language == "en":
            await bot.send_message(user_id, text=ex.welcome_message_english)
        else:
            await bot.send_message(user_id, text=ex.welcome_message_russian)
    finally:
        await bot.answer_callback_query(call.id)


@dispatcher.message_handler()
async def get_weather_and_send_messages(message):
    conn = connection_pool.getconn()
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM users WHERE tg_id = %s", (message.from_user.id,))
    user_language = cursor.fetchone()
    if user_language:
        user_language = user_language[0]
    else:
        user_language = "en"
    try:
        current_weather_info = ex.weather_info_english
        current_temperature_expressions = ex.temperature_expressions_english
        current_cloud_expressions = ex.cloud_expressions_english
        current_wind_expressions = ex.wind_expressions_english
        current_mixed_expressions = ex.mixed_expressions_english
        if user_language == "ru":
            current_weather_info = ex.weather_info_russian
            current_temperature_expressions = ex.temperature_expressions_russian
            current_cloud_expressions = ex.cloud_expressions_russian
            current_wind_expressions = ex.wind_expressions_russian
            current_mixed_expressions = ex.mixed_expressions_russian

        location = message.text
        config_dict = get_default_config()
        config_dict["language"] = user_language
        owm = OWM(environ["OWM_API"], config=config_dict)
        mgr = owm.weather_manager()
        observation = mgr.weather_at_place(location)
        weather = observation.weather

        temperature = str(round(weather.temperature("celsius")["temp"])) + "°C"
        wind_speed = str(weather.wind()["speed"])
        status = weather.detailed_status
        cloudiness = str(weather.clouds) + "%"
        humidity = str(weather.humidity) + "%"
        mph = str(round(weather.wind()["speed"] * 2.237))
        fahrenheit = str(round((weather.temperature("celsius")["temp"] * 9 / 5) + 32)) + "°F"

        temp = weather.temperature("celsius")["temp"]
        wind = weather.wind()["speed"]
        cloud = weather.clouds

        await bot.send_message(message.from_user.id,
                               current_weather_info.format(location, temperature, fahrenheit, status, cloudiness,
                                                           wind_speed, mph, humidity))
        if temp <= -10:
            await bot.send_message(message.from_user.id, current_temperature_expressions[0])
        elif -10 < temp <= 0:
            await bot.send_message(message.from_user.id, current_temperature_expressions[1])
        elif 0 < temp <= 14:
            await bot.send_message(message.from_user.id, current_temperature_expressions[2])
        elif 14 < temp <= 30:
            await bot.send_message(message.from_user.id, current_temperature_expressions[3])
        elif 30 < temp <= 39:
            await bot.send_message(message.from_user.id, current_temperature_expressions[4])
        else:
            await bot.send_message(message.from_user.id, current_temperature_expressions[5])
            if cloud < 50:
                await bot.send_message(message.from_user.id, current_cloud_expressions[0])
        if cloud >= 70:
            if temp >= 0:
                await bot.send_message(message.from_user.id, current_cloud_expressions[1])
            else:
                await bot.send_message(message.from_user.id, current_cloud_expressions[2])
        if 55 <= cloud < 70:
            if temp >= 0:
                await bot.send_message(message.from_user.id, current_cloud_expressions[3])
            else:
                await bot.send_message(message.from_user.id, current_cloud_expressions[4])
        if wind >= 8:
            await bot.send_message(message.from_user.id, current_wind_expressions[0])
            if temp < -5:
                await bot.send_message(message.from_user.id, current_wind_expressions[1])
        else:
            if -10 < temp <= 0:
                await bot.send_message(message.from_user.id, current_wind_expressions[2])
        if 14 < temp <= 36 and wind < 8 and cloud < 55:
            await bot.send_message(message.from_user.id, current_mixed_expressions[0])
        if 14 < temp < 39 and wind < 8 and cloud < 55:
            await bot.send_message(message.from_user.id, current_mixed_expressions[1])
    except pyowm.commons.exceptions.NotFoundError:
        if user_language == "ru":
            current_not_found = ex.not_found_expression_russian
        else:
            current_not_found = ex.not_found_expression_english
        cursor.execute(sql.SQL("SELECT city, country FROM cities WHERE city ILIKE %s"), [f"%{message.text}%"])
        rows = cursor.fetchall()
        if rows:
            options = [f"{row[0]}, {row[1]}" for row in rows]
            options_str = "\n".join(options)
            await bot.send_message(message.from_user.id, current_not_found.format(options_str))
        else:
            if user_language == "ru":
                await bot.send_message(message.from_user.id, ex.error_message_russian)
            else:
                await bot.send_message(message.from_user.id, ex.error_message_english)
    finally:
        cursor.close()
        conn.commit()
        connection_pool.putconn(conn)


executor.start_polling(dispatcher)
