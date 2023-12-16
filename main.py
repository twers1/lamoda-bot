import asyncio
from datetime import datetime

import requests
from aiogram import executor

from src.loader import dp, bot
from src.lamoda_api import get_auth_token, get_calendar

last_check_time = None  # Добавляем переменную для хранения времени последней проверки
last_has_slots = False  # Флаг, указывающий наличие слотов в предыдущей проверке


async def process_unavailable_slots(slots):
    messages = []
    for slot in slots:
        if slot.get('availability'):
            start_time = datetime.fromisoformat(slot.get("startAt"))
            end_time = datetime.fromisoformat(slot.get("endAt"))
            message = f'✅ Доступен слот к отгрузке!\n\nИнформация о слоте:\n' \
                      f'Начало: {start_time.strftime("%d.%m.%Y %H:%M:%S")}\n' \
                      f'Окончание: {end_time.strftime("%d.%m.%Y %H:%M:%S")}\n' \
                      f'Доступно вещей к поставке: {slot.get("freeCapacityCount")}\n'
            messages.append(message)
    return messages


async def send_long_message(chat_id, text):
    max_length = 4096  # Максимальная длина сообщения для отправки в Telegram

    while text:
        chunk, text = text[:max_length], text[max_length:]
        await bot.send_message(chat_id, chunk)


async def check_calendar():
    global last_check_time, last_has_slots
    try:
        # Получаем текущую дату и время
        current_datetime = datetime.now()

        # Получаем токен и сессионную куку PHPSESSID
        token, php_session_cookie = get_auth_token()

        # Создаем заголовки с токеном и сессионной кукой
        headers = {
            'X-Auth-Token': token,
            'Cookie': f'PHPSESSID={php_session_cookie}'
        }

        # Получаем календарный ответ с использованием заголовков
        calendar_response = get_calendar(headers)

        # Проверяем статус ответа
        if calendar_response.status_code == 200:
            calendar_data = calendar_response.json()

            # Ищем слоты с параметром availability равным False
            unavailable_slots = [slot for slot in calendar_data.get('data', {}).get('slots', []) if
                                 not slot.get('availability')]

            if unavailable_slots:
                # выводим информацию о слотах
                messages = await process_unavailable_slots(unavailable_slots)
                last_check_time_message = f'Последняя проверка была: {current_datetime - last_check_time}' if last_check_time is not None else ''

                # Собираем все сообщения в одну строку
                combined_message = '\n'.join(messages)

                # Проверяем, если сообщение слишком длинное
                if combined_message:
                    if len(combined_message) > 4096:
                        await send_long_message(-4008242375, combined_message)
                    else:
                        await bot.send_message(-4008242375, f'{combined_message}{last_check_time_message}')

                last_has_slots = True
                last_check_time = current_datetime  # Обновляем время последней проверки

            elif last_has_slots:
                await bot.send_message(-4008242375, 'Нет доступных слотов')
                last_has_slots = False

        elif calendar_response.status_code == 401:
            # В случае истечения срока действия токена, можно обновить только токен, оставив сессионную куку неизменной
            new_token, _ = get_auth_token()
            headers['X-Auth-Token'] = new_token  # Обновляем токен в заголовках
            calendar_response = get_calendar(headers)
            calendar_data = calendar_response.json()

            # Ищем слоты с параметром availability равным False
            unavailable_slots = [slot for slot in calendar_data.get('data', {}).get('slots', []) if
                                 not slot.get('availability')]

            if unavailable_slots:
                # Если есть недоступные слоты, выводим информацию о слотах
                messages = await process_unavailable_slots(unavailable_slots)
                last_check_time_message = f'Последняя проверка была: {current_datetime - last_check_time}' if last_check_time is not None else ''

                # Собираем все сообщения в одну строку
                combined_message = '\n'.join(messages)

                # Проверяем, если сообщение слишком длинное
                if combined_message:
                    if len(combined_message) > 4096:
                        await send_long_message(-4008242375, combined_message)
                    else:
                        await bot.send_message(-4008242375, f'{combined_message}{last_check_time_message}')

                last_has_slots = True
                last_check_time = current_datetime  # Обновляем время последней проверки

            elif last_has_slots:
                await bot.send_message(-4008242375, 'Нет доступных слотов')
                last_has_slots = False

    except requests.exceptions.RequestException as e:
        print(f'Request failed: {e}')


async def scheduled():
    while True:
        await check_calendar()
        await asyncio.sleep(180)

if __name__ == '__main__':
    print("Bot started")

    # Запускаем планировщик задач
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled())

    executor.start_polling(dp, skip_updates=True)
    print("Bot stopped")
