import os #Модуль для работы с операционной сис-мой
import logging #Модуль для ведения журнала логов

import pymysql.cursors
import requests
import asyncio
from config import telegram_token #Импорт конфига
import dialogflow_v2 as dialogflow #Модуль DialogFlowыы
from aiogram import Bot, Dispatcher, executor, types #Модули аиограм
from aiogram.contrib.fsm_storage.memory import MemoryStorage

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'telegram-bot-lxwr-de14b0eaae26.json'


session_client = dialogflow.SessionsClient() #Сессия клиента
project_id = 'telegram-bot-lxwr' #Айди проекта берём с json файла
session_id = 'sessions' #Указываем любое значение, в моём случае "sessions"
language_code = 'ru' #Язык русский
session = session_client.session_path(project_id, session_id) #Объявляем сессию по айди проекта и айди сессии

logging.basicConfig(level=logging.INFO) #Логгирование на уровне INFO


loop = asyncio.get_event_loop()
bot = Bot(token=telegram_token, parse_mode="HTML") #Создание экземпляра класса бо

dp = Dispatcher(bot, loop=loop, storage=MemoryStorage()) #Создание экземпляра класса диспатчера

#con = pymysql.connect(host='bitproject.beget.tech', user='bitproject_reglm', password='BK3QSWfc', db='bitproject_reglm', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)

con = pymysql.connect(host='localhost', user='root', password='admin', db='bot1cbit', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)


if __name__ == "__main__":
    from handlers import dp, send_to_admin
    executor.start_polling(dp, on_startup=send_to_admin)


    # scheduler.start()
    #executor.start_polling(dp, skip_updates=True)


'''
#-------------------------------------------------------------
import apiai, json


def send_message(message):

    request = apiai.ApiAI("de14b0eaae26c26db6a9d8e79a08d4068bf750cc").text_request()
    request.lang = 'ru'
    request.session_id = 'session_1'
    request.query = message
    response = json.loads(request.getresponse().read().decode('utf-8'))
    print(response)


print('Введите ваше сообщение: ')
message = input()
while message != 'выход':
    send_message(message)
    message = input()
'''