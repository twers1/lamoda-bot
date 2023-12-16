import os
from dotenv import load_dotenv

# Библиотека для загрузки данных из файла ENV
load_dotenv()

# Подключение переменных из файла ENV
TOKEN = os.getenv("TOKEN")
password = os.getenv('PASSWORD')
