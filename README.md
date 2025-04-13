**Telegram media saver Bot**

It is a telegram bot for downloading different kinds of content, music, photos, videos from tiktok, youtube, YT music, spotify, instagram, pornhub, twitter, pinterest

### Requirements
Python 3.8 or higher

PostgreSQL

### Installation and Setup

1. Install PostgreSQL
   
Install PostgreSQL on your machine. You can download it from the official PostgreSQL website.

2. Create a Database

Once PostgreSQL is installed, create a database named cobainsaver. You can do this using the following commands in the PostgreSQL shell:
`CREATE DATABASE cobainsaver;`

3. Clone the Repository

Clone this repository to your local machine:

`git clone https://github.com/nazar067/CobainSaver-python.git`

`cd CobainSaver-python`

4. Install Python Dependencies

Create and activate a virtual environment:

`python3 -m venv venv`

`source venv/bin/activate  # For Linux/MacOS`

`venv\Scripts\activate     # For Windows`

Install the required Python packages:

`pip install -r requirements.txt`

5. Configure the Project

Rename the config.example.py file to config.py:

`cp config.example.py config.py`

Open the config.py file and fill in your credentials:

Telegram Bot Token: You can obtain this token from BotFather.

Database Connection String: Configure the DATABASE_URL for your PostgreSQL database.

Admin id: You can get it by @getmyid_bot

SPOTIFY_PUBLIC: You can get it on https://developer.spotify.com/

SPOTIFY_PRIVATE: You can get it on https://developer.spotify.com/

LEAKS_ID: Your chat_id or you can disable it in utils\select_service.py:22

YT_USERNAME: Your email for youtube

YT_PASSWORD: Your password for email

Example:

`API_TOKEN = "your_telegram_bot_token"`

`DATABASE_URL = "postgresql://username:password@localhost:5432/cobainsaver"`

`ADMIN_ID = "753848394"`

`SPOTIFY_PUBLIC = "uuae9hmb2d664afcgrf4fe95c4ii8f"`

`SPOTIFY_PRIVATE = "52as3bc3bgh55462bdrrtldf6d9125a9"`

`LEAKS_ID = "-1002789527167"`

`YT_USERNAME = "testemail@gmail.com"`

`YT_PASSWORD = "qwerty123"`

6. Start the Bot

Run the bot using the following command:

`python bot.py`

### Contributing
If you have suggestions or find any issues, feel free to open an issue or submit a pull request. Contributions are welcome!

### License
This project is licensed under the MIT License.
