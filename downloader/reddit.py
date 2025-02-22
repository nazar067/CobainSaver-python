import logging
import os
from RedDownloader import RedDownloader
from user.get_user_path import get_user_path
from utils.get_name import get_random_file_name

async def fetch_reddit_post(url: str, chat_id: int) -> dict:

    file = RedDownloader.Download(url = url , output="test" , quality = 720)
    print(file.destination)
    print(file.directory)
    print(file.mediaType)