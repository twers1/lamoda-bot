import asyncio
from datetime import datetime

import requests
from aiogram import executor

from src.loader import dp, bot
from src.lamoda_api import get_auth_token, get_calendar

last_check_time = None  # Добавляем переменную для хранения времени последней проверки
last_has_slots = False  # Флаг, указывающий наличие слотов в предыдущей проверке


async def process_available_slots(slots):
    messages = []
    for slot in slots:
        availability = slot.get('availability')
        free_capacity_count_str = slot.get('freeCapacityCount', '0')

        # Convert freeCapacityCount to an integer (default to 0 if not convertible)
        free_capacity_count = int(free_capacity_count_str) if free_capacity_count_str.isdigit() else 0

        if availability and (free_capacity_count > 340 or (free_capacity_count_str.isdigit() and int(
                free_capacity_count_str) > 200) or "более" in free_capacity_count_str.lower()):
            start_time = datetime.fromisoformat(slot.get("startAt"))
            end_time = datetime.fromisoformat(slot.get("endAt"))

            if "более" in free_capacity_count_str.lower():
                message = f'✅ Доступен слот к отгрузке!\n\nИнформация о слоте:\n' \
                          f'Начало: {start_time.strftime("%d.%m.%Y %H:%M:%S")}\n' \
                          f'Окончание: {end_time.strftime("%d.%m.%Y %H:%M:%S")}\n' \
                          f'Доступно более 2000 вещей к поставке\n'
            else:
                message = f'✅ Доступен слот к отгрузке!\n\nИнформация о слоте:\n' \
                          f'Начало: {start_time.strftime("%d.%m.%Y %H:%M:%S")}\n' \
                          f'Окончание: {end_time.strftime("%d.%m.%Y %H:%M:%S")}\n' \
                          f'Доступно вещей к поставке: {free_capacity_count}\n'

            messages.append(message)
    return messages


async def send_long_message(chat_id, text):
    try:
        max_length = 4096  # Максимальная длина сообщения для отправки в Telegram
        print('ауууууууууу')
        while text:
            chunk, text = text[:max_length], text[max_length:]
            print(f"Chunk length: {len(chunk)}")
            await bot.send_message(chat_id, chunk)
    except Exception as e:
        print(f"Error sending long message: {e}")


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

            # Ищем слоты с параметром availability равным True
            available_slots = [slot for slot in calendar_data.get('data', {}).get('slots', []) if
                               slot.get('availability')]
            print(available_slots)

            if available_slots:
                # выводим информацию о слотах
                messages = await process_available_slots(available_slots)
                last_check_time_message = f'Последняя проверка была: {current_datetime - last_check_time}' if last_check_time is not None else ''

                # Собираем все сообщения в одну строку
                combined_message = '\n'.join(messages)

                # Проверяем, если сообщение слишком длинное
                if combined_message:
                    if len(combined_message) > 4096:
                        await send_long_message(-1002131738291, combined_message)
                    else:
                        await bot.send_message(-1002131738291, f'{combined_message}{last_check_time_message}')

                last_has_slots = True
                last_check_time = current_datetime  # Обновляем время последней проверки

            elif last_has_slots:
                await bot.send_message(-1002131738291, 'Нет доступных слотов')
                last_has_slots = False

        elif calendar_response.status_code == 401:
            # В случае истечения срока действия токена, можно обновить только токен, оставив сессионную куку неизменной
            new_token, _ = get_auth_token()
            headers['X-Auth-Token'] = new_token  # Обновляем токен в заголовках
            calendar_response = get_calendar(headers)
            calendar_data = calendar_response.json()

            # Ищем слоты с параметром availability равным True
            available_slots = [slot for slot in calendar_data.get('data', {}).get('slots', []) if
                               slot.get('availability')]

            if available_slots:
                messages = await process_available_slots(available_slots)
                last_check_time_message = f'Последняя проверка была: {current_datetime - last_check_time}' if last_check_time is not None else ''

                # Собираем все сообщения в одну строку
                combined_message = '\n'.join(messages)

                # Проверяем, если сообщение слишком длинное
                if combined_message:
                    if len(combined_message) > 30:
                        await send_long_message(-1002131738291, combined_message)
                    else:
                        await bot.send_message(-1002131738291, f'{combined_message}{last_check_time_message}')

                last_has_slots = True
                last_check_time = current_datetime  # Обновляем время последней проверки

            elif last_has_slots:
                await bot.send_message(-1002131738291, 'Нет доступных слотов')
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
