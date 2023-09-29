# WeatherAnywhere Telegram Bot


## Table of Contents

- [Table of Contents](#table-of-contents)
- [Introduction](#introduction)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Usage](#usage)
- [Features](#features)
- [Contact](#contact)
- [License](#license)


## Introduction

WeatherAnywhere is a Telegram chatbot that provides users with current weather information and useful advice based on their location input. It also stores user data in a PostgreSQL database and offers hints for valid locations if users make mistakes while inputting locations.


## Getting Started

Follow these instructions to set up and run the WeatherAnywhere on your machine or server.

### Prerequisites

Before you begin, ensure you have the following:

1. Python 3 installed
2. Postgresql database installed and configured
3. A Telegram bot token (obtain one by talking to the BotFather)
4. OpenWeatherMap API configured

### Installation

1. Clone this repository to your local machine:

    ```bash
    https://github.com/AramArakelyan777/weather-telegram-bot
   
2. Change into the project directory:

    ```bash
    cd weather-telegram-bot
   
3. Create a virtual environment

    ```bash
    python -m venv venv
   
4. Install the project dependencies from the requirements.txt file:

    ```bash
    pip install -r requirements.txt

### Configuration

Create the necessary venv variables:

    TELEGRAM_BOT_TOKEN=your_telegram_bot_token
    DB_NAME=your-database-name
    PASSWORD=your-database-password
    OWM_API=your-openweathermap-api


## Usage

To start the Bot, run the following command and use the bot in telegram:

    python main.py


## Features

1. Weather Information: The bot provides current weather information based on user location input.
2. Advice: The bot offers useful advice and(or) some funny messages depending on the weather conditions.
3. Database Storage: User data is stored in a Postgresql database for future interactions.
4. Location Hints: If a user makes a mistake while inputting a location, the bot provides hints from the database.
5. Language: The bot is available in 2 languages: English and Russian.


## Contact

If you have questions or feedback, please reach out to me by email:

    aram777arakelyan@gmail.com

I appreciate your support!


## License

This project is licensed under the MIT License - see the LICENSE file for details.