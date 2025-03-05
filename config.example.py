#In the root directory, create an config.py file and copy the contents of the config.example.py file there.
import os
API_TOKEN = "Your telegram bot token"
DATABASE_URL = os.getenv("DATABASE_URL", "connection string to postgress")
SPOTIFY_PUBLIC = "You can get it on https://developer.spotify.com/"
SPOTIFY_PRIVATE = "You can get it on https://developer.spotify.com/"
TIKTOK_API = "https://www.tikwm.com/api/"
TWITTER_API = "https://api.vxtwitter.com/Twitter/status/"
LEAKS_ID = "Your private group's id"
THREAD_GROUP_ID = "Your private group's id"
ADMIN_ID = "Your telegram id(you can get it by @getmyid_bot)"
YT_USERNAME = "email"
YT_PASSWORD = "password"