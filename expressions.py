"""Some expressions the bot sends to the user depending on the weather."""

start_message = "Hi, {}, hope you are doing well!\nPlease choose a language."

help_message = ("To change the language, enter /start, choose a language, and enter the name of a "
                "location, or send your location (ensure your location on your phone is turned on). If the bot "
                "does not respond, please wait; there may be short-term connection delays.\n\nЧтобы изменить язык, "
                "введите /start, выберите язык и введите название местоположения или отправьте свое "
                "местоположение (убедитесь, что ваше местоположение на вашем телефоне включено). Если бот "
                "не отвечает, пожалуйста, подождите; возможны кратковременные задержки подключения.")

welcome_message_english = "My name is WeatherAnywhere.\nWrite the name of any location in the World.📍"

welcome_message_russian = "Меня зовут WeatherAnywhere.\nНапишите название любой локации на Планете.📍 "

weather_info_english = "🌡 Temperature in {}: {}({}).\n🌦 Weather status: {}." \
                       "\n☁ Cloudiness: {}.\n🌬 Wind speed: {} KM/H({} MPH).\n💧 Humidity: {}. "

weather_info_russian = "🌡 Температура в {}: {}({}).\n🌦 Статус погоды: {}.\n☁ Процент облачности: {}.\n🌬 Скорость " \
                       "ветра: {} км/ч({} миль/ч).\n💧 Влажность: {}. "

error_message_english = "Unable to find the resource.❌\nPlease try again."

error_message_russian = "Не удалось найти ресурс❌.\nПожалуйста, попробуйте еще раз."

temperature_expressions_english = ["I'd stay at home today.", "It's cold, find something warm to wear.🧣",
                                   "Summer clothes are prohibited!🧤", "It's a warm day today.🌞",
                                   "Please dress in summer attire.👕",
                                   "Is this because of global warming?"]

temperature_expressions_russian = ["Я бы сегодня остался дома.", "Холодно, надо надеть что-то теплое.🧣",
                                   "Летняя одежда запрещена!🧤", "Сегодня теплый день.🌞",
                                   "Ну и жара, можно надеть летнюю одежду.👕",
                                   "Это что, из-за глобального потепления?!"]

cloud_expressions_english = ["There is a high risk of getting a sunstroke!🌡",
                             "It might rain today.☔", "Who does not like when it snows?🌨",
                             "There is a chance that it will rain.🌂", "Good news, it might snow today!❄"]

cloud_expressions_russian = ["Повышен риск получения солнечного удара.🌡",
                             "Возможно, сегодня пойдет дождь.☔", "Да кто же не любит снег?🌨",
                             "Есть шанс, что пойдет дождь.🌂", "Кажется сегодня будет снег!❄"]

wind_expressions_english = ["There is a strong wind outside.🌪", "Not a good day for having a walk.",
                            "It's a great time for having a winter walk!"]

wind_expressions_russian = ["Слишком сильный ветер.🌪", "Не очень хороший день для прогулки.",
                            "Отличный день для зимней прогулки!"]

mixed_expressions_english = ["Time for merrymaking.🕶", "It seems that it's the day to hang out with friends!🌟"]

mixed_expressions_russian = ["Время для веселья.🕶", "Кажется пора замутить вечеринку с друзьями!🌟"]

not_found_expression_english = "Perhaps you mean one of the following:\n{}."

not_found_expression_russian = "Возможно вы имели в виду что-то из этого:\n{}."

shareButtonTextEnglish = "Share Location 📍"

shareButtonTextRussian = "Поделиться локацией 📍"
