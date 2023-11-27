import logging
import asyncio
import sys
from os import environ

import psycopg2.pool
from psycopg2 import sql
import pyowm.commons.exceptions
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyowm import OWM
from pyowm.utils.config import get_default_config
from opencage.geocoder import OpenCageGeocode
from opencage.geocoder import InvalidInputError, RateLimitExceededError, UnknownError

import expressions as ex

bot = Bot(environ["BOT_TOKEN"])
dispatcher = Dispatcher(bot)
geocoder = OpenCageGeocode(environ["OPEN_CAGE_API_KEY"])

logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler)

connection_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=100,
    dbname=environ["DB_NAME"],
    user="postgres",
    password=environ["DB_PASSWORD"],
)


def get_keyboard(text):
    """
    Creates a reply markup keyboard with a share location button and returns it.
    :return: keyboard object
    The function creates a ReplyKeyboardMarkup and a button, and adds the button to it.
    """

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton(text=text, request_location=True)
    keyboard.add(button)
    return keyboard


def insert_user_data(connection, connection_cursor, first_name, last_name, current_language, telegram_id):
    """
    Insert the user data into the database.
    :param connection: database connection,
    :param connection_cursor: database connection cursor,
    :param first_name: first name of the user,
    :param last_name: last name of the user,
    :param current_language: the language the user has chosen,
    :param telegram_id: user telegram id,
    :return: None
    The function inserts only unique user data into a postgresql database.
    """
    try:
        connection_cursor.execute("SELECT id FROM users WHERE tg_id = %s", (telegram_id,))
        existing_user_id = connection_cursor.fetchone()

        if not existing_user_id:
            connection_cursor.execute(
                "INSERT INTO users (fname, lname, language, tg_id) VALUES (%s, %s, %s, %s)",
                (first_name, last_name, current_language, telegram_id,)
            )
            connection_cursor.close()
            connection.commit()
            connection_pool.putconn(connection)

            logging.info(f"User data inserted successfully for {telegram_id}")

    except Exception as exc:
        logging.error(f"Error handling start command: {exc}")


@dispatcher.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    """
    Create inline language keyboard buttons in the bot and send a message
    :param message: the user message
    :return: None
    The function creates inline keyboard buttons for choosing a
    language, inserts the user data and sends a start message.
    """

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
        logging.info(f"Start command processed for user {message.from_user.id}")

    except Exception as e:
        logging.error(f"Error handling start command: {e}")

    finally:
        cursor.close()
        conn.commit()
        connection_pool.putconn(conn)


@dispatcher.message_handler(commands=["help"])
async def help_the_user(message: types.Message):
    """
    Send help message.
    :param message: the user message
    :return: None
    The function sends a help message after the user enters the respective command.
    """

    try:
        await bot.send_message(message.from_user.id, ex.help_message)
        logging.info(f"Help command processed for user {message.from_user.id}")

    except Exception as exc:
        logging.error(f"Error handling help command: {exc}")


@dispatcher.callback_query_handler(lambda c: c.data in ["enId", "ruId"])
async def to_query_language(call: types.callback_query):
    """
    Process the inline keyboard buttons query and update the DB table.
    :param call: callback call
    :return: None
    The function gets the language the user has selected and writes that information
    in the DB table under the name of the user. It also sends a welcome message.
    """

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

        if chosen_language == "ru":
            await bot.send_message(user_id, text=ex.welcome_message_russian,
                                   reply_markup=get_keyboard(ex.shareButtonTextRussian))
        else:
            await bot.send_message(user_id, text=ex.welcome_message_english,
                                   reply_markup=get_keyboard(ex.shareButtonTextEnglish))

    except Exception as exc:
        logging.error(f"Error processing callback query: {exc}")

    finally:
        await bot.answer_callback_query(call.id)


@dispatcher.message_handler(content_types=["location", "text"])
async def get_weather_and_send_messages(message: types.Message):
    """
    Get the weather information, send some appropriate messages.
    :param message: the message the user sends
    :return: None
    The function gets the chosen language of the current user from the database
    table and gets the weather information using an API and sends it to the user.
    It also sends some messages depending on the weather. If the name of a location
    entered/sent by the user does not exist, the function will check a similar name
    of a location and send it with the name of the country it is in, getting
    that information from the database. If it does not found anything, it
    will inform the user about it.
    """

    conn = connection_pool.getconn()
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM users WHERE tg_id = %s", (message.from_user.id,))
    user_language = cursor.fetchone()

    if user_language:
        user_language = user_language[0]
    else:
        user_language = "en"

    loading_message = None

    try:
        if user_language == "ru":
            current_weather_info = ex.weather_info_russian
            current_temperature_expressions = ex.temperature_expressions_russian
            current_cloud_expressions = ex.cloud_expressions_russian
            current_wind_expressions = ex.wind_expressions_russian
            current_mixed_expressions = ex.mixed_expressions_russian
            current_loading_text = ex.loadingTextRussian
        else:
            current_weather_info = ex.weather_info_english
            current_temperature_expressions = ex.temperature_expressions_english
            current_cloud_expressions = ex.cloud_expressions_english
            current_wind_expressions = ex.wind_expressions_english
            current_mixed_expressions = ex.mixed_expressions_english
            current_loading_text = ex.loadingTextEnglish

        loading_message = await bot.send_message(message.from_user.id, text=current_loading_text)
        await asyncio.sleep(1)

        location = ""
        if message.content_type == types.ContentType.LOCATION:
            loc = message.location
            latitude, longitude = loc.latitude, loc.longitude

            try:
                result = geocoder.reverse_geocode(latitude, longitude)

                if result and "components" in result[0] and "city" in result[0]["components"]:
                    location = result[0]["components"]["city"]
                elif result and "components" in result[0] and "country" in result[0]["components"]:
                    location = result[0]["components"]["country"]
                else:
                    await bot.send_message(message.from_user.id, ex.error_message_english)

            except (InvalidInputError, RateLimitExceededError, UnknownError):
                await bot.send_message(message.from_user.id, text=ex.error_message_english)

        else:
            location = message.text

        config_dict = get_default_config()
        config_dict["language"] = user_language
        owm = OWM(environ["OWM_API"], config=config_dict)
        mgr = owm.weather_manager()
        observation = mgr.weather_at_place(location)
        weather = observation.weather

        if loading_message:
            await bot.delete_message(message.from_user.id, loading_message.message_id)

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
                                                           wind_speed, mph, humidity), )

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
        logging.info(f"Weather information sent successfully to user {message.from_user.id}")

    except pyowm.commons.exceptions.NotFoundError:
        if user_language == "ru":
            current_not_found = ex.not_found_expression_russian
            current_error_message = ex.error_message_russian
        else:
            current_not_found = ex.not_found_expression_english
            current_error_message = ex.error_message_english

        cursor.execute(sql.SQL("SELECT city, country FROM cities WHERE city ILIKE %s"), [f"%{message.text}%"])
        rows = cursor.fetchall()

        if loading_message:
            await bot.delete_message(message.from_user.id, loading_message.message_id)

        if rows:
            options = [f"{row[0]}, {row[1]}" for row in rows]
            options_str = "\n".join(options)
            await bot.send_message(message.from_user.id, current_not_found.format(options_str))
        else:
            await bot.send_message(message.from_user.id, current_error_message)

    except Exception as exc:
        logging.error(f"Error processing message: {exc}")

    finally:
        cursor.close()
        conn.commit()
        connection_pool.putconn(conn)


executor.start_polling(dispatcher)
