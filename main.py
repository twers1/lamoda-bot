import requests
import json

# Загрузка данных из JSON-файла
with open('mamour.postman_collection.json', 'r') as file:
    data = json.load(file)

# Переменная для хранения исходного токена
original_auth_token = None

def make_request(request_data, token=None, params=None):
    url = request_data['request']['url']['raw']
    method = request_data['request']['method']
    headers = {}

    # Добавление заголовка с токеном для авторизованных запросов
    if token:
        headers['X-Auth-Token'] = token

    # Выполнение запроса
    if method == 'GET':
        response = requests.get(url, headers=headers, params=params)
    elif method == 'POST':
        headers['Content-Type'] = 'application/json'
        body = request_data['request']['body']['raw']
        response = requests.post(url, headers=headers, json=json.loads(body))

    return response

# Авторизация
auth_response = make_request(data['item'][0])

# Проверка успешной авторизации и получение токена
try:
    auth_response.raise_for_status()
    auth_data = auth_response.json()
    if 'token' in auth_data['data']:
        original_auth_token = auth_data['data']['token']
        print("Original Auth Token:", original_auth_token)

        # Запрос календаря с использованием токена авторизации
        calendar_params = {
            'month': '2023-12',
            'partnerId': '4823',
            'directionId': '1'
        }

        # Использование original_auth_token при каждом запросе календаря
        calendar_response = make_request(data['item'][1], token=original_auth_token, params=calendar_params)

        # Вывод полного URL запроса календаря
        print("Полный URL запроса календаря:", calendar_response.request.url)

        # Вывод ответа на запрос календаря
        print("Ответ на запрос календаря после обновления токена:", calendar_response.text)

        if calendar_response.status_code == 401 and 'refreshToken' in auth_data['data']:
            print("Received 401 response. Trying to refresh the token...")  # Отладочный вывод

            refreshed_auth_response = make_request(data['item'][0], token=auth_data['data']['refreshToken'])
            refreshed_auth_data = refreshed_auth_response.json()

            print("Refreshed Auth Response:", refreshed_auth_response.text)  # Отладочный вывод

            if 'token' in refreshed_auth_data['data']:
                original_auth_token = refreshed_auth_data['data']['token']
                print("New Auth Token:", original_auth_token)

                # Повторный запрос календаря с обновленным токеном и параметрами
                calendar_response = make_request(data['item'][1], token=original_auth_token, params=calendar_params)

                # Проверяем успешность запроса после обновления токена
                if calendar_response.status_code == 200:
                    print("Ответ на запрос календаря после обновления токена:", calendar_response.text)
                else:
                    print("Ошибка при запросе календаря после обновления токена. Код ответа:",
                          calendar_response.status_code)
                    print("Ответ на запрос календаря после обновления токена:", calendar_response.text)
            else:
                print("Токен не найден в ответе обновления токена.")
        else:
            print("Токен не обновлен. Код ответа:", calendar_response.status_code)
            print("Ответ на запрос календаря:", calendar_response.text)
    else:
        print("Токен не найден в ответе авторизации.")
except requests.exceptions.RequestException as e:
    print(f"Произошла ошибка: {e}")


# import asyncio
# import json
#
# import requests
# from aiogram import Bot, Dispatcher, types
# from aiogram import executor
#
# # Замените 'YOUR_BOT_TOKEN' на токен вашего бота
# TOKEN = '5855017352:AAG8c6XkSK93wvgJ2xiGbNM3uSZM-0Bs9iY'
#
# bot = Bot(token=TOKEN)
# dp = Dispatcher(bot)
#
# @dp.message_handler(commands=['start'])
# async def start(message: types.Message):
#     await message.answer("Привет! Я бот для проверки доступности.")
#
#
# @dp.message_handler()
# async def check_availability(message: types.Message):
#     url = 'https://backend.gm.lamoda.ru/api/v1/calendar?month=2023-12&partnerId=4823&directionId=1'
#     response = requests.get(url)
#
#     try:
#         data = response.json()
#         print(data)
#     except json.JSONDecodeError as e:
#         print(f"Error decoding JSON: {e}")
#         return
#
#     trace_id = data.get('traceId')
#     if trace_id:
#         print(f"Trace ID: {trace_id}")
#
#     items = data.get('items', [])
#     print(items)
#     for item in items:
#         print(item)
#         availability = item.get('availability', False)
#
#         if availability:
#             # Notify the user that the availability is True
#             await bot.send_message(chat_id=message.from_user.id, text="Ячейка доступна!")
#
#             # Optionally, you can provide additional information
#             await bot.send_message(chat_id=message.from_user.id, text=f"Доступность найдена: {item}")
#
#             # You might want to break out of the loop if you only want to notify about the first available item
#             break
#
#
# async def scheduler(dispatcher):
#     while True:
#         await asyncio.sleep(1)  # Проверка каждые 24 часа (измените по необходимости)
#         # Вызываем функцию check_availability, чтобы отправить уведомление
#         await check_availability(types.Message)
#
# if __name__ == '__main__':
#     loop = asyncio.get_event_loop()
#     loop.create_task(scheduler(dp))
#     executor.start_polling(dp, loop=loop)
